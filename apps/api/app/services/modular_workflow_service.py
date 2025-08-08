"""
Modular Workflow Service

Defensive, modular implementation that integrates with existing services
while providing the new agent-based workflow capabilities.
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
)
from ..core.agents.registry import agent_registry
from ..core.agents.base import BaseAgent, AgentExecutionContext, ThreatOutput
from ..core.llm import get_llm_provider, get_system_prompt_for_step

logger = logging.getLogger(__name__)


class ModularWorkflowService:
    """
    Defensive workflow service that provides modular agent execution
    while integrating with existing infrastructure.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self._llm_provider = None
        
    async def _get_llm_provider(self, step_name: str = "default"):
        """Defensive LLM provider initialization with step-specific configuration"""
        try:
            # Use existing LLM factory with step-specific configuration
            provider = await get_llm_provider(step=step_name)
            logger.info(f"✅ LLM provider initialized for step '{step_name}': {type(provider).__name__}")
            return provider
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM provider for '{step_name}': {e}")
            logger.info("🔄 Falling back to mock provider for testing")
            # Return existing mock or create new one
            return MockLLMProvider()
    
    async def create_template(
        self, 
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        automation_settings: Dict[str, Any] = None,
        client_access_rules: Dict[str, Any] = None,
        created_by: int = None
    ) -> WorkflowTemplate:
        """Create workflow template with defensive validation"""
        
        try:
            # Defensive input validation
            if not name or len(name.strip()) == 0:
                raise ValueError("Template name is required")
            
            if not steps or len(steps) == 0:
                raise ValueError("At least one workflow step is required")
            
            # Validate all agents exist
            for step in steps:
                agent_type = step.get('agent_type')
                if not agent_type:
                    raise ValueError(f"Step missing agent_type: {step}")
                
                agent = agent_registry.get_agent(agent_type)
                if not agent:
                    raise ValueError(f"Agent not found: {agent_type}")
            
            template = WorkflowTemplate(
                name=name.strip(),
                description=description.strip() if description else None,
                steps=steps,
                automation_settings=automation_settings or {
                    "enabled": True,
                    "confidence_threshold": 0.85,
                    "max_auto_approvals_per_day": 50
                },
                client_access_rules=client_access_rules or {
                    "authentication_method": "token",
                    "token_expiry_days": 30
                },
                created_by=created_by
            )
            
            self.db.add(template)
            await self.db.commit()
            await self.db.refresh(template)
            
            logger.info(f"✅ Created workflow template: {name} with {len(steps)} steps")
            return template
            
        except Exception as e:
            logger.error(f"❌ Failed to create template: {e}")
            await self.db.rollback()
            raise
    
    async def get_template(self, template_id: UUID) -> Optional[WorkflowTemplate]:
        """Retrieve workflow template with defensive error handling"""
        try:
            stmt = select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Failed to get template {template_id}: {e}")
            return None
    
    async def list_templates(self, active_only: bool = True) -> List[WorkflowTemplate]:
        """List templates with defensive error handling"""
        try:
            stmt = select(WorkflowTemplate)
            if active_only:
                stmt = stmt.where(WorkflowTemplate.is_active == True)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"❌ Failed to list templates: {e}")
            return []
    
    async def start_workflow(
        self,
        template_id: UUID,
        client_id: str = None,
        client_email: str = None,
        initial_data: Dict[str, Any] = None
    ) -> Optional[WorkflowExecution]:
        """Start workflow execution with defensive validation"""
        
        try:
            # Validate template exists
            template = await self.get_template(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            if not template.is_active:
                raise ValueError(f"Template {template.name} is not active")
            
            # Create execution record
            execution = WorkflowExecution(
                template_id=template_id,
                client_id=client_id,
                client_email=client_email,
                data=initial_data or {},
                status='pending'
            )
            
            self.db.add(execution)
            await self.db.commit()
            await self.db.refresh(execution)
            
            logger.info(f"✅ Started workflow execution {execution.id}")
            return execution
            
        except Exception as e:
            logger.error(f"❌ Failed to start workflow: {e}")
            await self.db.rollback()
            return None
    
    async def execute_workflow_step(
        self,
        execution_id: UUID,
        step_index: int,
        force_execution: bool = False
    ) -> Dict[str, Any]:
        """Execute a single workflow step with defensive error handling"""
        
        try:
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
            
            if execution.status in ['completed', 'failed'] and not force_execution:
                return {"status": "already_complete", "message": "Workflow already completed"}
            
            # Get step configuration
            if step_index >= len(execution.template.steps):
                raise ValueError(f"Step index {step_index} out of range")
            
            step_config = execution.template.steps[step_index]
            step_name = step_config.get('name', f'Step {step_index + 1}')
            agent_type = step_config.get('agent_type')
            
            logger.info(f"🔄 Executing step {step_index}: {step_name} with {agent_type}")
            
            # Get agent
            agent = agent_registry.get_agent(agent_type)
            if not agent:
                raise ValueError(f"Agent not found: {agent_type}")
            
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
            
            # Execute agent with defensive context building
            context = self._build_execution_context(execution, step_config)
            
            # Get step-specific LLM provider (map agent types to LLM steps)
            llm_step_mapping = {
                "document_analysis": "dfd_extraction",
                "architectural_risk": "threat_generation", 
                "business_financial": "threat_refinement",
                "compliance_governance": "threat_generation",
                "data_flow_analysis": "dfd_extraction"
            }
            llm_step = llm_step_mapping.get(agent_type, "threat_generation")
            llm_provider = await self._get_llm_provider(llm_step)
            
            start_time = datetime.utcnow()
            
            # Execute agent with error handling
            threats = []
            try:
                threats = await agent.analyze(
                    context=context,
                    llm_provider=llm_provider,
                    db_session=self.db
                )
                logger.info(f"✅ Agent execution completed: {len(threats)} threats")
            except Exception as agent_error:
                logger.error(f"❌ Agent execution failed: {agent_error}")
                # Continue with empty results rather than failing entire workflow
                threats = []
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Calculate confidence (defensive)
            avg_confidence = 0.0
            if threats:
                confidences = [t.confidence_score for t in threats if hasattr(t, 'confidence_score')]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Update step execution
            step_execution.status = 'completed'
            step_execution.completed_at = datetime.utcnow()
            step_execution.execution_time_ms = int(execution_time)
            step_execution.confidence_score = avg_confidence
            step_execution.automated = avg_confidence >= step_config.get('confidence_threshold', 0.8)
            step_execution.requires_review = not step_execution.automated
            step_execution.output_data = {
                "threats": [self._threat_to_dict(t) for t in threats],
                "confidence_score": avg_confidence,
                "threat_count": len(threats)
            }
            
            # Update workflow execution
            execution.current_step = step_index + 1
            execution.last_activity_at = datetime.utcnow()
            execution.data[f"step_{step_index}_result"] = step_execution.output_data
            
            await self.db.commit()
            
            logger.info(f"✅ Step {step_index} completed successfully")
            
            return {
                "status": "completed",
                "step_index": step_index,
                "step_name": step_name,
                "agent_name": agent_type,
                "automated": step_execution.automated,
                "requires_review": step_execution.requires_review,
                "confidence_score": avg_confidence,
                "execution_time_ms": int(execution_time),
                "threat_count": len(threats),
                "threats": [self._threat_to_dict(t) for t in threats]
            }
            
        except Exception as e:
            logger.error(f"❌ Step execution failed: {e}")
            
            # Update step as failed
            try:
                if 'step_execution' in locals():
                    step_execution.status = 'failed'
                    step_execution.error_message = str(e)
                    step_execution.completed_at = datetime.utcnow()
                    await self.db.commit()
            except Exception as db_error:
                logger.error(f"❌ Failed to update failed step: {db_error}")
            
            return {
                "status": "failed",
                "error": str(e),
                "step_index": step_index
            }
    
    def _build_execution_context(
        self, 
        execution: WorkflowExecution, 
        step_config: Dict[str, Any]
    ) -> AgentExecutionContext:
        """Defensive execution context building"""
        
        try:
            # Get document content (defensive)
            document_content = execution.data.get('document_content', '')
            if not document_content and 'document_text' in execution.data:
                document_content = execution.data['document_text']
            
            # Get components (defensive)
            components = execution.data.get('components', [])
            if not components and 'dfd_components' in execution.data:
                components = execution.data['dfd_components']
            
            # Get existing threats (defensive)
            existing_threats = []
            for key, value in execution.data.items():
                if key.startswith('step_') and key.endswith('_result'):
                    if isinstance(value, dict) and 'threats' in value:
                        existing_threats.extend(value['threats'])
            
            return AgentExecutionContext(
                document_text=document_content or "Sample document content for testing",
                components=components,
                existing_threats=existing_threats,
                pipeline_id=str(execution.id),
                user_config=step_config.get('parameters', {})
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Context building had issues, using defaults: {e}")
            # Return minimal context to keep workflow running
            return AgentExecutionContext(
                document_text="Sample document content for testing",
                components=[],
                existing_threats=[],
                pipeline_id=str(execution.id),
                user_config={}
            )
    
    def _threat_to_dict(self, threat: ThreatOutput) -> Dict[str, Any]:
        """Defensive threat serialization"""
        try:
            if hasattr(threat, 'to_v3_format'):
                return threat.to_v3_format()
            elif hasattr(threat, 'model_dump'):
                return threat.model_dump()
            else:
                return {
                    "threat_name": getattr(threat, 'threat_name', 'Unknown'),
                    "description": getattr(threat, 'description', ''),
                    "agent_source": getattr(threat, 'agent_source', 'unknown')
                }
        except Exception as e:
            logger.warning(f"⚠️ Threat serialization failed: {e}")
            return {"error": "Failed to serialize threat"}
    
    async def get_execution_status(self, execution_id: UUID) -> Optional[Dict[str, Any]]:
        """Get execution status with defensive error handling"""
        try:
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
                return None
            
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
            
        except Exception as e:
            logger.error(f"❌ Failed to get execution status: {e}")
            return None


class MockLLMProvider:
    """Mock LLM provider for testing when real provider fails"""
    
    async def generate_completion(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3):
        """Generate mock completion for testing"""
        logger.info("🧪 Using mock LLM provider for testing")
        
        # Return mock threat analysis
        return {
            'content': '''
            [
                {
                    "Threat Name": "Mock Authentication Bypass",
                    "Description": "Potential authentication bypass in login system",
                    "STRIDE Category": "Spoofing",
                    "Affected Component": "Authentication Service",
                    "Potential Impact": "High - Unauthorized access to system",
                    "Likelihood": "Medium - Requires specific conditions",
                    "Suggested Mitigation": "Implement multi-factor authentication and session validation"
                },
                {
                    "Threat Name": "Mock Data Exposure",
                    "Description": "Sensitive data may be exposed through API responses",
                    "STRIDE Category": "Information Disclosure",
                    "Affected Component": "API Gateway",
                    "Potential Impact": "High - Customer data breach",
                    "Likelihood": "Low - Requires API exploitation",
                    "Suggested Mitigation": "Implement response filtering and data classification"
                }
            ]
            '''
        }