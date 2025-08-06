from enum import Enum
from typing import Dict, Any, Optional, List
import uuid
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import get_llm_provider
from app.core.pipeline.dfd_extraction_service import extract_dfd_from_text, validate_dfd_components
from app.core.pipeline.steps.dfd_extraction_enhanced import extract_dfd_enhanced, EnhancedDFDExtractor
from app.core.pipeline.steps.threat_generator import ThreatGenerator
from app.core.pipeline.steps.threat_generator_v2 import ThreatGeneratorV2
from app.core.pipeline.steps.threat_generator_v3 import ThreatGeneratorV3
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
        Handle DFD extraction step with optional quality enhancement.
        
        Args:
            pipeline_id: Pipeline identifier
            data: May contain 'document_text', enhancement flags, and configuration
        
        Returns:
            Extracted DFD components with quality report
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
        
        # Check for enhanced extraction flags
        use_enhanced = data.get("use_enhanced_extraction", True)  # Default to enhanced
        stride_review = data.get("enable_stride_review", True)
        confidence_scoring = data.get("enable_confidence_scoring", True)
        security_validation = data.get("enable_security_validation", True)
        
        logger.info(f"Starting DFD extraction for pipeline {pipeline_id} (enhanced: {use_enhanced})")
        logger.info(f"DFD extraction data received: {data}")
        
        if use_enhanced:
            # Use enhanced extraction with STRIDE expert
            logger.info("Using enhanced DFD extraction with STRIDE expert review")
            
            dfd_components, quality_report = await extract_dfd_enhanced(
                llm_provider=self.llm_provider,
                document_text=document_text,
                enable_stride_review=stride_review,
                enable_confidence_scoring=confidence_scoring,
                enable_security_validation=security_validation
            )
            
            # Legacy validation for compatibility
            validation_result = await validate_dfd_components(dfd_components)
            
            logger.info(f"Enhanced DFD extraction complete. "
                       f"Quality score: {quality_report.get('quality_summary', {}).get('overall_quality_score', 'N/A')}")
            
            # Convert to dict for storage
            result = {
                "dfd_components": dfd_components.model_dump(),
                "validation": validation_result,
                "quality_report": quality_report,
                "extraction_method": "enhanced",
                "extracted_at": datetime.utcnow().isoformat()
            }
            
        else:
            # Use original extraction method
            logger.info("Using original DFD extraction method")
            
            dfd_components = await extract_dfd_from_text(
                llm_provider=self.llm_provider,
                document_text=document_text
            )
            
            # Validate the extraction
            validation_result = await validate_dfd_components(dfd_components)
            
            logger.info(f"Basic DFD extraction complete. Quality score: {validation_result['quality_score']}")
            
            # Convert to dict for storage
            result = {
                "dfd_components": dfd_components.model_dump(),
                "validation": validation_result,
                "extraction_method": "basic",
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
        
        # Check which generator version is requested (V3 is now default)
        use_v1 = data.get("use_v1_generator", False) or data.get("basic", False)
        use_v2 = data.get("use_v2_generator", False) or data.get("context_aware", False)
        use_v3 = data.get("use_v3_generator", True) or data.get("multi_agent", True)  # Default to True
        
        # Priority logic: explicit v1 or v2 override default v3
        if use_v1 or use_v2:
            use_v3 = False
        
        if use_v3 and not (use_v1 or use_v2):
            logger.info("Using Threat Generator V3 with multi-agent analysis")
            threat_generator = ThreatGeneratorV3()
            
            # Get original document text if available for comprehensive analysis
            document_text = pipeline.document_content if hasattr(pipeline, 'document_content') else None
            
            # Get the session from service
            session = service.session if hasattr(service, 'session') else await self._get_session()
            
            # Execute V3 threat generation with multi-agent system
            result = await threat_generator.execute(
                db_session=session,
                pipeline_step_result=None,
                component_data=dfd_components,
                document_text=document_text
            )
        elif use_v2:
            logger.info("Using Threat Generator V2 with context-aware risk scoring")
            threat_generator = ThreatGeneratorV2()
            
            # Get original document text if available for control parsing
            document_text = pipeline.document_content if hasattr(pipeline, 'document_content') else None
            
            # Get the session from service
            session = service.session if hasattr(service, 'session') else await self._get_session()
            
            # Execute V2 threat generation with context awareness
            result = await threat_generator.execute(
                db_session=session,
                pipeline_step_result=None,
                component_data=dfd_components,
                document_text=document_text
            )
        elif use_v1:
            # Use original RAG-powered threat generator (V1)
            logger.info("Using Threat Generator V1 (original RAG-powered)")
            threat_generator = ThreatGenerator()
            
            # Get the session from service
            session = service.session if hasattr(service, 'session') else await self._get_session()
            
            # Execute threat generation with RAG - the threat generator doesn't need pipeline step result
            result = await threat_generator.execute(
                db_session=session,
                pipeline_step_result=None,  # Not needed for this implementation
                component_data=dfd_components
            )
        else:
            # Fallback to V3 if no specific version requested (should not reach here due to default logic above)
            logger.info("Fallback: Using Threat Generator V3 with multi-agent analysis")
            threat_generator = ThreatGeneratorV3()
            
            document_text = pipeline.document_content if hasattr(pipeline, 'document_content') else None
            session = service.session if hasattr(service, 'session') else await self._get_session()
            
            result = await threat_generator.execute(
                db_session=session,
                pipeline_step_result=None,
                component_data=dfd_components,
                document_text=document_text
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
        """Handle AI-powered threat refinement step"""
        # Get pipeline to check if threat generation is complete
        pipeline = await service.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        # Check if threat generation step is complete
        threat_step = next((step for step in pipeline.steps if step.step_name == "threat_generation"), None)
        if not threat_step or threat_step.status != StepStatus.COMPLETED:
            raise ValueError("Threat generation must be completed before refinement")
        
        # Get threats from the threat generation step results
        threat_result = next((result for result in threat_step.results 
                            if result.result_type == "threats"), None)
        if not threat_result:
            raise ValueError("No threats found from threat generation step")
        
        threat_data = threat_result.result_data
        if not threat_data or not threat_data.get("threats"):
            raise ValueError("No threats found to refine")
        
        logger.info(f"Starting AI-powered refinement for pipeline {pipeline_id}")
        
        # Import and use the optimized AI-powered threat refiner
        from app.core.pipeline.steps.threat_refiner import ThreatRefiner
        
        threat_refiner = ThreatRefiner()
        
        # Get the session from service
        session = service.session if hasattr(service, 'session') else await self._get_session()
        
        # Execute threat refinement with AI capabilities
        result = await threat_refiner.execute(
            db_session=session,
            pipeline_step_result=None,
            threat_data=threat_data
        )
        
        # Store refined threats in pipeline database
        await service.update_pipeline_data(
            pipeline_id,
            refined_threats=result.get("refined_threats", [])
        )
        
        # Add timestamp
        result["refined_at"] = datetime.utcnow().isoformat()
        
        # Store step result
        await service.add_step_result(
            pipeline_id, "threat_refinement", "refined_threats", result
        )
        
        logger.info(f"Completed threat refinement for pipeline {pipeline_id}")
        return result
    
    async def _handle_attack_path_analysis(
        self,
        pipeline_id: str,
        data: Dict[str, Any],
        service: PipelineService
    ) -> Dict[str, Any]:
        """Handle attack path analysis step"""
        # Get pipeline to check previous steps are complete
        pipeline = await service.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        # Verify threat refinement is complete and get refined threats
        threat_refine_step = next((step for step in pipeline.steps 
                                 if step.step_name == "threat_refinement"), None)
        if not threat_refine_step or threat_refine_step.status != StepStatus.COMPLETED:
            raise ValueError("Threat refinement must be completed before attack path analysis")
        
        # Get refined threats from step results
        threat_result = next((result for result in threat_refine_step.results 
                            if result.result_type == "refined_threats"), None)
        if not threat_result:
            raise ValueError("No refined threats found from threat refinement step")
        
        refined_threats = threat_result.result_data.get("refined_threats", [])
        if not refined_threats:
            raise ValueError("No refined threats data available for analysis")
        
        # Get DFD components from pipeline
        dfd_components = pipeline.dfd_components
        if not dfd_components:
            raise ValueError("DFD components not found. Run DFD extraction first.")
        
        logger.info(f"Starting attack path analysis for pipeline {pipeline_id}")
        logger.info(f"Analyzing {len(refined_threats)} refined threats")
        
        # Import and use the attack path analyzer
        from app.core.pipeline.steps.attack_path_analyzer import AttackPathAnalyzer
        
        # Configure analyzer based on data parameters
        max_path_length = data.get("max_path_length", 5)
        max_paths_to_analyze = data.get("max_paths_to_analyze", 20)
        
        analyzer = AttackPathAnalyzer(
            max_path_length=max_path_length,
            max_paths_to_analyze=max_paths_to_analyze
        )
        
        # Get the session from service
        session = service.session if hasattr(service, 'session') else await self._get_session()
        
        # Execute attack path analysis
        result = await analyzer.execute(
            db_session=session,
            pipeline_step_result=None,
            refined_threats=refined_threats,
            dfd_components=dfd_components
        )
        
        # Store attack paths in pipeline database
        await service.update_pipeline_data(
            pipeline_id,
            attack_paths=result.get("attack_paths", [])
        )
        
        # Add timestamp
        result["analyzed_at"] = datetime.utcnow().isoformat()
        
        # Store step result
        await service.add_step_result(
            pipeline_id, "attack_path_analysis", "attack_paths", result
        )
        
        logger.info(f"Attack path analysis complete for pipeline {pipeline_id}")
        logger.info(f"Found {len(result.get('attack_paths', []))} attack paths, "
                   f"{len(result.get('critical_scenarios', []))} critical scenarios")
        
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