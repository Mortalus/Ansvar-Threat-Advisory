"""
Modular Workflows API - Simplified Implementation

Defensive API endpoints that work with existing infrastructure.
"""

import logging
from uuid import UUID
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_async_session
from ...services.modular_workflow_service import ModularWorkflowService
from ...core.agents.registry import agent_registry

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_workflow_service(
    db: AsyncSession = Depends(get_async_session)
) -> ModularWorkflowService:
    """Get workflow service instance"""
    return ModularWorkflowService(db)

@router.get("/agents", response_model=dict)
async def list_available_agents():
    """List all available agents for workflow creation"""
    try:
        agents = agent_registry.list_all_agents()
        
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
            "total": len(agents)
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        return {"agents": [], "total": 0, "error": str(e)}

@router.post("/templates", response_model=dict)
async def create_workflow_template(
    template_data: dict,
    workflow_service: ModularWorkflowService = Depends(get_workflow_service)
):
    """Create a new workflow template"""
    try:
        template = await workflow_service.create_template(
            name=template_data["name"],
            description=template_data.get("description"),
            steps=template_data["steps"]
        )
        
        return {
            "id": str(template.id),
            "name": template.name,
            "message": "Template created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/executions", response_model=dict)
async def start_workflow_execution(
    execution_data: dict,
    background_tasks: BackgroundTasks,
    workflow_service: ModularWorkflowService = Depends(get_workflow_service)
):
    """Start workflow execution"""
    try:
        execution = await workflow_service.start_workflow(
            template_id=UUID(execution_data["template_id"]),
            client_id=execution_data.get("client_id"),
            initial_data=execution_data.get("initial_data", {})
        )
        
        if not execution:
            raise HTTPException(status_code=400, detail="Failed to start execution")
        
        return {
            "execution_id": str(execution.id),
            "status": "started",
            "message": "Workflow execution started"
        }
    except Exception as e:
        logger.error(f"Failed to start execution: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/executions/{execution_id}/status", response_model=dict)
async def get_execution_status(
    execution_id: UUID,
    workflow_service: ModularWorkflowService = Depends(get_workflow_service)
):
    """Get execution status"""
    try:
        status_info = await workflow_service.get_execution_status(execution_id)
        if not status_info:
            raise HTTPException(status_code=404, detail="Execution not found")
        return status_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))