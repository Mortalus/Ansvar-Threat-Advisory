from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Optional
import PyPDF2
import io
import logging
from pydantic import BaseModel
from app.core.pipeline.manager import PipelineManager, PipelineStep
from app.models.dfd import DFDComponents
from app.dependencies import get_pipeline_manager
from app.utils.token_counter import TokenCounter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

class ExtractDFDRequest(BaseModel):
    pipeline_id: str
    background: bool = False  # Flag to enable background processing
    use_enhanced_extraction: bool = True  # Enable enhanced extraction with STRIDE expert (recommended)
    enable_stride_review: bool = True  # Enable STRIDE expert review
    enable_confidence_scoring: bool = True  # Enable confidence scoring
    enable_security_validation: bool = True  # Enable security validation checklist

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
    
    # Calculate token estimates for the extracted text
    estimated_tokens = TokenCounter.estimate_tokens(combined_text)
    token_cost_estimate = TokenCounter.estimate_cost(
        input_tokens=estimated_tokens,
        output_tokens=estimated_tokens // 4,  # Estimate output tokens as 1/4 of input
        model="llama-3.3-70b-instruct"  # Default model for estimation
    )
    
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
            "token_estimate": {
                "estimated_tokens": estimated_tokens,
                "model_basis": token_cost_estimate["model"],
                "discrete_summary": f"🪙 {estimated_tokens:,} tokens"
            },
            "status": "uploaded"
        }
    
    except Exception as e:
        logger.error(f"Pipeline creation failed: {e}")
        # Still return the extracted text info even if pipeline fails
        return {
            "files": processed_files,
            "text_length": len(combined_text),
            "token_estimate": {
                "estimated_tokens": estimated_tokens,
                "model_basis": token_cost_estimate["model"],
                "discrete_summary": f"🪙 {estimated_tokens:,} tokens"
            },
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
        logger.info(f"DFD extraction request: use_enhanced={request.use_enhanced_extraction}, "
                   f"stride_review={request.enable_stride_review}, "
                   f"confidence_scoring={request.enable_confidence_scoring}, "
                   f"security_validation={request.enable_security_validation}")
        
        if request.background:
            # Background execution path
            from app.tasks.pipeline_tasks import execute_pipeline_step
            
            task = execute_pipeline_step.delay(
                pipeline_id=request.pipeline_id,
                step="dfd_extraction",
                data={
                    "use_enhanced_extraction": request.use_enhanced_extraction,
                    "enable_stride_review": request.enable_stride_review,
                    "enable_confidence_scoring": request.enable_confidence_scoring,
                    "enable_security_validation": request.enable_security_validation
                }
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
        
        # Execute DFD extraction step with enhancement options
        data = {
            "use_enhanced_extraction": request.use_enhanced_extraction,
            "enable_stride_review": request.enable_stride_review,
            "enable_confidence_scoring": request.enable_confidence_scoring,
            "enable_security_validation": request.enable_security_validation
        }
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

class GenerateThreatsRequest(BaseModel):
    pipeline_id: str
    # V3 is the only threat generator available (multi-agent analysis with context-aware risk scoring)

class RefineThreatRequest(BaseModel):
    pipeline_id: str

class AttackPathAnalysisRequest(BaseModel):
    pipeline_id: str
    max_path_length: int = 5
    max_paths_to_analyze: int = 20

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

@router.post("/generate-threats", response_model=dict)
async def generate_threats(
    request: GenerateThreatsRequest,
    pipeline_manager: PipelineManager = Depends(get_pipeline_manager)
):
    """
    Generate threats based on reviewed DFD components.
    Uses RAG-powered AI to identify potential security threats.
    """
    try:
        pipeline_id = request.pipeline_id
        
        # Verify that DFD review is complete
        pipeline = await pipeline_manager.get_pipeline(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
        
        if pipeline["steps"]["dfd_review"]["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail="DFD review must be completed before threat generation"
            )
        
        # Execute threat generation step with version flags
        result = await pipeline_manager.execute_step(
            pipeline_id=pipeline_id,
            step=PipelineStep.THREAT_GENERATION,
            data={
                "use_v2_generator": request.use_v2_generator,
                "context_aware": request.context_aware,
                "use_v3_generator": request.use_v3_generator,
                "multi_agent": request.multi_agent
            }
        )
        
        return {
            "pipeline_id": pipeline_id,
            "threats": result["threats"],
            "total_count": result["total_count"],
            "components_analyzed": result["components_analyzed"],
            "knowledge_sources_used": result["knowledge_sources_used"],
            "generated_at": result.get("generated_at"),
            "status": "generated"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Threat generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Threat generation failed: {str(e)}"
        )

@router.post("/refine-threats", response_model=dict)
async def refine_threats(
    request: RefineThreatRequest,
    pipeline_manager: PipelineManager = Depends(get_pipeline_manager)
):
    """
    Refine generated threats using AI-powered analysis.
    Enhances threats with business context, risk assessment, and prioritization.
    """
    try:
        pipeline_id = request.pipeline_id
        
        # Verify that threat generation is complete
        pipeline = await pipeline_manager.get_pipeline(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
        
        threat_gen_step = pipeline["steps"].get("threat_generation", {})
        if threat_gen_step.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail="Threat generation must be completed before refinement"
            )
        
        # Execute threat refinement step
        result = await pipeline_manager.execute_step(
            pipeline_id=pipeline_id,
            step=PipelineStep.THREAT_REFINEMENT,
            data={}
        )
        
        return {
            "pipeline_id": pipeline_id,
            "refined_threats": result["refined_threats"],
            "total_count": result["total_count"],
            "refinement_stats": result["refinement_stats"],
            "refined_at": result.get("refined_at"),
            "status": "refined"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Threat refinement failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Threat refinement failed: {str(e)}"
        )

@router.post("/analyze-attack-paths", response_model=dict)
async def analyze_attack_paths(
    request: AttackPathAnalysisRequest,
    pipeline_manager: PipelineManager = Depends(get_pipeline_manager)
):
    """
    Analyze attack paths based on refined threats and DFD components.
    Identifies potential attack chains and provides defensive recommendations.
    """
    try:
        pipeline_id = request.pipeline_id
        
        # Verify that threat refinement is complete
        pipeline = await pipeline_manager.get_pipeline(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
        
        threat_refine_step = pipeline["steps"].get("threat_refinement", {})
        if threat_refine_step.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail="Threat refinement must be completed before attack path analysis"
            )
        
        # Execute attack path analysis step
        result = await pipeline_manager.execute_step(
            pipeline_id=pipeline_id,
            step=PipelineStep.ATTACK_PATH_ANALYSIS,
            data={
                "max_path_length": request.max_path_length,
                "max_paths_to_analyze": request.max_paths_to_analyze
            }
        )
        
        return {
            "pipeline_id": pipeline_id,
            "attack_paths": result["attack_paths"],
            "critical_scenarios": result["critical_scenarios"],
            "defense_priorities": result["defense_priorities"],
            "threat_coverage": result["threat_coverage"],
            "metadata": result["metadata"],
            "analyzed_at": result.get("analyzed_at"),
            "status": "analyzed"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Attack path analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Attack path analysis failed: {str(e)}"
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