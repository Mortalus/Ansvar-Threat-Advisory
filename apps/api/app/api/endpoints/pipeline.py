from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from app.core.pipeline.manager import PipelineManager, PipelineStatus
from app.dependencies import get_pipeline_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["pipeline"])

@router.post("/create")
async def create_pipeline(
    metadata: Optional[Dict[str, Any]] = None,
    manager: PipelineManager = Depends(get_pipeline_manager)
):
    """Create a new pipeline run"""
    try:
        # Extract parameters from metadata if provided
        if metadata:
            name = metadata.get('name')
            description = metadata.get('description')
            owner_id = metadata.get('owner_id')
        else:
            name = description = owner_id = None
            
        pipeline_id = await manager.create_pipeline(
            name=name,
            description=description, 
            owner_id=owner_id
        )
        return {
            "pipeline_id": pipeline_id,
            "status": "created",
            "message": "Pipeline created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{pipeline_id}/status")
async def get_pipeline_status(
    pipeline_id: str,
    manager: PipelineManager = Depends(get_pipeline_manager)
):
    """Get the current status of a pipeline"""
    try:
        status = await manager.get_pipeline_status(pipeline_id)
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{pipeline_id}/cancel")
async def cancel_pipeline(
    pipeline_id: str,
    manager: PipelineManager = Depends(get_pipeline_manager)
):
    """Cancel a running pipeline"""
    try:
        success = await manager.cancel_pipeline(pipeline_id)
        if not success:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        return {
            "success": True,
            "message": f"Pipeline {pipeline_id} cancelled"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_pipelines(
    status: Optional[str] = None,
    limit: int = 10,
    manager: PipelineManager = Depends(get_pipeline_manager)
):
    """List pipelines with optional filtering"""
    try:
        # Validate status if provided
        if status:
            try:
                status_enum = PipelineStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {', '.join([s.value for s in PipelineStatus])}"
                )
        else:
            status_enum = None
        
        pipelines = await manager.list_pipelines(status=status_enum, limit=limit)
        return pipelines
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list pipelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{pipeline_id}/result/{step}")
async def get_step_result(
    pipeline_id: str,
    step: str,
    manager: PipelineManager = Depends(get_pipeline_manager)
):
    """Get the result of a specific pipeline step"""
    try:
        pipeline = await manager.get_pipeline(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        if step not in pipeline["steps"]:
            raise HTTPException(status_code=400, detail=f"Invalid step: {step}")
        
        step_info = pipeline["steps"][step]
        if step_info["status"] != PipelineStatus.COMPLETED:
            return {
                "status": step_info["status"],
                "message": f"Step {step} is not completed yet"
            }
        
        return {
            "status": "completed",
            "result": step_info["result"],
            "completed_at": step_info["completed_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get step result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    manager: PipelineManager = Depends(get_pipeline_manager)
):
    """Delete a pipeline and its results"""
    try:
        pipeline = await manager.get_pipeline(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        # In production, this would delete from database
        if pipeline_id in manager.pipelines:
            del manager.pipelines[pipeline_id]
        
        return {
            "success": True,
            "message": f"Pipeline {pipeline_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))