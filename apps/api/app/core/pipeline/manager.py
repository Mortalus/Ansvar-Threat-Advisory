# apps/api/app/core/pipeline/manager.py

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

from app.config import Settings
from app.core.llm.base import BaseLLMProvider
from app.core.llm.ollama import OllamaProvider
from app.core.llm.azure import AzureOpenAIProvider
from app.core.llm.scaleway import ScalewayProvider

# Import pipeline steps
from app.core.pipeline.steps.dfd_extraction import DFDExtractionStep

logger = logging.getLogger(__name__)

class PipelineStep(str, Enum):
    DOCUMENT_UPLOAD = "document_upload"
    DFD_EXTRACTION = "dfd_extraction"
    THREAT_GENERATION = "threat_generation"
    THREAT_REFINEMENT = "threat_refinement"
    ATTACK_PATH_ANALYSIS = "attack_path_analysis"

class PipelineStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pipelines: Dict[str, Dict[str, Any]] = {}
        
        # Initialize step handlers
        self.dfd_extraction_step = None
        
    def create_pipeline(self, name: str) -> str:
        """Create a new pipeline instance"""
        pipeline_id = str(uuid.uuid4())
        
        self.pipelines[pipeline_id] = {
            "id": pipeline_id,
            "name": name,
            "status": PipelineStatus.IDLE,
            "current_step": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "steps": {
                step.value: {
                    "status": "pending",
                    "data": None,
                    "error": None,
                    "started_at": None,
                    "completed_at": None
                } for step in PipelineStep
            },
            "errors": [],
            "results": {}
        }
        
        return pipeline_id
    
    def get_llm_provider(self, step_num: int) -> BaseLLMProvider:
        """Get the appropriate LLM provider for a step"""
        config = self.settings.get_step_config(step_num)
        
        if config["provider"] == "ollama":
            return OllamaProvider(config)
        elif config["provider"] == "azure":
            return AzureOpenAIProvider(config)
        elif config["provider"] == "scaleway":
            return ScalewayProvider(config)
        else:
            raise ValueError(f"Unknown provider: {config['provider']}")
    
    async def validate_step_input(self, pipeline_id: str, step: PipelineStep) -> bool:
        """Validate that the input for a step is ready"""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return False
            
        # Check previous step completion
        step_order = list(PipelineStep)
        current_index = step_order.index(step)
        
        if current_index > 0:
            prev_step = step_order[current_index - 1]
            if pipeline["steps"][prev_step.value]["status"] != "completed":
                return False
                
            # Validate previous step output exists
            if not pipeline["steps"][prev_step.value]["data"]:
                return False
                
        return True
    
    async def execute_step(self, pipeline_id: str, step: PipelineStep, input_data: Any = None) -> Dict[str, Any]:
        """Execute a specific pipeline step"""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
            
        # Update pipeline status
        pipeline["status"] = PipelineStatus.RUNNING
        pipeline["current_step"] = step.value
        pipeline["steps"][step.value]["status"] = "running"
        pipeline["steps"][step.value]["started_at"] = datetime.utcnow().isoformat()
        pipeline["updated_at"] = datetime.utcnow().isoformat()
        
        try:
            # Get step number for LLM config
            step_num = list(PipelineStep).index(step) + 1
            
            # Execute based on step type
            if step == PipelineStep.DOCUMENT_UPLOAD:
                result = await self._handle_document_upload(input_data)
                
            elif step == PipelineStep.DFD_EXTRACTION:
                result = await self._extract_dfd(pipeline_id, step_num)
                
            elif step == PipelineStep.THREAT_GENERATION:
                result = await self._generate_threats(pipeline_id, step_num)
                
            elif step == PipelineStep.THREAT_REFINEMENT:
                result = await self._refine_threats(pipeline_id, step_num)
                
            elif step == PipelineStep.ATTACK_PATH_ANALYSIS:
                result = await self._analyze_attack_paths(pipeline_id, step_num)
                
            else:
                raise ValueError(f"Unknown step: {step}")
                
            # Update pipeline with results
            pipeline["steps"][step.value]["status"] = "completed"
            pipeline["steps"][step.value]["data"] = result
            pipeline["steps"][step.value]["completed_at"] = datetime.utcnow().isoformat()
            pipeline["updated_at"] = datetime.utcnow().isoformat()
            
            # Check if all steps are complete
            all_complete = all(
                s["status"] == "completed" 
                for s in pipeline["steps"].values()
            )
            if all_complete:
                pipeline["status"] = PipelineStatus.COMPLETED
            else:
                pipeline["status"] = PipelineStatus.IDLE
                
            return result
            
        except Exception as e:
            logger.error(f"Step {step} failed: {e}")
            pipeline["steps"][step.value]["status"] = "failed"
            pipeline["steps"][step.value]["error"] = str(e)
            pipeline["status"] = PipelineStatus.FAILED
            pipeline["errors"].append({
                "step": step.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    async def _handle_document_upload(self, input_data: Any) -> Dict[str, Any]:
        """Handle document upload step"""
        # This would typically process the uploaded file
        # For now, we'll just store the file information
        return {
            "status": "completed",
            "filename": input_data.get("filename", "document.txt"),
            "content": input_data.get("content", ""),
            "size": len(input_data.get("content", "")),
            "type": input_data.get("type", "text/plain"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _extract_dfd(self, pipeline_id: str, step_num: int) -> Dict[str, Any]:
        """Extract DFD from uploaded documents"""
        logger.info(f"Starting DFD extraction for pipeline {pipeline_id}")
        
        # Get LLM provider for this step
        llm_provider = self.get_llm_provider(step_num)
        
        # Initialize DFD extraction step if not already done
        if not self.dfd_extraction_step:
            self.dfd_extraction_step = DFDExtractionStep(llm_provider)
        else:
            # Update LLM provider
            self.dfd_extraction_step.llm_provider = llm_provider
        
        # Get pipeline data
        pipeline = self.pipelines[pipeline_id]
        
        # Prepare input data from previous steps
        pipeline_data = {
            "document_upload": pipeline["steps"]["document_upload"]
        }
        
        # Execute DFD extraction
        result = await self.dfd_extraction_step.execute(pipeline_data)
        
        logger.info(f"DFD extraction completed for pipeline {pipeline_id}")
        return result
    
    async def _generate_threats(self, pipeline_id: str, step_num: int) -> Dict[str, Any]:
        """Generate threats using STRIDE methodology"""
        # TODO: Implement threat generation
        logger.info(f"Generating threats for pipeline {pipeline_id}")
        
        pipeline = self.pipelines[pipeline_id]
        dfd_data = pipeline["steps"]["dfd_extraction"]["data"]
        
        # For now, return mock data
        return {
            "status": "completed",
            "threats": [
                {
                    "id": "T001",
                    "category": "Spoofing",
                    "component": "User Authentication",
                    "description": "Attacker could spoof user identity",
                    "risk_level": "High"
                },
                {
                    "id": "T002",
                    "category": "Tampering",
                    "component": "Data Flow",
                    "description": "Data could be modified in transit",
                    "risk_level": "Medium"
                }
            ],
            "total_threats": 2,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _refine_threats(self, pipeline_id: str, step_num: int) -> Dict[str, Any]:
        """Refine and enhance generated threats"""
        # TODO: Implement threat refinement
        logger.info(f"Refining threats for pipeline {pipeline_id}")
        
        pipeline = self.pipelines[pipeline_id]
        threats_data = pipeline["steps"]["threat_generation"]["data"]
        
        # For now, return enhanced mock data
        return {
            "status": "completed",
            "refined_threats": threats_data.get("threats", []),
            "enhancements": ["Added CVSS scores", "Linked to CWE database"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _analyze_attack_paths(self, pipeline_id: str, step_num: int) -> Dict[str, Any]:
        """Analyze potential attack paths"""
        # TODO: Implement attack path analysis
        logger.info(f"Analyzing attack paths for pipeline {pipeline_id}")
        
        pipeline = self.pipelines[pipeline_id]
        threats_data = pipeline["steps"]["threat_refinement"]["data"]
        
        # For now, return mock attack paths
        return {
            "status": "completed",
            "attack_paths": [
                {
                    "id": "AP001",
                    "name": "External to Database",
                    "steps": ["Internet", "CDN", "Load Balancer", "Web Server", "Database"],
                    "risk_score": 8.5,
                    "exploited_threats": ["T001", "T002"]
                }
            ],
            "total_paths": 1,
            "critical_paths": 1,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_pipeline_status(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a pipeline"""
        return self.pipelines.get(pipeline_id)
    
    def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all pipelines"""
        return list(self.pipelines.values())
    
    async def run_full_pipeline(self, pipeline_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete pipeline from start to finish"""
        results = {}
        
        # Execute each step in order
        for step in PipelineStep:
            if step == PipelineStep.DOCUMENT_UPLOAD:
                result = await self.execute_step(pipeline_id, step, document_data)
            else:
                # Validate input is ready
                if not await self.validate_step_input(pipeline_id, step):
                    raise ValueError(f"Input not ready for step {step}")
                result = await self.execute_step(pipeline_id, step)
            
            results[step.value] = result
            
            # Add small delay between steps (optional)
            await asyncio.sleep(0.5)
        
        return results