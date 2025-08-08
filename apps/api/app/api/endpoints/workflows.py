"""
Workflow API Endpoints

Provides REST endpoints for managing agent-based workflow templates
and executing workflows with automation and review controls.
"""

import logging
from uuid import UUID
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_async_session
from ...models.workflow_template import (
    WorkflowTemplate,
    WorkflowTemplateCreate,
    WorkflowTemplateUpdate,
    WorkflowExecutionCreate,
    WorkflowStepAction
)
from ...services.workflow_manager import WorkflowManager
from ...services.llm_service import LLMService
from ...api.v1.auth import require_permission
from ...models import User, PermissionType

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_workflow_manager(
    db: AsyncSession = Depends(get_async_session),
    llm_service: LLMService = Depends(LLMService)
) -> WorkflowManager:
    """Dependency to get workflow manager instance"""
    return WorkflowManager(db, llm_service)


# Template Management Endpoints

@router.post("/templates", response_model=dict)
async def create_workflow_template(
    template_data: WorkflowTemplateCreate,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: User = Depends(require_permission(PermissionType.PIPELINE_CREATE))
):
    """Create a new workflow template (Admin only)"""
    try:
        template = await workflow_manager.create_template(
            name=template_data.name,
            description=template_data.description,
            steps=[step.model_dump() for step in template_data.steps],
            automation_settings=template_data.automation_settings.model_dump(),
            client_access_rules=template_data.client_access_rules.model_dump(),
            created_by=current_user.id
        )
        
        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "step_count": len(template.steps),
            "created_at": template.created_at.isoformat(),
            "message": "Workflow template created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create workflow template: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/templates", response_model=List[dict])
async def list_workflow_templates(
    active_only: bool = True,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: User = Depends(require_permission(PermissionType.PIPELINE_VIEW))
):
    """List all workflow templates"""
    try:
        templates = await workflow_manager.list_templates(active_only=active_only)
        
        return [
            {
                "id": str(template.id),
                "name": template.name,
                "description": template.description,
                "version": template.version,
                "step_count": len(template.steps),
                "is_active": template.is_active,
                "is_default": template.is_default,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
            for template in templates
        ]
        
    except Exception as e:
        logger.error(f"Failed to list workflow templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )


@router.get("/templates/{template_id}", response_model=dict)
async def get_workflow_template(
    template_id: UUID,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: User = Depends(require_permission(PermissionType.PIPELINE_VIEW))
):
    """Get detailed workflow template information"""
    try:
        template = await workflow_manager.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "version": template.version,
            "steps": template.steps,
            "automation_settings": template.automation_settings,
            "client_access_rules": template.client_access_rules,
            "is_active": template.is_active,
            "is_default": template.is_default,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template"
        )


@router.put("/templates/{template_id}", response_model=dict)
async def update_workflow_template(
    template_id: UUID,
    template_data: WorkflowTemplateUpdate,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: User = Depends(require_permission(PermissionType.PIPELINE_MODIFY))
):
    """Update workflow template (Admin only)"""
    try:
        template = await workflow_manager.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Update template fields
        if template_data.name is not None:
            template.name = template_data.name
        if template_data.description is not None:
            template.description = template_data.description
        if template_data.steps is not None:
            template.steps = [step.model_dump() for step in template_data.steps]
        if template_data.automation_settings is not None:
            template.automation_settings = template_data.automation_settings.model_dump()
        if template_data.client_access_rules is not None:
            template.client_access_rules = template_data.client_access_rules.model_dump()
        if template_data.is_active is not None:
            template.is_active = template_data.is_active
        if template_data.is_default is not None:
            template.is_default = template_data.is_default
        
        await workflow_manager.db.commit()
        
        return {
            "id": str(template.id),
            "name": template.name,
            "message": "Template updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update template: {str(e)}"
        )


# Workflow Execution Endpoints

@router.post("/executions", response_model=dict)
async def start_workflow_execution(
    execution_data: WorkflowExecutionCreate,
    background_tasks: BackgroundTasks,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: User = Depends(require_permission(PermissionType.PIPELINE_EXECUTE))
):
    """Start a new workflow execution"""
    try:
        execution = await workflow_manager.start_workflow(
            template_id=UUID(execution_data.template_id),
            client_id=execution_data.client_id,
            client_email=execution_data.client_email,
            initial_data=execution_data.initial_data,
            automation_overrides=execution_data.automation_overrides
        )
        
        # Execute workflow in background
        background_tasks.add_task(
            workflow_manager.execute_workflow,
            execution.id
        )
        
        return {
            "execution_id": str(execution.id),
            "status": execution.status,
            "template_id": str(execution.template_id),
            "client_id": execution.client_id,
            "started_at": execution.started_at.isoformat(),
            "message": "Workflow execution started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start workflow execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start execution: {str(e)}"
        )


@router.get("/executions/{execution_id}/status", response_model=dict)
async def get_execution_status(
    execution_id: UUID,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: User = Depends(require_permission(PermissionType.PIPELINE_VIEW))
):
    """Get current status of workflow execution"""
    try:
        status_info = await workflow_manager.get_execution_status(execution_id)
        return status_info
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get execution status {execution_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve execution status"
        )


@router.post("/executions/{execution_id}/steps/{step_index}/action", response_model=dict)
async def perform_step_action(
    execution_id: UUID,
    step_index: int,
    action: WorkflowStepAction,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: User = Depends(require_permission(PermissionType.PIPELINE_MODIFY))
):
    """Perform action on workflow step (approve, reject, retry, skip)"""
    try:
        if action.action == "approve":
            success = await workflow_manager.approve_step(
                execution_id=execution_id,
                step_index=step_index,
                approved_by=current_user.id,
                modifications=action.data
            )
            
            if success:
                return {
                    "execution_id": str(execution_id),
                    "step_index": step_index,
                    "action": action.action,
                    "status": "approved",
                    "message": "Step approved successfully"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Step not found or cannot be approved"
                )
        
        # Add other actions (reject, retry, skip) as needed
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action {action.action} not implemented yet"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform step action: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to perform action: {str(e)}"
        )


# Agent Information Endpoints

@router.get("/agents", response_model=dict)
async def list_available_agents(
    category: Optional[str] = None,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: User = Depends(require_permission(PermissionType.PIPELINE_VIEW))
):
    """List all available agents for workflow creation"""
    try:
        if category:
            agents = workflow_manager.agent_registry.get_agents_by_category(category)
        else:
            agents = workflow_manager.agent_registry.list_all_agents()
        
        return {
            "agents": [
                {
                    "name": agent.get_metadata().name,
                    "version": agent.get_metadata().version,
                    "description": agent.get_metadata().description,
                    "category": agent.get_metadata().category,
                    "priority": agent.get_metadata().priority,
                    "requires_document": agent.get_metadata().requires_document,
                    "requires_components": agent.get_metadata().requires_components,
                    "estimated_tokens": agent.get_metadata().estimated_tokens,
                    "enabled_by_default": agent.get_metadata().enabled_by_default
                }
                for agent in agents
            ],
            "total": len(agents),
            "category": category
        }
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agents"
        )


@router.get("/agents/{agent_name}", response_model=dict)
async def get_agent_info(
    agent_name: str,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: User = Depends(require_permission(PermissionType.PIPELINE_VIEW))
):
    """Get detailed information about a specific agent"""
    try:
        agent_info = workflow_manager.agent_registry.get_agent_info(agent_name)
        if not agent_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_name} not found"
            )
        
        return agent_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent info for {agent_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent information"
        )


@router.get("/registry/stats", response_model=dict)
async def get_registry_stats(
    workflow_manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: User = Depends(require_permission(PermissionType.SYSTEM_ADMIN))
):
    """Get agent registry statistics (Admin only)"""
    try:
        stats = workflow_manager.agent_registry.get_registry_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get registry stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve registry statistics"
        )