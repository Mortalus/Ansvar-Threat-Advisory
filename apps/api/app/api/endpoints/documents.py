from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Optional
import PyPDF2
import io
import logging
from pydantic import BaseModel
from app.core.pipeline.manager import PipelineManager, PipelineStep
from app.models.dfd import DFDComponents
from app.dependencies import get_pipeline_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

class ExtractDFDRequest(BaseModel):
    pipeline_id: str
    background: bool = False  # New flag to enable background processing

async def extract_text_from_file(file: UploadFile) -> str:
    """Extract text content from uploaded file"""
    try:
        # Check file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File {file.filename} exceeds maximum size of 10MB"
            )
        
        text = ""
        
        # Handle PDF files
        if file.content_type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num + 1}: {e}")
                    continue
        
        # Handle text files
        elif file.content_type in ["text/plain", "text/markdown"]:
            text = contents.decode('utf-8', errors='ignore')
        
        # Handle DOCX files (would need python-docx library)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # For now, we'll skip DOCX support but note it in the error
            raise HTTPException(
                status_code=400,
                detail=f"DOCX support coming soon. Please convert {file.filename} to PDF or TXT"
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type} for file {file.filename}"
            )
        
        return text.strip()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process file {file.filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file {file.filename}: {str(e)}"
        )
    finally:
        # Reset file pointer for potential reuse
        await file.seek(0)

@router.post("/upload", response_model=dict)
async def upload_documents(
    files: List[UploadFile] = File(...),
    pipeline_manager: PipelineManager = Depends(get_pipeline_manager)
):
    """
    Upload one or more documents for DFD extraction.
    Supports PDF and TXT files up to 10MB each.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Extract text from all files
    combined_text = ""
    processed_files = []
    
    for file in files:
        try:
            logger.info(f"Processing file: {file.filename}")
            text = await extract_text_from_file(file)
            
            if text:
                combined_text += f"\n\n=== Document: {file.filename} ===\n{text}\n"
                processed_files.append({
                    "filename": file.filename,
                    "size": file.size if hasattr(file, 'size') else len(await file.read()),
                    "content_type": file.content_type
                })
        finally:
            await file.close()
    
    if not combined_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No text could be extracted from the uploaded documents"
        )
    
    # Log extraction success
    logger.info(f"Successfully extracted {len(combined_text)} characters from {len(processed_files)} files")
    
    # Create pipeline but don't automatically run DFD extraction
    try:
        # Create pipeline run
        pipeline_id = await pipeline_manager.create_pipeline()
        
        # Execute document upload step only
        upload_result = await pipeline_manager.execute_step(
            pipeline_id=pipeline_id,
            step=PipelineStep.DOCUMENT_UPLOAD,
            data={"document_text": combined_text}
        )
        
        return {
            "pipeline_id": pipeline_id,
            "files": processed_files,
            "text_length": len(combined_text),
            "document_upload_result": upload_result,
            "status": "uploaded"
        }
    
    except Exception as e:
        logger.error(f"Pipeline creation failed: {e}")
        # Still return the extracted text info even if pipeline fails
        return {
            "files": processed_files,
            "text_length": len(combined_text),
            "status": "text_extracted",
            "pipeline_status": "failed",
            "error": str(e)
        }

@router.post("/extract-dfd", response_model=dict)
async def extract_dfd_from_documents(
    request: ExtractDFDRequest,
    pipeline_manager: PipelineManager = Depends(get_pipeline_manager)
):
    """
    Manually trigger DFD extraction for an uploaded document pipeline.
    
    If background=True, queues the extraction as a background task and returns immediately.
    If background=False, executes synchronously and returns results.
    """
    try:
        if request.background:
            # Background execution path
            from app.tasks.pipeline_tasks import execute_pipeline_step
            
            task = execute_pipeline_step.delay(
                pipeline_id=request.pipeline_id,
                step="dfd_extraction",
                data={}
            )
            
            return {
                "pipeline_id": request.pipeline_id,
                "task_id": task.id,
                "status": "queued",
                "message": "DFD extraction queued for background processing"
            }
        
        # Synchronous execution path (existing logic)
        # Extract pipeline_id from request body
        pipeline_id = request.pipeline_id
        logger.info(f"Attempting to extract DFD for pipeline: {pipeline_id}")
        
        # Get the pipeline to check if document upload is complete
        pipeline = await pipeline_manager.get_pipeline(pipeline_id)
        logger.info(f"Pipeline found: {pipeline is not None}")
        
        if not pipeline:
            logger.warning(f"Pipeline {pipeline_id} not found in manager")
            # Log all available pipelines for debugging
            all_pipelines = await pipeline_manager.list_pipelines()
            logger.info(f"Available pipelines: {[p['id'] for p in all_pipelines]}")
            raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
        
        # Check if document upload step is complete
        if pipeline["steps"]["document_upload"]["status"] != "completed":
            raise HTTPException(
                status_code=400, 
                detail="Document upload must be completed before DFD extraction"
            )
        
        # Get the document text from the pipeline
        # Document text is now stored in the database and will be retrieved by the manager
        # We just need to pass the pipeline_id, the manager will get the text from DB
        document_text = None
        
        # Try to get document text from step results if available
        upload_step = pipeline["steps"].get("document_upload", {})
        if upload_step.get("result"):
            document_text = upload_step["result"].get("document_text")
        
        # The PipelineManager will handle getting document text from database if not provided
        
        # Execute DFD extraction step
        data = {}
        if document_text:
            data["document_text"] = document_text
        
        result = await pipeline_manager.execute_step(
            pipeline_id=pipeline_id,
            step=PipelineStep.DFD_EXTRACTION,
            data=data
        )
        
        return {
            "pipeline_id": pipeline_id,
            "dfd_components": result["dfd_components"],
            "validation": result["validation"],
            "status": "extracted"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DFD extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"DFD extraction failed: {str(e)}"
        )

class ReviewDFDRequest(BaseModel):
    pipeline_id: str
    dfd_components: DFDComponents

@router.post("/review-dfd", response_model=dict)
async def review_dfd_components(
    request: ReviewDFDRequest,
    pipeline_manager: PipelineManager = Depends(get_pipeline_manager)
):
    """
    Review and update DFD components extracted from documents.
    This step allows users to edit the extracted DFD before proceeding to threat generation.
    """
    try:
        # Extract request data
        pipeline_id = request.pipeline_id
        dfd_components = request.dfd_components
        
        # Execute DFD review step
        result = await pipeline_manager.execute_step(
            pipeline_id=pipeline_id,
            step=PipelineStep.DFD_REVIEW,
            data={"dfd_components": dfd_components.model_dump()}
        )
        
        return {
            "pipeline_id": pipeline_id,
            "dfd_components": result["dfd_components"],
            "status": "reviewed",
            "reviewed_at": result["reviewed_at"]
        }
    
    except Exception as e:
        logger.error(f"DFD review failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"DFD review failed: {str(e)}"
        )

@router.get("/sample", response_model=DFDComponents)
async def get_sample_dfd():
    """Get a sample DFD structure for testing"""
    return DFDComponents(
        project_name="Sample E-Commerce Platform",
        project_version="1.0",
        industry_context="Retail",
        external_entities=["Customer", "Admin", "Payment Gateway"],
        assets=["User Database", "Product Database", "Session Store"],
        processes=["Web Server", "API Gateway", "Auth Service"],
        trust_boundaries=["Internet", "DMZ", "Internal Network"],
        data_flows=[
            {
                "source": "Customer",
                "destination": "Web Server",
                "data_description": "HTTP requests",
                "data_classification": "Public",
                "protocol": "HTTPS",
                "authentication_mechanism": "Session Cookie"
            }
        ]
    )