from enum import Enum
from typing import Dict, Any, Optional, List
import uuid
import logging
from datetime import datetime
from app.core.llm import get_llm_provider
from app.core.pipeline.dfd_extraction_service import extract_dfd_from_text, validate_dfd_components
from app.models.dfd import DFDComponents

logger = logging.getLogger(__name__)

class PipelineStep(str, Enum):
    """Pipeline step identifiers"""
    DOCUMENT_UPLOAD = "document_upload"
    DFD_EXTRACTION = "dfd_extraction"
    THREAT_GENERATION = "threat_generation"
    THREAT_REFINEMENT = "threat_refinement"
    ATTACK_PATH_ANALYSIS = "attack_path_analysis"

class PipelineStatus(str, Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PipelineManager:
    """
    Manages the threat modeling pipeline execution.
    Coordinates between different steps and maintains state.
    """
    
    def __init__(self):
        # In-memory storage for pipeline runs (replace with database in production)
        self.pipelines: Dict[str, Dict[str, Any]] = {}
        self.llm_provider = None
    
    async def create_pipeline(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new pipeline run.
        
        Args:
            metadata: Optional metadata for the pipeline run
        
        Returns:
            Pipeline ID
        """
        pipeline_id = str(uuid.uuid4())
        
        self.pipelines[pipeline_id] = {
            "id": pipeline_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "status": PipelineStatus.PENDING,
            "current_step": None,
            "steps": {
                step.value: {
                    "status": PipelineStatus.PENDING,
                    "started_at": None,
                    "completed_at": None,
                    "result": None,
                    "error": None
                }
                for step in PipelineStep
            },
            "metadata": metadata or {},
            "results": {}
        }
        
        logger.info(f"Created pipeline: {pipeline_id}")
        return pipeline_id
    
    async def get_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline information by ID"""
        return self.pipelines.get(pipeline_id)
    
    async def update_pipeline_status(
        self,
        pipeline_id: str,
        status: PipelineStatus,
        current_step: Optional[PipelineStep] = None
    ):
        """Update the overall pipeline status"""
        if pipeline_id in self.pipelines:
            self.pipelines[pipeline_id]["status"] = status
            self.pipelines[pipeline_id]["updated_at"] = datetime.utcnow().isoformat()
            
            if current_step:
                self.pipelines[pipeline_id]["current_step"] = current_step.value
    
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
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        pipeline = self.pipelines[pipeline_id]
        step_info = pipeline["steps"][step.value]
        
        # Update step status
        step_info["status"] = PipelineStatus.IN_PROGRESS
        step_info["started_at"] = datetime.utcnow().isoformat()
        
        # Update pipeline status
        await self.update_pipeline_status(pipeline_id, PipelineStatus.IN_PROGRESS, step)
        
        try:
            # Execute the appropriate step
            if step == PipelineStep.DOCUMENT_UPLOAD:
                result = await self._handle_document_upload(pipeline_id, data)
            
            elif step == PipelineStep.DFD_EXTRACTION:
                result = await self._handle_dfd_extraction(pipeline_id, data)
            
            elif step == PipelineStep.THREAT_GENERATION:
                result = await self._handle_threat_generation(pipeline_id, data)
            
            elif step == PipelineStep.THREAT_REFINEMENT:
                result = await self._handle_threat_refinement(pipeline_id, data)
            
            elif step == PipelineStep.ATTACK_PATH_ANALYSIS:
                result = await self._handle_attack_path_analysis(pipeline_id, data)
            
            else:
                raise ValueError(f"Unknown step: {step}")
            
            # Update step with success
            step_info["status"] = PipelineStatus.COMPLETED
            step_info["completed_at"] = datetime.utcnow().isoformat()
            step_info["result"] = result
            
            # Store result in pipeline
            pipeline["results"][step.value] = result
            
            # Check if all steps are complete
            all_complete = all(
                s["status"] == PipelineStatus.COMPLETED
                for s in pipeline["steps"].values()
            )
            
            if all_complete:
                await self.update_pipeline_status(pipeline_id, PipelineStatus.COMPLETED)
            
            logger.info(f"Pipeline {pipeline_id}: Step {step} completed successfully")
            return result
            
        except Exception as e:
            # Update step with failure
            step_info["status"] = PipelineStatus.FAILED
            step_info["completed_at"] = datetime.utcnow().isoformat()
            step_info["error"] = str(e)
            
            # Update pipeline status
            await self.update_pipeline_status(pipeline_id, PipelineStatus.FAILED)
            
            logger.error(f"Pipeline {pipeline_id}: Step {step} failed: {e}")
            raise
    
    async def _handle_document_upload(
        self,
        pipeline_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle document upload step"""
        # This step is mostly handled by the endpoint
        # Just validate and store the document text
        document_text = data.get("document_text", "")
        
        if not document_text:
            raise ValueError("No document text provided")
        
        return {
            "text_length": len(document_text),
            "status": "uploaded"
        }
    
    async def _handle_dfd_extraction(
        self,
        pipeline_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle DFD extraction step using LLM.
        
        Args:
            pipeline_id: Pipeline identifier
            data: Must contain 'document_text' key
        
        Returns:
            Extracted DFD components
        """
        document_text = data.get("document_text")
        
        if not document_text:
            raise ValueError("Document text is required for DFD extraction")
        
        # Get LLM provider
        if not self.llm_provider:
            self.llm_provider = get_llm_provider(step="dfd_extraction")
        
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
        
        # Store in pipeline for use by subsequent steps
        self.pipelines[pipeline_id]["dfd_components"] = dfd_components
        
        return result
    
    async def _handle_threat_generation(
        self,
        pipeline_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle threat generation step"""
        # Get DFD components from previous step
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        dfd_components = pipeline.get("dfd_components")
        if not dfd_components:
            raise ValueError("DFD components not found. Run DFD extraction first.")
        
        # TODO: Implement threat generation logic
        # For now, return a placeholder
        return {
            "threats": [
                {
                    "id": "T001",
                    "name": "SQL Injection",
                    "category": "Input Validation",
                    "severity": "High",
                    "affected_component": "Web Server",
                    "description": "Potential SQL injection in user input fields"
                },
                {
                    "id": "T002",
                    "name": "Weak Authentication",
                    "category": "Authentication",
                    "severity": "Medium",
                    "affected_component": "API Gateway",
                    "description": "API keys may be exposed in client-side code"
                }
            ],
            "total_threats": 2,
            "high_severity": 1,
            "medium_severity": 1,
            "low_severity": 0
        }
    
    async def _handle_threat_refinement(
        self,
        pipeline_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle threat refinement step"""
        # TODO: Implement threat refinement logic
        return {
            "refined_threats": [],
            "status": "pending_implementation"
        }
    
    async def _handle_attack_path_analysis(
        self,
        pipeline_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle attack path analysis step"""
        # TODO: Implement attack path analysis logic
        return {
            "attack_paths": [],
            "status": "pending_implementation"
        }
    
    async def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Get the current status of a pipeline.
        
        Returns:
            Dictionary with pipeline status and step information
        """
        pipeline = self.pipelines.get(pipeline_id)
        
        if not pipeline:
            return {"error": "Pipeline not found"}
        
        return {
            "id": pipeline_id,
            "status": pipeline["status"],
            "current_step": pipeline["current_step"],
            "created_at": pipeline["created_at"],
            "updated_at": pipeline["updated_at"],
            "steps": pipeline["steps"],
            "metadata": pipeline["metadata"]
        }
    
    async def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancel a running pipeline"""
        if pipeline_id in self.pipelines:
            await self.update_pipeline_status(pipeline_id, PipelineStatus.CANCELLED)
            logger.info(f"Pipeline {pipeline_id} cancelled")
            return True
        return False
    
    async def list_pipelines(
        self,
        status: Optional[PipelineStatus] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List pipelines with optional filtering.
        
        Args:
            status: Filter by status
            limit: Maximum number of results
        
        Returns:
            List of pipeline summaries
        """
        pipelines = []
        
        for pipeline_id, pipeline in self.pipelines.items():
            if status and pipeline["status"] != status:
                continue
            
            pipelines.append({
                "id": pipeline_id,
                "status": pipeline["status"],
                "current_step": pipeline["current_step"],
                "created_at": pipeline["created_at"],
                "updated_at": pipeline["updated_at"]
            })
        
        # Sort by created_at descending
        pipelines.sort(key=lambda x: x["created_at"], reverse=True)
        
        return pipelines[:limit]