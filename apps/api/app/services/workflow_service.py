"""
Phase 2: Core Workflow Engine Service
Handles sequential workflow execution with robust error handling and state management.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.workflow import (
    WorkflowTemplate, WorkflowRun, WorkflowStepExecution, WorkflowArtifact,
    WorkflowStatus, StepStatus
)
from app.models import User
from app.core.agents.registry import AgentRegistry, agent_registry
from app.core.agents.base import AgentExecutionContext
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class WorkflowExecutionError(Exception):
    """Custom exception for workflow execution errors"""
    pass


class DAGValidator:
    """Validates and analyzes workflow DAG structures"""
    
    @staticmethod
    def validate_dag(definition: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate DAG structure for cycles and missing dependencies.
        Returns (is_valid, error_message)
        """
        if not definition or 'steps' not in definition:
            return False, "Missing 'steps' in workflow definition"
        
        steps = definition['steps']
        if not steps:
            return False, "Workflow must have at least one step"
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            if step_id in steps:
                deps = steps[step_id].get('depends_on', [])
                for dep in deps:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(step_id)
            return False
        
        # Check each step for cycles
        for step_id in steps:
            if step_id not in visited:
                if has_cycle(step_id):
                    return False, f"Cycle detected involving step '{step_id}'"
        
        # Validate all dependencies exist
        for step_id, step_def in steps.items():
            deps = step_def.get('depends_on', [])
            for dep in deps:
                if dep not in steps:
                    return False, f"Step '{step_id}' depends on non-existent step '{dep}'"
        
        return True, None
    
    @staticmethod
    def get_execution_order(definition: Dict[str, Any]) -> List[str]:
        """
        Get topologically sorted execution order for steps.
        Returns list of step IDs in execution order.
        """
        steps = definition.get('steps', {})
        if not steps:
            return []
        
        # Build adjacency list
        graph = {step_id: set(step.get('depends_on', [])) for step_id, step in steps.items()}
        
        # Kahn's algorithm for topological sort
        in_degree = {step_id: 0 for step_id in steps}
        for step_id in steps:
            for dep in graph[step_id]:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            step_id = queue.pop(0)
            result.append(step_id)
            
            # Remove edges from this node
            for next_step in steps:
                if step_id in graph[next_step]:
                    graph[next_step].remove(step_id)
                    in_degree[next_step] -= 1
                    if in_degree[next_step] == 0:
                        queue.append(next_step)
        
        return result


class WorkflowService:
    """
    Core workflow execution service for Phase 2.
    Handles sequential workflow execution with artifact management.
    """
    
    def __init__(self):
        # Use the global registry so discovery performed at startup/endpoints is respected
        self.agent_registry = agent_registry
        self.dag_validator = DAGValidator()
    
    async def create_template(
        self,
        db: AsyncSession,
        name: str,
        description: str,
        definition: Dict[str, Any],
        user: User,
        category: Optional[str] = None
    ) -> WorkflowTemplate:
        """Create a new workflow template with validation."""
        # Validate DAG structure
        is_valid, error_msg = self.dag_validator.validate_dag(definition)
        if not is_valid:
            raise WorkflowExecutionError(f"Invalid workflow definition: {error_msg}")
        
        # Validate all agents exist
        for step_id, step_def in definition['steps'].items():
            agent_type = step_def.get('agent_type')
            if not agent_type:
                raise WorkflowExecutionError(f"Step '{step_id}' missing agent_type")
            
            if not self.agent_registry.get_agent(agent_type):
                raise WorkflowExecutionError(f"Unknown agent type '{agent_type}' in step '{step_id}'")
        
        # Create template
        template = WorkflowTemplate(
            name=name,
            description=description,
            definition=definition,
            category=category,
            version="1.0.0",
            is_active=True,
            created_by=user.id if user else None
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Created workflow template '{name}' with {len(definition['steps'])} steps")
        return template
    
    async def start_run(
        self,
        db: AsyncSession,
        template_id: int,
        user: User,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> WorkflowRun:
        """
        Start a new workflow run from a template.
        Creates WorkflowRun and initializes step executions.
        """
        # Fetch template
        result = await db.execute(
            select(WorkflowTemplate).where(
                and_(
                    WorkflowTemplate.id == template_id,
                    WorkflowTemplate.is_active == True
                )
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise WorkflowExecutionError(f"Template {template_id} not found or inactive")
        
        # Create run with template snapshot
        run = WorkflowRun(
            name=f"Run of {template.name}",
            template_id=template.id,
            template_version=template.version,
            run_definition=template.definition,  # Audit trail
            run_id=uuid.uuid4(),
            status=WorkflowStatus.CREATED,
            user_id=user.id,
            total_steps=len(template.definition['steps']),
            completed_steps=0,
            max_retries=3
        )
        
        db.add(run)
        # Flush to assign run.id before creating child rows
        await db.flush()
        
        # Create step executions
        execution_order = self.dag_validator.get_execution_order(template.definition)
        for position, step_id in enumerate(execution_order):
            step_def = template.definition['steps'][step_id]
            
            # Merge initial_context into the first step's config to pass inputs (e.g., document_text)
            step_config: Dict[str, Any] = step_def.get('config', {}).copy()
            if position == 0 and initial_context:
                # Only include safe known keys to avoid leaking unrelated context
                for key in ("document_text",):
                    if key in initial_context and key not in step_config:
                        step_config[key] = initial_context[key]

            step_exec = WorkflowStepExecution()
            step_exec.run_id = run.id
            step_exec.step_id = step_id
            step_exec.agent_type = step_def['agent_type']
            step_exec.status = StepStatus.PENDING
            step_exec.execution_order = position
            step_exec.configuration = step_config
            db.add(step_exec)
        
        await db.commit()
        await db.refresh(run)
        
        logger.info(f"Started workflow run {run.run_id} from template '{template.name}'")
        return run
    
    async def execute_next_step(
        self,
        db: AsyncSession,
        run_id: uuid.UUID,
        user_prompt_override: Optional[str] = None
    ) -> Optional[WorkflowStepExecution]:
        """
        Execute the next pending step in a workflow run with comprehensive logging.
        Returns the executed step or None if no steps are ready.
        """
        logger.info(f"🔍 WORKFLOW SERVICE: Starting step execution for run {run_id}")
        
        try:
            # Get run with steps
            logger.debug(f"📊 Fetching workflow run from database")
            result = await db.execute(
                select(WorkflowRun)
                .options(selectinload(WorkflowRun.step_executions))
                .where(WorkflowRun.run_id == run_id)
            )
            run = result.scalar_one_or_none()
            
            if not run:
                logger.error(f"❌ Workflow run not found: {run_id}")
                raise WorkflowExecutionError(f"Run {run_id} not found")
            
            logger.info(f"✅ Found workflow run: ID={run.id}, Status={run.status}, Steps={len(run.step_executions)}")
            
            if run.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                logger.info(f"⚠️ Run {run.run_id} is in terminal state {run.status}")
                return None

        except Exception as e:
            logger.error(f"❌ Error fetching workflow run: {str(e)}")
            raise WorkflowExecutionError(f"Failed to fetch run {run_id}: {str(e)}")
        
        # Find next executable step
        next_step = await self._find_next_executable_step(db, run)
        if not next_step:
            # Check if all steps are complete
            all_complete = all(
                step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
                for step in run.step_executions
            )
            
            if all_complete:
                run.status = WorkflowStatus.COMPLETED
                run.completed_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Workflow run {run.run_id} completed successfully")
            
            return None
        
        # Execute step
        try:
            # Update run status if needed
            # Transition from created to running
            if (isinstance(run.status, str) and run.status == WorkflowStatus.CREATED.value) or run.status == WorkflowStatus.CREATED:
                run.status = WorkflowStatus.RUNNING
                run.started_at = datetime.utcnow()
            
            # Mark step as running
            next_step.status = StepStatus.RUNNING
            next_step.started_at = datetime.utcnow()
            next_step.retry_count += 1
            
            await db.commit()
            
            # Get input artifacts
            input_artifacts = await self._get_step_input_artifacts(db, run, next_step)
            
            # Execute agent
            agent = self.agent_registry.get_agent(next_step.agent_type)
            if not agent:
                raise WorkflowExecutionError(f"Agent '{next_step.agent_type}' not found")
            
            # Prepare execution context
            context = {
                'run_id': str(run.run_id),
                'step_id': next_step.step_id,
                'input_artifacts': input_artifacts,
                'config': next_step.configuration,
                'user_prompt': user_prompt_override
            }
            
            # Execute agent: if it has an extract method (DFD style), call it; else fallback to mock
            logger.info(f"🤖 AGENT EXECUTION: Starting {next_step.agent_type} agent")
            result: Dict[str, Any]
            try:
                # Prefer agent.extract returning (model, metadata)
                if hasattr(agent, "extract"):
                    logger.info(f"🔧 Agent has extract method, executing DFD-style extraction")
                    logger.debug(f"📝 Execution context: {context}")
                    
                    from app.services.llm_service import LLMService
                    logger.debug("🏗️ Initializing LLMService")
                    llm_service = LLMService()
                    
                    logger.debug(f"🔍 Getting LLM provider for agent: {next_step.agent_type}")
                    provider = await llm_service.get_provider(step=next_step.agent_type)
                    
                    logger.info(f"🚀 Calling agent.extract() with context and provider")
                    dfd_components, meta = await agent.extract(
                        context=AgentExecutionContext(**context),  # type: ignore[arg-type]
                        llm_provider=provider,
                        db_session=db,
                        settings_service=None,
                    )
                    logger.info(f"✅ Agent extraction completed successfully")
                    logger.debug(f"📊 Token usage: {meta}")
                    result = {
                        "status": "success",
                        "agent": next_step.agent_type,
                        "dfd_components": dfd_components.model_dump(),
                        "metadata": meta,
                    }
                else:
                    # Fallback to existing mock path
                    result = await self._execute_agent(agent, context)
            except Exception as exec_err:
                logger.error(f"Agent execution failed: {exec_err}")
                raise
            
            # Create output artifact
            output_artifact = WorkflowArtifact(
                run_id=run.id,
                producing_step_id=next_step.step_id,
                name=f"{next_step.step_id}_output",
                artifact_type='json',
                version=1,
                is_latest=True
            )
            output_artifact.set_content(result, 'json')
            
            db.add(output_artifact)
            
            # Update step execution
            next_step.status = StepStatus.COMPLETED
            next_step.completed_at = datetime.utcnow()
            # Persist to assign artifact ID
            await db.flush()
            next_step.output_artifacts = [output_artifact.id]
            if next_step.started_at and next_step.completed_at:
                next_step.duration_seconds = int((next_step.completed_at - next_step.started_at).total_seconds())
            
            # Update run progress
            run.completed_steps += 1
            
            # CRITICAL FIX: Check if this was the last step and mark run as COMPLETED immediately
            if run.completed_steps >= run.total_steps:
                logger.info(f"🎉 All steps completed! Marking run {run.run_id} as COMPLETED")
                run.status = WorkflowStatus.COMPLETED
                run.completed_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(next_step)
            
            logger.info(f"Successfully executed step '{next_step.step_id}' in run {run.run_id}")
            return next_step
            
        except Exception as e:
            logger.error(f"Error executing step '{next_step.step_id}': {str(e)}")
            
            # Mark step as failed
            next_step.status = StepStatus.FAILED
            next_step.error_message = str(e)
            next_step.completed_at = datetime.utcnow()
            
            # Check if we should retry
            if next_step.retry_count < run.max_retries:
                next_step.status = StepStatus.PENDING  # Reset for retry
                logger.info(f"Step '{next_step.step_id}' will be retried ({next_step.retry_count}/{run.max_retries})")
            else:
                # Mark run as failed if critical step fails
                run.status = WorkflowStatus.FAILED
                run.error_message = f"Step '{next_step.step_id}' failed after {run.max_retries} retries"
                run.completed_at = datetime.utcnow()
            
            await db.commit()
            raise
    
    async def _find_next_executable_step(
        self,
        db: AsyncSession,
        run: WorkflowRun
    ) -> Optional[WorkflowStepExecution]:
        """Find the next step that can be executed based on dependencies."""
        for step in sorted(run.step_executions, key=lambda s: (s.execution_order or 0)):
            if step.status != StepStatus.PENDING:
                continue
            
            # Check if all dependencies are complete
            try:
                deps = run.run_definition.get('steps', {}).get(step.step_id, {}).get('depends_on', [])
            except Exception:
                deps = []
            if deps:
                dep_steps = [s for s in run.step_executions if s.step_id in deps]
                all_deps_complete = all(s.status == StepStatus.COMPLETED for s in dep_steps)
                if not all_deps_complete:
                    continue
            
            return step
        
        return None
    
    async def _get_step_input_artifacts(
        self,
        db: AsyncSession,
        run: WorkflowRun,
        step: WorkflowStepExecution
    ) -> List[WorkflowArtifact]:
        """Get input artifacts for a step based on dependencies."""
        deps = run.run_definition.get('steps', {}).get(step.step_id, {}).get('depends_on', [])
        if not deps:
            return []
        
        # Get latest artifacts from dependent steps
        result = await db.execute(
            select(WorkflowArtifact).where(
                and_(
                    WorkflowArtifact.run_id == run.id,
                    WorkflowArtifact.producing_step_id.in_(deps),
                    WorkflowArtifact.is_latest == True
                )
            )
        )
        
        return list(result.scalars().all())
    
    async def _execute_agent(self, agent: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an agent with the given context.
        Simplified for Phase 2 - will be enhanced in later phases.
        """
        # For Phase 2, we'll return a mock result
        # In Phase 3+, this will integrate with the actual agent execution
        return {
            'status': 'success',
            'agent': context['step_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'message': f"Executed {context['step_id']} successfully",
            'data': {
                'input_artifact_count': len(context['input_artifacts']),
                'config': context['config']
            }
        }
    
    async def get_run_status(
        self,
        db: AsyncSession,
        run_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get detailed status of a workflow run."""
        result = await db.execute(
            select(WorkflowRun)
            .options(selectinload(WorkflowRun.step_executions))
            .where(WorkflowRun.run_id == run_id)
        )
        run = result.scalar_one_or_none()
        
        if not run:
            raise WorkflowExecutionError(f"Run {run_id} not found")
        
        # Get artifacts count
        artifact_result = await db.execute(
            select(WorkflowArtifact).where(WorkflowArtifact.run_id == run.id)
        )
        artifacts = list(artifact_result.scalars().all())
        
        return {
            'run_id': str(run.run_id),
            'status': run.status.value if hasattr(run.status, 'value') else run.status,
            'progress': run.get_progress_percentage(),
            'total_steps': run.total_steps,
            'completed_steps': run.completed_steps,
            'started_at': run.started_at.isoformat() if run.started_at else None,
            'completed_at': run.completed_at.isoformat() if run.completed_at else None,
            'steps': [
                {
                    'step_id': step.step_id,
                    'agent_type': step.agent_type,
                    'status': step.status.value if hasattr(step.status, 'value') else step.status,
                    'position': step.execution_order,
                    'retry_count': step.retry_count,
                    'execution_time_ms': (step.duration_seconds or 0) * 1000 if getattr(step, 'duration_seconds', None) is not None else None
                }
                for step in sorted(run.step_executions, key=lambda s: (s.execution_order or 0))
            ],
            'artifacts_count': len(artifacts),
            'can_retry': run.can_retry(),
            'is_terminal': run.is_terminal()
        }
    
    async def cancel_run(
        self,
        db: AsyncSession,
        run_id: uuid.UUID
    ) -> WorkflowRun:
        """Cancel a running workflow."""
        result = await db.execute(
            select(WorkflowRun).where(WorkflowRun.run_id == run_id)
        )
        run = result.scalar_one_or_none()
        
        if not run:
            raise WorkflowExecutionError(f"Run {run_id} not found")
        
        if run.is_terminal():
            raise WorkflowExecutionError(f"Cannot cancel run in {run.status} state")
        
        run.status = WorkflowStatus.CANCELLED
        run.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(run)
        
        logger.info(f"Cancelled workflow run {run.run_id}")
        return run