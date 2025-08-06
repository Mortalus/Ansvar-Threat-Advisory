from enum import Enum
from typing import Dict, Any, Optional, List
import uuid
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import get_llm_provider
from app.core.pipeline.dfd_extraction_service import extract_dfd_from_text, validate_dfd_components
from app.core.pipeline.steps.threat_generator import ThreatGenerator
from app.models.dfd import DFDComponents
from app.models import Pipeline, PipelineStep as PipelineStepModel, PipelineStatus, StepStatus
from app.services import PipelineService
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

class PipelineStep(str, Enum):
    """Pipeline step identifiers"""
    DOCUMENT_UPLOAD = "document_upload"
    DFD_EXTRACTION = "dfd_extraction"
    DFD_REVIEW = "dfd_review"
    THREAT_GENERATION = "threat_generation"
    THREAT_REFINEMENT = "threat_refinement"
    ATTACK_PATH_ANALYSIS = "attack_path_analysis"

class PipelineManager:
    """
    Manages the threat modeling pipeline execution.
    Coordinates between different steps and maintains state in the database.
    """
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self._own_session = session is None  # Track if we need to manage our own session
        self.llm_provider = None
    
    async def _get_session(self) -> AsyncSession:
        """Get database session"""
        if self.session:
            return self.session
        else:
            return AsyncSessionLocal()
    
    async def _get_service(self, session: Optional[AsyncSession] = None) -> PipelineService:
        """Get pipeline service with session"""
        if session:
            return PipelineService(session)
        else:
            session = await self._get_session()
            return PipelineService(session)
    
    async def create_pipeline(
        self, 
        name: Optional[str] = None,
        description: Optional[str] = None,
        owner_id: Optional[int] = None
    ) -> str:
        """
        Create a new pipeline run.
        
        Args:
            name: Optional name for the pipeline
            description: Optional description
            owner_id: Optional owner user ID
        
        Returns:
            Pipeline ID
        """
        session = await self._get_session()
        service = PipelineService(session)
        
        try:
            pipeline = await service.create_pipeline(
                name=name,
                description=description,
                owner_id=owner_id
            )
            
            logger.info(f"Created pipeline: {pipeline.pipeline_id}")
            return pipeline.pipeline_id
            
        finally:
            if self._own_session:
                await session.close()
    
    async def get_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline information by ID"""
        session = await self._get_session()
        service = PipelineService(session)
        
        try:
            pipeline = await service.get_pipeline(pipeline_id)
            if not pipeline:
                return None
            
            # Convert database model to the expected dictionary format
            return await self._format_pipeline_response(pipeline)
            
        finally:
            if self._own_session:
                await session.close()
    
    async def _format_pipeline_response(self, pipeline: Pipeline) -> Dict[str, Any]:
        """Convert database pipeline model to API response format"""
        steps_dict = {}
        
        for step in pipeline.steps:
            steps_dict[step.step_name] = {
                "status": step.status.value,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                "error": step.error_message,
                "result": None  # Will be populated from step results
            }
            
            # Add results data
            for result in step.results:
                if result.result_type in ["dfd_components", "validation", "threats", "attack_paths"]:
                    steps_dict[step.step_name]["result"] = result.result_data
        
        return {
            "id": pipeline.pipeline_id,
            "status": pipeline.status.value,
            "current_step": self._get_current_step_name(pipeline),
            "created_at": pipeline.created_at.isoformat(),
            "updated_at": pipeline.updated_at.isoformat(),
            "started_at": pipeline.started_at.isoformat() if pipeline.started_at else None,
            "completed_at": pipeline.completed_at.isoformat() if pipeline.completed_at else None,
            "steps": steps_dict,
            "metadata": {
                "name": pipeline.name,
                "description": pipeline.description,
                "document_files": pipeline.document_files or [],
                "text_length": pipeline.text_length
            }
        }
    
    def _get_current_step_name(self, pipeline: Pipeline) -> Optional[str]:
        """Determine current step based on step statuses"""
        for step in sorted(pipeline.steps, key=lambda s: s.step_number):
            if step.status in [StepStatus.PENDING, StepStatus.IN_PROGRESS]:
                return step.step_name
        return None
    
    async def update_pipeline_status(
        self,
        pipeline_id: str,
        status: PipelineStatus,
        current_step: Optional[PipelineStep] = None
    ):
        """Update the overall pipeline status"""
        session = await self._get_session()
        service = PipelineService(session)
        
        try:
            await service.update_pipeline_status(pipeline_id, status)
        finally:
            if self._own_session:
                await session.close()
    
    async def execute_step(
        self,
        pipeline_id: str,
        step: PipelineStep,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific pipeline step.
        
        Args:
            pipeline_id: The pipeline identifier
            step: The step to execute
            data: Input data for the step
        
        Returns:
            Result of the step execution
        """
        session = await self._get_session()
        service = PipelineService(session)
        
        try:
            # Verify pipeline exists
            pipeline = await service.get_pipeline(pipeline_id)
            if not pipeline:
                raise ValueError(f"Pipeline {pipeline_id} not found")
            
            # Update step status to in_progress
            await service.update_step_status(
                pipeline_id, step.value, StepStatus.IN_PROGRESS
            )
            
            # Update pipeline status
            await service.update_pipeline_status(pipeline_id, PipelineStatus.IN_PROGRESS)
            
            try:
                # Execute the appropriate step
                if step == PipelineStep.DOCUMENT_UPLOAD:
                    result = await self._handle_document_upload(pipeline_id, data, service)
                
                elif step == PipelineStep.DFD_EXTRACTION:
                    result = await self._handle_dfd_extraction(pipeline_id, data, service)
                
                elif step == PipelineStep.DFD_REVIEW:
                    result = await self._handle_dfd_review(pipeline_id, data, service)
                
                elif step == PipelineStep.THREAT_GENERATION:
                    result = await self._handle_threat_generation(pipeline_id, data, service)
                
                elif step == PipelineStep.THREAT_REFINEMENT:
                    result = await self._handle_threat_refinement(pipeline_id, data, service)
                
                elif step == PipelineStep.ATTACK_PATH_ANALYSIS:
                    result = await self._handle_attack_path_analysis(pipeline_id, data, service)
                
                else:
                    raise ValueError(f"Unknown step: {step}")
                
                # Update step with success
                await service.update_step_status(
                    pipeline_id, step.value, StepStatus.COMPLETED
                )
                
                logger.info(f"Pipeline {pipeline_id}: Step {step} completed successfully")
                return result
                
            except Exception as e:
                # Update step with failure
                await service.update_step_status(
                    pipeline_id, step.value, StepStatus.FAILED, str(e)
                )
                
                # Update pipeline status
                await service.update_pipeline_status(pipeline_id, PipelineStatus.FAILED)
                
                logger.error(f"Pipeline {pipeline_id}: Step {step} failed: {e}")
                raise
            
        finally:
            if self._own_session:
                await session.close()
    
    async def _handle_document_upload(
        self,
        pipeline_id: str,
        data: Dict[str, Any],
        service: PipelineService
    ) -> Dict[str, Any]:
        """Handle document upload step"""
        # This step is mostly handled by the endpoint
        # Just validate and store the document text
        document_text = data.get("document_text", "")
        document_files = data.get("files", [])
        
        if not document_text:
            raise ValueError("No document text provided")
        
        # Store document data in pipeline
        await service.update_pipeline_data(
            pipeline_id,
            document_text=document_text,
            text_length=len(document_text),
            document_files=document_files
        )
        
        # Store result
        result = {
            "document_text": document_text,
            "text_length": len(document_text),
            "files": document_files,
            "status": "uploaded"
        }
        
        await service.add_step_result(
            pipeline_id, "document_upload", "upload_info", result
        )
        
        return result
    
    async def _handle_dfd_extraction(
        self,
        pipeline_id: str,
        data: Dict[str, Any],
        service: PipelineService
    ) -> Dict[str, Any]:
        """
        Handle DFD extraction step using LLM.
        
        Args:
            pipeline_id: Pipeline identifier
            data: Must contain 'document_text' key
        
        Returns:
            Extracted DFD components
        """
        # Get document text from data or from pipeline database
        document_text = data.get("document_text")
        
        if not document_text:
            # Get document text from database
            pipeline = await service.get_pipeline(pipeline_id)
            if not pipeline or not pipeline.document_text:
                raise ValueError("Document text is required for DFD extraction")
            document_text = pipeline.document_text
        
        # Get LLM provider
        if not self.llm_provider:
            self.llm_provider = await get_llm_provider(step="dfd_extraction")
        
        logger.info(f"Starting DFD extraction for pipeline {pipeline_id}")
        
        # Extract DFD components
        dfd_components = await extract_dfd_from_text(
            llm_provider=self.llm_provider,
            document_text=document_text
        )
        
        # Validate the extraction
        validation_result = await validate_dfd_components(dfd_components)
        
        logger.info(f"DFD extraction complete. Quality score: {validation_result['quality_score']}")
        
        # Convert to dict for storage
        result = {
            "dfd_components": dfd_components.model_dump(),
            "validation": validation_result,
            "extracted_at": datetime.utcnow().isoformat()
        }
        
        # Store DFD components in pipeline database
        await service.update_pipeline_data(
            pipeline_id,
            dfd_components=dfd_components.model_dump(),
            dfd_validation=validation_result
        )
        
        # Store step result
        await service.add_step_result(
            pipeline_id, "dfd_extraction", "dfd_components", result
        )
        
        return result
    
    async def _handle_dfd_review(
        self,
        pipeline_id: str,
        data: Dict[str, Any],
        service: PipelineService
    ) -> Dict[str, Any]:
        """
        Handle DFD review step - allows user to review and edit extracted DFD components.
        
        Args:
            pipeline_id: Pipeline identifier
            data: Must contain 'dfd_components' key with updated DFD data
        
        Returns:
            Updated DFD components
        """
        # Get current DFD components from database
        pipeline = await service.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        current_dfd = pipeline.dfd_components
        if not current_dfd:
            raise ValueError("DFD components not found. Run DFD extraction first.")
        
        # Get updated DFD components from request data
        updated_dfd_data = data.get("dfd_components")
        if not updated_dfd_data:
            raise ValueError("No updated DFD components provided")
        
        # Validate the updated DFD components
        try:
            updated_dfd = DFDComponents(**updated_dfd_data)
        except Exception as e:
            raise ValueError(f"Invalid DFD components format: {e}")
        
        # Store the updated DFD components in database
        await service.update_pipeline_data(
            pipeline_id,
            dfd_components=updated_dfd.model_dump()
        )
        
        result = {
            "dfd_components": updated_dfd.model_dump(),
            "reviewed_at": datetime.utcnow().isoformat(),
            "status": "reviewed"
        }
        
        # Store step result
        await service.add_step_result(
            pipeline_id, "dfd_review", "dfd_review", result
        )
        
        logger.info(f"DFD review completed for pipeline {pipeline_id}")
        
        return result
    
    async def _handle_threat_generation(
        self,
        pipeline_id: str,
        data: Dict[str, Any],
        service: PipelineService
    ) -> Dict[str, Any]:
        """Handle threat generation step"""
        # Get DFD components from database
        pipeline = await service.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        dfd_components = pipeline.dfd_components
        if not dfd_components:
            raise ValueError("DFD components not found. Run DFD extraction first.")
        
        # Use RAG-powered threat generator
        threat_generator = ThreatGenerator()
        
        # Get the session from service
        session = service.session if hasattr(service, 'session') else await self._get_session()
        
        # Execute threat generation with RAG - the threat generator doesn't need pipeline step result
        result = await threat_generator.execute(
            db_session=session,
            pipeline_step_result=None,  # Not needed for this implementation
            component_data=dfd_components
        )
        
        # Store threats in pipeline database
        await service.update_pipeline_data(
            pipeline_id,
            threats=result.get("threats", [])
        )
        
        # Add timestamp
        result["generated_at"] = datetime.utcnow().isoformat()
        
        # Store step result
        await service.add_step_result(
            pipeline_id, "threat_generation", "threats", result
        )
        
        return result
    
    async def _handle_threat_refinement(
        self,
        pipeline_id: str,
        data: Dict[str, Any],
        service: PipelineService
    ) -> Dict[str, Any]:
        """Handle threat refinement step"""
        # TODO: Implement threat refinement logic
        result = {
            "refined_threats": [],
            "status": "pending_implementation",
            "refined_at": datetime.utcnow().isoformat()
        }
        
        # Store refined threats in pipeline database (when implemented)
        await service.update_pipeline_data(
            pipeline_id,
            refined_threats=result["refined_threats"]
        )
        
        # Store step result
        await service.add_step_result(
            pipeline_id, "threat_refinement", "refined_threats", result
        )
        
        return result
    
    async def _handle_attack_path_analysis(
        self,
        pipeline_id: str,
        data: Dict[str, Any],
        service: PipelineService
    ) -> Dict[str, Any]:
        """Handle attack path analysis step"""
        # TODO: Implement attack path analysis logic
        result = {
            "attack_paths": [],
            "status": "pending_implementation",
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        # Store attack paths in pipeline database (when implemented)
        await service.update_pipeline_data(
            pipeline_id,
            attack_paths=result["attack_paths"]
        )
        
        # Store step result
        await service.add_step_result(
            pipeline_id, "attack_path_analysis", "attack_paths", result
        )
        
        return result
    
    async def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Get the current status of a pipeline.
        
        Returns:
            Dictionary with pipeline status and step information
        """
        # This method is now redundant since we have get_pipeline that returns formatted data
        # Delegate to get_pipeline for consistency
        return await self.get_pipeline(pipeline_id)
    
    async def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancel a running pipeline"""
        session = await self._get_session()
        service = PipelineService(session)
        
        try:
            pipeline = await service.get_pipeline(pipeline_id)
            if pipeline:
                await service.update_pipeline_status(pipeline_id, PipelineStatus.CANCELLED)
                logger.info(f"Pipeline {pipeline_id} cancelled")
                return True
            return False
        finally:
            if self._own_session:
                await session.close()
    
    async def list_pipelines(
        self,
        status: Optional[PipelineStatus] = None,
        limit: int = 10,
        owner_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List pipelines with optional filtering.
        
        Args:
            status: Filter by status
            limit: Maximum number of results
            owner_id: Filter by owner
        
        Returns:
            List of pipeline summaries
        """
        session = await self._get_session()
        service = PipelineService(session)
        
        try:
            # Get pipelines from database
            db_pipelines = await service.list_pipelines(owner_id=owner_id, limit=limit * 2)  # Get extra for filtering
            
            pipelines = []
            for pipeline in db_pipelines:
                # Apply status filter if specified
                if status and pipeline.status != status:
                    continue
                    
                pipelines.append({
                    "id": pipeline.pipeline_id,
                    "status": pipeline.status.value,
                    "current_step": self._get_current_step_name(pipeline),
                    "created_at": pipeline.created_at.isoformat(),
                    "updated_at": pipeline.updated_at.isoformat(),
                    "name": pipeline.name,
                    "description": pipeline.description
                })
                
                # Stop when we have enough results
                if len(pipelines) >= limit:
                    break
            
            return pipelines
            
        finally:
            if self._own_session:
                await session.close()