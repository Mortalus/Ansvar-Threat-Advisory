from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Optional
import PyPDF2
import io
import logging
from app.core.pipeline.manager import PipelineManager, PipelineStep
from app.models.dfd import DFDComponents

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

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
    pipeline_manager: PipelineManager = Depends(lambda: PipelineManager())
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
    
    # Trigger DFD extraction pipeline
    try:
        # Create pipeline run
        pipeline_id = await pipeline_manager.create_pipeline()
        
        # Execute DFD extraction step
        dfd_result = await pipeline_manager.execute_step(
            pipeline_id=pipeline_id,
            step=PipelineStep.DFD_EXTRACTION,
            data={"document_text": combined_text}
        )
        
        return {
            "pipeline_id": pipeline_id,
            "files": processed_files,
            "text_length": len(combined_text),
            "dfd_components": dfd_result,
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        # Still return the extracted text info even if pipeline fails
        return {
            "files": processed_files,
            "text_length": len(combined_text),
            "status": "text_extracted",
            "pipeline_status": "failed",
            "error": str(e)
        }

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