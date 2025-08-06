"""Task management endpoints for background job processing"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging
from datetime import datetime

from app.tasks.pipeline_tasks import execute_pipeline_step, execute_full_pipeline
from app.tasks.llm_tasks import extract_dfd_task, generate_threats_task
from app.celery_app import celery_app
from app.dependencies import get_pipeline_manager
from app.core.pipeline.manager import PipelineManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskResponse(BaseModel):
    task_id: str
    pipeline_id: str
    status: str
    message: str
    submitted_at: str


class BackgroundStepRequest(BaseModel):
    pipeline_id: str
    step: str
    data: Optional[Dict[str, Any]] = {}


class BackgroundPipelineRequest(BaseModel):
    pipeline_id: str
    start_step: Optional[str] = "document_upload"


@router.post("/execute-step", response_model=TaskResponse)
async def execute_step_background(
    request: BackgroundStepRequest,
    pipeline_manager: PipelineManager = Depends(get_pipeline_manager)
):
    """
    Execute a single pipeline step in the background
    
    This endpoint queues a pipeline step for background execution and returns
    immediately with a task ID for monitoring progress.
    """
    try:
        # Validate pipeline exists
        pipeline = await pipeline_manager.get_pipeline(request.pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail=f"Pipeline {request.pipeline_id} not found")
        
        # Submit background task
        task = execute_pipeline_step.delay(
            pipeline_id=request.pipeline_id,
            step=request.step,
            data=request.data
        )
        
        logger.info(f"Queued step {request.step} for pipeline {request.pipeline_id}, task_id: {task.id}")
        
        return TaskResponse(
            task_id=task.id,
            pipeline_id=request.pipeline_id,
            status="queued",
            message=f"Step {request.step} queued for background execution",
            submitted_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue step execution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")


@router.post("/execute-pipeline", response_model=TaskResponse)
async def execute_pipeline_background(
    request: BackgroundPipelineRequest,
    pipeline_manager: PipelineManager = Depends(get_pipeline_manager)
):
    """
    Execute multiple pipeline steps in sequence in the background
    
    This is useful for running a complete threat modeling analysis without
    manual intervention between steps.
    """
    try:
        # Validate pipeline exists
        pipeline = await pipeline_manager.get_pipeline(request.pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail=f"Pipeline {request.pipeline_id} not found")
        
        # Submit background task for full pipeline
        task = execute_full_pipeline.delay(
            pipeline_id=request.pipeline_id,
            start_step=request.start_step
        )
        
        logger.info(f"Queued full pipeline execution for {request.pipeline_id}, task_id: {task.id}")
        
        return TaskResponse(
            task_id=task.id,
            pipeline_id=request.pipeline_id,
            status="queued",
            message=f"Full pipeline execution queued starting from {request.start_step}",
            submitted_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue pipeline execution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the current status of a background task
    
    Returns detailed information about task progress, results, or errors.
    """
    try:
        # Get task result from Celery
        result = celery_app.AsyncResult(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        response = {
            "task_id": task_id,
            "status": result.status,
            "current": result.result if result.status != 'FAILURE' else None,
            "error": str(result.result) if result.status == 'FAILURE' else None
        }
        
        # Add progress information if available
        if result.status == 'PROGRESS' and isinstance(result.result, dict):
            response["progress"] = result.result
        elif result.status == 'SUCCESS' and isinstance(result.result, dict):
            response["result"] = result.result
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a running background task
    
    Note: Tasks that are already executing may not be immediately canceled.
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        logger.info(f"Canceled task {task_id}")
        
        return {
            "task_id": task_id,
            "status": "canceled",
            "message": "Task cancellation requested",
            "canceled_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.get("/list")
async def list_active_tasks():
    """
    List all active tasks
    
    Returns information about currently running and queued tasks.
    """
    try:
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled() 
        reserved_tasks = inspect.reserved()
        
        return {
            "active": active_tasks or {},
            "scheduled": scheduled_tasks or {},
            "reserved": reserved_tasks or {},
            "queried_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/stats")
async def get_task_stats():
    """
    Get Celery task statistics and worker information
    """
    try:
        inspect = celery_app.control.inspect()
        
        stats = inspect.stats()
        registered_tasks = inspect.registered()
        
        return {
            "worker_stats": stats or {},
            "registered_tasks": registered_tasks or {},
            "queried_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task stats: {str(e)}")


@router.post("/health")
async def health_check():
    """
    Check if Celery workers are running and responsive
    """
    try:
        # Test with a simple health check task
        from app.celery_app import health_check
        
        task = health_check.delay()
        result = task.get(timeout=10)  # 10 second timeout
        
        return {
            "status": "healthy",
            "message": "Celery workers are responsive",
            "worker_response": result,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy", 
            "message": f"Celery workers not responding: {str(e)}",
            "checked_at": datetime.utcnow().isoformat()
        }