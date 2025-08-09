"""
Phase 2: Workflow Execution Celery Tasks
Handles asynchronous workflow step execution with robust error handling.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from celery import Task
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.database import get_async_session
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_async_session_context():
    """Context manager for async database sessions in Celery tasks."""
    async for session in get_async_session():
        try:
            yield session
        finally:
            await session.close()
from app.models.workflow import (
    WorkflowRun, WorkflowStepExecution, WorkflowArtifact,
    WorkflowStatus, StepStatus
)
from app.services.workflow_service import WorkflowService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class WorkflowTask(Task):
    """Base task class with database session management."""
    
    def __init__(self):
        super().__init__()
        self.workflow_service = None
    
    def __call__(self, *args, **kwargs):
        if not self.workflow_service:
            self.workflow_service = WorkflowService()
        return self.run(*args, **kwargs)


@celery_app.task(base=WorkflowTask, bind=True, name='workflow.execute_step')
async def execute_workflow_step(
    self,
    run_id: str,
    step_id: str,
    prompt_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a single workflow step asynchronously.
    
    Args:
        run_id: UUID of the workflow run
        step_id: ID of the step to execute
        prompt_override: Optional user prompt override
    
    Returns:
        Execution result with status and artifacts
    """
    async with get_async_session_context() as db:
        try:
            # Fetch run and step
            run_result = await db.execute(
                select(WorkflowRun)
                .options(selectinload(WorkflowRun.step_executions))
                .where(WorkflowRun.id == uuid.UUID(run_id))
            )
            run = run_result.scalar_one_or_none()
            
            if not run:
                raise ValueError(f"Run {run_id} not found")
            
            # Find the specific step
            step = next(
                (s for s in run.step_executions if s.step_id == step_id),
                None
            )
            
            if not step:
                raise ValueError(f"Step {step_id} not found in run {run_id}")
            
            # Check if step is ready to execute
            if step.status != StepStatus.PENDING:
                logger.warning(f"Step {step_id} is not pending, current status: {step.status}")
                return {
                    'status': 'skipped',
                    'reason': f'Step already in {step.status} state'
                }
            
            # Check dependencies
            if step.depends_on:
                dep_result = await db.execute(
                    select(WorkflowStepExecution).where(
                        and_(
                            WorkflowStepExecution.run_id == run.id,
                            WorkflowStepExecution.step_id.in_(step.depends_on)
                        )
                    )
                )
                dep_steps = list(dep_result.scalars().all())
                
                incomplete_deps = [
                    d.step_id for d in dep_steps 
                    if d.status != StepStatus.COMPLETED
                ]
                
                if incomplete_deps:
                    return {
                        'status': 'waiting',
                        'waiting_for': incomplete_deps
                    }
            
            # Update step status
            step.status = StepStatus.RUNNING
            step.started_at = datetime.utcnow()
            step.retry_count += 1
            await db.commit()
            
            # Get input artifacts from dependencies
            input_artifacts = []
            if step.depends_on:
                artifact_result = await db.execute(
                    select(WorkflowArtifact).where(
                        and_(
                            WorkflowArtifact.run_id == run.id,
                            WorkflowArtifact.step_id.in_(step.depends_on),
                            WorkflowArtifact.is_latest == True
                        )
                    )
                )
                input_artifacts = list(artifact_result.scalars().all())
            
            # Execute the agent
            agent_result = await self._execute_agent_task(
                step.agent_type,
                step.config,
                input_artifacts,
                prompt_override
            )
            
            # Create output artifact
            output_artifact = WorkflowArtifact(
                run_id=run.id,
                step_id=step.step_id,
                name=f"{step.step_id}_output",
                artifact_type='json',
                version=1,
                is_latest=True,
                created_by_id=run.started_by_id
            )
            output_artifact.set_content(agent_result, 'json')
            db.add(output_artifact)
            
            # Update step completion
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.utcnow()
            step.output_artifact_ids = [str(output_artifact.id)]
            step.execution_time_ms = int(
                (step.completed_at - step.started_at).total_seconds() * 1000
            )
            
            # Update run progress
            run.completed_steps += 1
            
            # Check if workflow is complete
            all_steps_complete = all(
                s.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
                for s in run.step_executions
            )
            
            if all_steps_complete:
                run.status = WorkflowStatus.COMPLETED
                run.completed_at = datetime.utcnow()
                logger.info(f"Workflow run {run.run_id} completed")
            
            await db.commit()
            
            # Trigger next steps if any are ready
            await self._trigger_next_steps(run_id)
            
            return {
                'status': 'success',
                'step_id': step_id,
                'execution_time_ms': step.execution_time_ms,
                'artifact_id': str(output_artifact.id),
                'workflow_complete': all_steps_complete
            }
            
        except Exception as e:
            logger.error(f"Error executing step {step_id}: {str(e)}")
            
            # Update step as failed
            async with get_async_session_context() as error_db:
                step_result = await error_db.execute(
                    select(WorkflowStepExecution).where(
                        and_(
                            WorkflowStepExecution.run_id == uuid.UUID(run_id),
                            WorkflowStepExecution.step_id == step_id
                        )
                    )
                )
                step = step_result.scalar_one_or_none()
                
                if step:
                    step.status = StepStatus.FAILED
                    step.error_message = str(e)
                    step.completed_at = datetime.utcnow()
                    
                    # Check retry logic
                    run_result = await error_db.execute(
                        select(WorkflowRun).where(WorkflowRun.id == uuid.UUID(run_id))
                    )
                    run = run_result.scalar_one_or_none()
                    
                    if run and step.retry_count < run.max_retries:
                        # Schedule retry
                        step.status = StepStatus.PENDING
                        logger.info(f"Scheduling retry for step {step_id} ({step.retry_count}/{run.max_retries})")
                        
                        # Reschedule the task with exponential backoff
                        retry_delay = 2 ** step.retry_count  # Exponential backoff
                        execute_workflow_step.apply_async(
                            args=[run_id, step_id, prompt_override],
                            countdown=retry_delay
                        )
                    else:
                        # Mark workflow as failed
                        if run:
                            run.status = WorkflowStatus.FAILED
                            run.error_message = f"Step {step_id} failed: {str(e)}"
                            run.completed_at = datetime.utcnow()
                    
                    await error_db.commit()
            
            raise

async def _execute_agent_task(
    agent_type: str,
    config: Dict[str, Any],
    input_artifacts: list,
    prompt_override: Optional[str]
) -> Dict[str, Any]:
    """
    Execute agent with given configuration.
    This is a simplified version for Phase 2.
    """
    # For Phase 2, return mock result
    # Phase 3+ will integrate actual agent execution
    return {
        'agent_type': agent_type,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'success',
        'config': config,
        'input_count': len(input_artifacts),
        'prompt_used': prompt_override or 'default',
        'results': {
            'message': f"Agent {agent_type} executed successfully",
            'data': {'mock': True, 'phase': 2}
        }
    }

async def _trigger_next_steps(run_id: str):
    """
    Check and trigger any steps that are now ready to execute.
    """
    async with get_async_session_context() as db:
        # Get run with all steps
        result = await db.execute(
            select(WorkflowRun)
            .options(selectinload(WorkflowRun.step_executions))
            .where(WorkflowRun.id == uuid.UUID(run_id))
        )
        run = result.scalar_one_or_none()
        
        if not run or run.status != WorkflowStatus.RUNNING:
            return
        
        # Find steps ready to execute
        for step in run.step_executions:
            if step.status != StepStatus.PENDING:
                continue
            
            # Check if dependencies are complete
            deps_complete = True
            if step.depends_on:
                for dep_id in step.depends_on:
                    dep_step = next(
                        (s for s in run.step_executions if s.step_id == dep_id),
                        None
                    )
                    if not dep_step or dep_step.status != StepStatus.COMPLETED:
                        deps_complete = False
                        break
            
            if deps_complete:
                # Trigger this step
                logger.info(f"Triggering step {step.step_id} in run {run.run_id}")
                execute_workflow_step.apply_async(
                    args=[str(run.id), step.step_id, None]
                )


@celery_app.task(name='workflow.execute_run')
async def execute_workflow_run(run_id: str) -> Dict[str, Any]:
    """
    Execute an entire workflow run by triggering initial steps.
    
    Args:
        run_id: UUID of the workflow run
    
    Returns:
        Status of workflow execution start
    """
    async with get_async_session_context() as db:
        # Get run with steps
        result = await db.execute(
            select(WorkflowRun)
            .options(selectinload(WorkflowRun.step_executions))
            .where(WorkflowRun.id == uuid.UUID(run_id))
        )
        run = result.scalar_one_or_none()
        
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        if run.status != WorkflowStatus.PENDING:
            return {
                'status': 'skipped',
                'reason': f'Run already in {run.status} state'
            }
        
        # Update run status
        run.status = WorkflowStatus.RUNNING
        run.started_at = datetime.utcnow()
        await db.commit()
        
        # Find and trigger initial steps (no dependencies)
        initial_steps = [
            step for step in run.step_executions
            if not step.depends_on
        ]
        
        triggered_count = 0
        for step in initial_steps:
            logger.info(f"Triggering initial step {step.step_id}")
            execute_workflow_step.apply_async(
                args=[str(run.id), step.step_id, None]
            )
            triggered_count += 1
        
        return {
            'status': 'started',
            'run_id': str(run.id),
            'initial_steps_triggered': triggered_count,
            'total_steps': run.total_steps
        }


@celery_app.task(name='workflow.cleanup_artifacts')
async def cleanup_expired_artifacts() -> Dict[str, Any]:
    """
    Periodic task to clean up expired workflow artifacts.
    Should be run daily via Celery beat.
    """
    async with get_async_session_context() as db:
        # Find expired artifacts
        result = await db.execute(
            select(WorkflowArtifact).where(
                and_(
                    WorkflowArtifact.expires_at != None,
                    WorkflowArtifact.expires_at < datetime.utcnow()
                )
            )
        )
        expired = list(result.scalars().all())
        
        deleted_count = 0
        for artifact in expired:
            try:
                # Clear content
                artifact.content_json = None
                artifact.content_text = None
                artifact.content_binary = None
                artifact.is_deleted = True
                deleted_count += 1
                
                logger.info(f"Cleaned up expired artifact {artifact.id}")
            except Exception as e:
                logger.error(f"Error cleaning artifact {artifact.id}: {e}")
        
        await db.commit()
        
        return {
            'status': 'success',
            'artifacts_cleaned': deleted_count,
            'timestamp': datetime.utcnow().isoformat()
        }