from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.core.pipeline.manager import PipelineManager, PipelineStep

router = APIRouter()
pipeline_manager = PipelineManager()

class PipelineCreateRequest(BaseModel):
    name: Optional[str] = None

class StepExecuteRequest(BaseModel):
    input_data: Optional[Dict[str, Any]] = None

@router.post("/create")
async def create_pipeline(request: PipelineCreateRequest):
    """Create a new pipeline instance"""
    pipeline_id = pipeline_manager.create_pipeline()
    return {
        "pipeline_id": pipeline_id,
        "status": "created",
        "message": "Pipeline created successfully"
    }

@router.get("/{pipeline_id}/status")
async def get_pipeline_status(pipeline_id: str):
    """Get pipeline status"""
    status = pipeline_manager.get_pipeline_status(pipeline_id)
    if not status:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return status

@router.post("/{pipeline_id}/step/{step_name}")
async def execute_step(
    pipeline_id: str, 
    step_name: str, 
    request: StepExecuteRequest,
    background_tasks: BackgroundTasks
):
    """Execute a specific pipeline step"""
    try:
        step = PipelineStep(step_name)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid step: {step_name}")
    
    # Validate step is ready
    is_valid = await pipeline_manager.validate_step_input(pipeline_id, step)
    if not is_valid:
        raise HTTPException(
            status_code=400, 
            detail="Step prerequisites not met. Ensure previous steps are completed."
        )
    
    # Execute step
    try:
        result = await pipeline_manager.execute_step(
            pipeline_id, 
            step, 
            request.input_data
        )
        return {
            "status": "completed",
            "step": step_name,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{pipeline_id}/validate/{step_name}")
async def validate_step(pipeline_id: str, step_name: str):
    """Validate if a step is ready to execute"""
    try:
        step = PipelineStep(step_name)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid step: {step_name}")
    
    is_valid = await pipeline_manager.validate_step_input(pipeline_id, step)
    return {
        "step": step_name,
        "is_valid": is_valid,
        "message": "Step is ready" if is_valid else "Prerequisites not met"
    }