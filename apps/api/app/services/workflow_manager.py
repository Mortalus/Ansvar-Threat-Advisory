"""
Workflow Manager Service

Orchestrates agent-based workflow execution with automation controls,
confidence-based decision making, and client review integration.
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from ..models.workflow_template import (
    WorkflowTemplate, 
    WorkflowExecution, 
    WorkflowStepExecution,
    WorkflowStepConfig,
    AutomationSettings
)
from ..core.agents.registry import agent_registry, AgentRegistry
from ..core.agents.base import BaseAgent, AgentExecutionContext, ThreatOutput
# from ..services.pipeline_manager import PipelineManager
# from ..services.llm_service import LLMService
# Temporary workaround - using mock LLMService
class LLMService:
    pass

logger = logging.getLogger(__name__)


class WorkflowManager:
    """
    Manages agent-based workflow execution with automation and review controls
    """
    
    def __init__(self, db_session: AsyncSession, llm_service: LLMService):
        self.db = db_session
        self.llm_service = llm_service
        self.agent_registry = agent_registry
# self.pipeline_manager = PipelineManager()
        
    async def create_template(
        self, 
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        automation_settings: Dict[str, Any] = None,
        client_access_rules: Dict[str, Any] = None,
        created_by: int = None
    ) -> WorkflowTemplate:
        """Create a new workflow template"""
        
        template = WorkflowTemplate(
            name=name,
            description=description,
            steps=steps,
            automation_settings=automation_settings or {},
            client_access_rules=client_access_rules or {},
            created_by=created_by
        )
        
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        
        logger.info(f"Created workflow template: {name} with {len(steps)} steps")
        return template
    
    async def get_template(self, template_id: UUID) -> Optional[WorkflowTemplate]:
        """Retrieve workflow template by ID"""
        stmt = select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_templates(self, active_only: bool = True) -> List[WorkflowTemplate]:
        """List all workflow templates"""
        stmt = select(WorkflowTemplate)
        if active_only:
            stmt = stmt.where(WorkflowTemplate.is_active == True)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def start_workflow(
        self,
        template_id: UUID,
        client_id: str = None,
        client_email: str = None,
        initial_data: Dict[str, Any] = None,
        automation_overrides: Dict[str, Any] = None
    ) -> WorkflowExecution:
        """Start a new workflow execution"""
        
        # Get template
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Create execution record
        execution = WorkflowExecution(
            template_id=template_id,
            client_id=client_id,
            client_email=client_email,
            data=initial_data or {},
            automation_overrides=automation_overrides or {},
            status='pending'
        )
        
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        
        logger.info(f"Started workflow execution {execution.id} from template {template.name}")
        return execution
    
    async def execute_workflow(self, execution_id: UUID) -> Dict[str, Any]:
        """Execute workflow steps with automation and review controls"""
        
        # Get execution with template
        stmt = (
            select(WorkflowExecution)
            .options(selectinload(WorkflowExecution.template))
            .where(WorkflowExecution.id == execution_id)
        )
        result = await self.db.execute(stmt)
        execution = result.scalar_one_or_none()
        
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        if execution.status in ['completed', 'failed']:
            return {"status": execution.status, "message": "Workflow already completed"}
        
        # Update execution status
        execution.status = 'running'
        execution.last_activity_at = datetime.utcnow()
        await self.db.commit()
        
        try:
            results = await self._execute_steps(execution)
            execution.status = 'completed'
            execution.completed_at = datetime.utcnow()
            
            logger.info(f"Workflow execution {execution_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow execution {execution_id} failed: {e}")
            execution.status = 'failed'
            results = {"error": str(e)}
        
        finally:
            execution.last_activity_at = datetime.utcnow()
            await self.db.commit()
        
        return {
            "status": execution.status,
            "results": results,
            "execution_id": str(execution_id)
        }
    
    async def _execute_steps(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute individual workflow steps"""
        
        template = execution.template
        steps = template.steps
        automation_settings = AutomationSettings(**template.automation_settings)
        
        results = {
            "steps": [],
            "threats": [],
            "metadata": {
                "total_steps": len(steps),
                "completed_steps": 0,
                "automated_steps": 0,
                "manual_reviews": 0
            }
        }
        
        # Execute each step
        for step_index, step_config in enumerate(steps):
            step_name = step_config.get('name', f'Step {step_index + 1}')
            logger.info(f"Executing step {step_index + 1}: {step_name}")
            
            try:
                step_result = await self._execute_step(
                    execution, 
                    step_index, 
                    step_config, 
                    automation_settings
                )
                
                results["steps"].append(step_result)
                results["metadata"]["completed_steps"] += 1
                
                if step_result.get("automated", False):
                    results["metadata"]["automated_steps"] += 1
                
                if step_result.get("requires_review", False):
                    results["metadata"]["manual_reviews"] += 1
                
                # Add threats to global results
                if "threats" in step_result:
                    results["threats"].extend(step_result["threats"])
                
                # Update execution progress
                execution.current_step = step_index + 1
                execution.data.update({
                    f"step_{step_index}_result": step_result
                })
                await self.db.commit()
                
            except Exception as e:
                logger.error(f"Step {step_index + 1} failed: {e}")
                results["steps"].append({
                    "step_index": step_index,
                    "step_name": step_name,
                    "status": "failed",
                    "error": str(e)
                })
                # Continue with next step or fail entire workflow based on config
                if step_config.get("stop_on_error", False):
                    raise
        
        return results
    
    async def _execute_step(
        self, 
        execution: WorkflowExecution, 
        step_index: int, 
        step_config: Dict[str, Any],
        automation_settings: AutomationSettings
    ) -> Dict[str, Any]:
        """Execute a single workflow step with agent"""
        
        step_name = step_config.get('name', f'Step {step_index + 1}')
        agent_type = step_config.get('agent_type')
        
        # Create step execution record
        step_execution = WorkflowStepExecution(
            workflow_execution_id=execution.id,
            step_index=step_index,
            step_name=step_name,
            agent_name=agent_type,
            status='running',
            started_at=datetime.utcnow(),
            input_data=step_config
        )
        
        self.db.add(step_execution)
        await self.db.commit()
        
        try:
            # Get agent for this step
            agent = self.agent_registry.get_agent(agent_type)
            if not agent:
                raise ValueError(f"Agent {agent_type} not found")
            
            # Prepare execution context
            context = self._build_execution_context(execution, step_config)
            
            # Execute agent
            start_time = datetime.utcnow()
            threats = await agent.analyze(
                context=context,
                llm_provider=self.llm_service,
                db_session=self.db
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Calculate confidence score
            avg_confidence = sum(t.confidence_score for t in threats) / len(threats) if threats else 0.0
            
            # Determine if automation should be applied
            automated, requires_review = self._should_automate(
                avg_confidence, 
                step_config, 
                automation_settings
            )
            
            # Update step execution
            step_execution.status = 'completed'
            step_execution.completed_at = datetime.utcnow()
            step_execution.execution_time_ms = int(execution_time)
            step_execution.confidence_score = avg_confidence
            step_execution.automated = automated
            step_execution.requires_review = requires_review
            step_execution.output_data = {
                "threats": [t.model_dump() for t in threats],
                "confidence_score": avg_confidence,
                "threat_count": len(threats)
            }
            
            await self.db.commit()
            
            logger.info(f"Step {step_name} completed: {len(threats)} threats, confidence {avg_confidence:.2f}")
            
            return {
                "step_index": step_index,
                "step_name": step_name,
                "agent_name": agent_type,
                "status": "completed",
                "automated": automated,
                "requires_review": requires_review,
                "confidence_score": avg_confidence,
                "execution_time_ms": int(execution_time),
                "threat_count": len(threats),
                "threats": [t.to_v3_format() for t in threats]
            }
            
        except Exception as e:
            step_execution.status = 'failed'
            step_execution.error_message = str(e)
            step_execution.completed_at = datetime.utcnow()
            await self.db.commit()
            raise
    
    def _build_execution_context(
        self, 
        execution: WorkflowExecution, 
        step_config: Dict[str, Any]
    ) -> AgentExecutionContext:
        """Build agent execution context from workflow data"""
        
        # Get document content from execution data or step inputs
        document_content = execution.data.get('document_content')
        if not document_content and 'document_path' in execution.data:
            # Load document if path provided
            document_content = self._load_document(execution.data['document_path'])
        
        # Get components from previous steps or initial data
        components = execution.data.get('components', [])
        
        # Merge step parameters from both legacy 'parameters' and 'optional_parameters'
        # so templates can supply prompt/input controls regardless of field name.
        step_parameters: Dict[str, Any] = {}
        try:
            if isinstance(step_config.get('parameters'), dict):
                step_parameters.update(step_config.get('parameters') or {})
            if isinstance(step_config.get('optional_parameters'), dict):
                # optional_parameters take precedence when keys overlap
                step_parameters.update(step_config.get('optional_parameters') or {})
        except Exception:
            # Defensive: ignore malformed parameters without failing the step
            step_parameters = {}

        # Get existing threats from previous steps with optional limit controls
        existing_threats: List[Dict[str, Any]] = []
        for key, value in execution.data.items():
            if key.startswith('step_') and key.endswith('_result'):
                if isinstance(value, dict) and 'threats' in value:
                    existing_threats.extend(value.get('threats') or [])

        # Apply limit to prior threats to control prompt size if configured
        try:
            prior_limit = int(step_parameters.get('existing_threats_limit', 50))
            if prior_limit > 0 and len(existing_threats) > prior_limit:
                existing_threats = existing_threats[:prior_limit]
        except Exception:
            # Ignore invalid limits
            pass

        return AgentExecutionContext(
            document_text=document_content,
            components=components,
            existing_threats=existing_threats,
            pipeline_id=str(execution.id),
            user_config=step_parameters
        )
    
    def _should_automate(
        self,
        confidence_score: float,
        step_config: Dict[str, Any],
        automation_settings: AutomationSettings
    ) -> Tuple[bool, bool]:
        """Determine if step should be automated or require manual review"""
        
        # Check if automation is globally enabled
        if not automation_settings.enabled:
            return False, True
        
        # Check step-level automation settings
        step_automation_enabled = step_config.get('automation_enabled', True)
        if not step_automation_enabled:
            return False, True
        
        # Check confidence thresholds
        step_threshold = step_config.get('confidence_threshold', automation_settings.confidence_threshold)
        
        if confidence_score >= step_threshold:
            # High confidence - can be automated
            return True, step_config.get('review_required', False)
        elif confidence_score >= step_threshold * 0.8:
            # Medium confidence - flag for quick review
            return False, True
        else:
            # Low confidence - require manual review
            return False, True
    
    def _load_document(self, document_path: str) -> Optional[str]:
        """Load document content from file path"""
        try:
            # This would integrate with your document storage system
            # For now, return None to indicate document not found
            logger.warning(f"Document loading not implemented for path: {document_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to load document {document_path}: {e}")
            return None
    
    async def get_execution_status(self, execution_id: UUID) -> Dict[str, Any]:
        """Get current status of workflow execution"""
        
        stmt = (
            select(WorkflowExecution)
            .options(
                selectinload(WorkflowExecution.template),
                selectinload(WorkflowExecution.step_executions)
            )
            .where(WorkflowExecution.id == execution_id)
        )
        result = await self.db.execute(stmt)
        execution = result.scalar_one_or_none()
        
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        # Calculate progress
        total_steps = len(execution.template.steps)
        completed_steps = len([s for s in execution.step_executions if s.status == 'completed'])
        progress_percent = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        return {
            "execution_id": str(execution.id),
            "template_name": execution.template.name,
            "status": execution.status,
            "current_step": execution.current_step,
            "total_steps": total_steps,
            "progress_percent": progress_percent,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "last_activity": execution.last_activity_at.isoformat() if execution.last_activity_at else None,
            "client_id": execution.client_id,
            "client_email": execution.client_email,
            "steps": [
                {
                    "step_index": step.step_index,
                    "step_name": step.step_name,
                    "agent_name": step.agent_name,
                    "status": step.status,
                    "automated": step.automated,
                    "confidence_score": step.confidence_score,
                    "requires_review": step.requires_review,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "execution_time_ms": step.execution_time_ms
                }
                for step in execution.step_executions
            ]
        }
    
    async def approve_step(
        self, 
        execution_id: UUID, 
        step_index: int, 
        approved_by: int,
        modifications: Dict[str, Any] = None
    ) -> bool:
        """Approve a workflow step that requires review"""
        
        stmt = (
            select(WorkflowStepExecution)
            .where(
                WorkflowStepExecution.workflow_execution_id == execution_id,
                WorkflowStepExecution.step_index == step_index
            )
        )
        result = await self.db.execute(stmt)
        step_execution = result.scalar_one_or_none()
        
        if not step_execution:
            return False
        
        step_execution.review_status = 'approved'
        step_execution.reviewed_by = approved_by
        step_execution.reviewed_at = datetime.utcnow()
        
        if modifications:
            # Apply modifications to the step output
            step_execution.output_data.update(modifications)
        
        await self.db.commit()
        
        logger.info(f"Step {step_index} approved by user {approved_by}")
        return True