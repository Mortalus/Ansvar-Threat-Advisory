"""
Simple Workflows API - Working Implementation

Simplified API endpoints that bypass complex database session management
to demonstrate the working modular workflow system.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks

from ...services.simple_workflow_service import simple_workflow_service
from ...core.agents.registry import agent_registry

logger = logging.getLogger(__name__)
router = APIRouter()


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
async def create_workflow_template(template_data: dict):
    """Create a new workflow template"""
    try:
        template = await simple_workflow_service.create_template(
            name=template_data["name"],
            description=template_data.get("description"),
            steps=template_data["steps"]
        )
        
        return {
            "id": template["id"],
            "name": template["name"],
            "description": template["description"],
            "step_count": len(template["steps"]),
            "created_at": template["created_at"],
            "message": "Template created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=list)
async def list_workflow_templates():
    """List all workflow templates"""
    try:
        templates = simple_workflow_service.list_templates()
        
        return [
            {
                "id": template["id"],
                "name": template["name"],
                "description": template["description"],
                "step_count": len(template["steps"]),
                "is_active": template["is_active"],
                "created_at": template["created_at"]
            }
            for template in templates
        ]
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve templates")


@router.post("/executions", response_model=dict)
async def start_workflow_execution(execution_data: dict, background_tasks: BackgroundTasks):
    """Start a new workflow execution"""
    try:
        execution = await simple_workflow_service.start_workflow(
            template_id=execution_data["template_id"],
            client_id=execution_data.get("client_id"),
            initial_data=execution_data.get("initial_data", {})
        )
        
        # Execute workflow in background
        background_tasks.add_task(
            simple_workflow_service.execute_complete_workflow,
            execution["id"]
        )
        
        return {
            "execution_id": execution["id"],
            "status": execution["status"],
            "template_id": execution["template_id"],
            "template_name": execution["template_name"],
            "client_id": execution["client_id"],
            "started_at": execution["started_at"],
            "message": "Workflow execution started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start workflow execution: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/executions", response_model=list)
async def list_workflow_executions():
    """List all workflow executions"""
    try:
        executions = simple_workflow_service.list_executions()
        
        return [
            {
                "execution_id": execution["id"],
                "template_name": execution["template_name"],
                "status": execution["status"],
                "current_step": execution["current_step"],
                "total_steps": execution["total_steps"],
                "progress_percent": execution["progress_percent"],
                "started_at": execution["started_at"],
                "completed_at": execution.get("completed_at"),
                "client_id": execution["client_id"],
                "threat_count": len(execution["threats"])
            }
            for execution in executions
        ]
    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve executions")


@router.get("/executions/{execution_id}/status", response_model=dict)
async def get_execution_status(execution_id: str):
    """Get current status of workflow execution"""
    try:
        execution = await simple_workflow_service.get_execution_status(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return {
            "execution_id": execution["id"],
            "template_name": execution["template_name"],
            "status": execution["status"],
            "current_step": execution["current_step"],
            "total_steps": execution["total_steps"],
            "progress_percent": execution["progress_percent"],
            "started_at": execution["started_at"],
            "completed_at": execution.get("completed_at"),
            "last_activity": execution.get("last_activity_at"),
            "client_id": execution["client_id"],
            "steps": execution["steps"],
            "threats": execution["threats"],
            "error": execution.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve execution status")


@router.post("/executions/{execution_id}/steps/{step_index}/execute", response_model=dict)
async def execute_workflow_step(execution_id: str, step_index: int):
    """Execute a single workflow step manually"""
    try:
        step_result = await simple_workflow_service.execute_workflow_step(execution_id, step_index)
        
        return {
            "execution_id": execution_id,
            "step_result": step_result,
            "message": f"Step {step_index} executed successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to execute step: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/demo/complete-workflow", response_model=dict)
async def demo_complete_workflow():
    """Demo endpoint to show complete workflow execution"""
    try:
        # Create a demo template
        template = await simple_workflow_service.create_template(
            name="Demo Complete Threat Analysis",
            description="Demonstration of complete modular threat modeling workflow",
            steps=[
                {
                    "name": "Document Analysis",
                    "description": "Initial document analysis using AI agents",
                    "agent_type": "document_analysis",
                    "confidence_threshold": 0.8
                },
                {
                    "name": "Architectural Risk Assessment",
                    "description": "Deep architectural security analysis",
                    "agent_type": "architectural_risk",
                    "confidence_threshold": 0.85
                },
                {
                    "name": "Business Impact Analysis",
                    "description": "Business and financial impact assessment",
                    "agent_type": "business_financial",
                    "confidence_threshold": 0.75
                }
            ]
        )
        
        # Start execution
        execution = await simple_workflow_service.start_workflow(
            template_id=template["id"],
            client_id="demo_client",
            initial_data={
                "document_content": """
                Web Application Architecture:
                - React frontend with user authentication
                - Node.js API backend with JWT tokens
                - PostgreSQL database with customer data
                - Redis for session management
                - AWS deployment with S3 file storage
                """,
                "components": [
                    "React Frontend",
                    "Node.js API",
                    "PostgreSQL Database",
                    "Redis Cache",
                    "AWS Infrastructure"
                ]
            }
        )
        
        # Execute complete workflow
        completed_execution = await simple_workflow_service.execute_complete_workflow(execution["id"])
        
        # Calculate summary stats
        total_threats = len(completed_execution["threats"])
        automated_steps = len([s for s in completed_execution["steps"] if s["automated"]])
        steps_count = len(completed_execution["steps"])
        avg_confidence = sum(s["confidence_score"] for s in completed_execution["steps"]) / steps_count if steps_count > 0 else 0.0
        
        return {
            "demo_status": "completed",
            "template": {
                "id": template["id"],
                "name": template["name"],
                "step_count": len(template["steps"])
            },
            "execution": {
                "id": completed_execution["id"],
                "status": completed_execution["status"],
                "progress_percent": completed_execution["progress_percent"],
                "total_threats": total_threats,
                "automated_steps": automated_steps,
                "manual_review_steps": steps_count - automated_steps,
                "average_confidence": round(avg_confidence, 3),
                "execution_time": completed_execution.get("completed_at", completed_execution.get("last_activity_at"))
            },
            "step_details": completed_execution["steps"],
            "threats_found": completed_execution["threats"],
            "message": f"Demo completed successfully! Found {total_threats} threats across {steps_count} steps."
        }
        
    except Exception as e:
        logger.error(f"Demo workflow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


@router.get("/status", response_model=dict)
async def get_workflow_system_status():
    """Get overall system status"""
    try:
        templates = simple_workflow_service.list_templates()
        executions = simple_workflow_service.list_executions()
        agents = agent_registry.list_all_agents()
        
        # Calculate stats
        running_executions = [e for e in executions if e["status"] == "running"]
        completed_executions = [e for e in executions if e["status"] == "completed"]
        failed_executions = [e for e in executions if e["status"] == "failed"]
        
        return {
            "system_status": "operational",
            "agents": {
                "total": len(agents),
                "categories": len(set(agent.get_metadata().category for agent in agents))
            },
            "templates": {
                "total": len(templates),
                "active": len([t for t in templates if t["is_active"]])
            },
            "executions": {
                "total": len(executions),
                "running": len(running_executions),
                "completed": len(completed_executions),
                "failed": len(failed_executions)
            },
            "message": "Modular workflow system operational"
        }
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return {
            "system_status": "error",
            "error": str(e),
            "message": "System status check failed"
        }