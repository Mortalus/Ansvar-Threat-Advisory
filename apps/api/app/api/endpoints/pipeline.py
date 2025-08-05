# apps/api/app/api/endpoints/pipeline.py

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from app.core.pipeline.manager import PipelineManager, PipelineStep
from app.config import get_settings
from app.dependencies import get_pipeline_manager

router = APIRouter()
logger = logging.getLogger(__name__)

class PipelineCreateRequest(BaseModel):
    name: str

class PipelineStepRequest(BaseModel):
    step: str
    input_data: Optional[Dict[str, Any]] = {}

class DocumentUploadRequest(BaseModel):
    filename: str
    content: str
    type: str = "text/plain"

@router.post("/pipelines", response_model=Dict[str, Any])
async def create_pipeline(
    request: PipelineCreateRequest,
    manager: PipelineManager = Depends(get_pipeline_manager)
):
    """Create a new pipeline instance"""
    try:
        pipeline_id = manager.create_pipeline(request.name)
        logger.info(f"Created pipeline: {pipeline_id}")
        return {
            "pipeline_id": pipeline_id,
            "status": "created",
            "name": request.name
        }
    except Exception as e:
        logger.error(f"Failed to create pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pipelines", response_model=List[Dict[str, Any]])
async def list_pipelines(manager: PipelineManager = Depends(get_pipeline_manager)):
    """List all pipelines"""
    return manager.list_pipelines()

@router.get("/pipelines/{pipeline_id}", response_model=Dict[str, Any])
async def get_pipeline_status(
    pipeline_id: str,
    manager: PipelineManager = Depends(get_pipeline_manager)
):
    """Get the status of a specific pipeline"""
    pipeline = manager.get_pipeline_status(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline

@router.post("/pipelines/{pipeline_id}/steps/{step}", response_model=Dict[str, Any])
async def execute_pipeline_step(
    pipeline_id: str,
    step: str,
    request: Optional[PipelineStepRequest] = None,
    manager: PipelineManager = Depends(get_pipeline_manager)
):
    """Execute a specific pipeline step"""
    try:
        # Validate step
        try:
            pipeline_step = PipelineStep(step)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid step: {step}")
        
        # Execute the step
        input_data = request.input_data if request else {}
        result = await manager.execute_step(pipeline_id, pipeline_step, input_data)
        
        return {
            "pipeline_id": pipeline_id,
            "step": step,
            "status": "completed",
            "result": result
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Step execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Step execution failed: {str(e)}")

@router.post("/pipelines/{pipeline_id}/upload", response_model=Dict[str, Any])
async def upload_document(
    pipeline_id: str,
    request: DocumentUploadRequest,
    manager: PipelineManager = Depends(get_pipeline_manager)
):
    """Upload a document to start the pipeline"""
    try:
        # Execute document upload step
        result = await manager.execute_step(
            pipeline_id,
            PipelineStep.DOCUMENT_UPLOAD,
            request.model_dump()
        )
        
        return {
            "pipeline_id": pipeline_id,
            "step": "document_upload",
            "status": "completed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

@router.post("/pipelines/{pipeline_id}/run", response_model=Dict[str, Any])
async def run_full_pipeline(
    pipeline_id: str,
    request: DocumentUploadRequest,
    manager: PipelineManager = Depends(get_pipeline_manager)
):
    """Run the complete pipeline from start to finish"""
    try:
        results = await manager.run_full_pipeline(pipeline_id, request.model_dump())
        return {
            "pipeline_id": pipeline_id,
            "status": "completed",
            "results": results
        }
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")