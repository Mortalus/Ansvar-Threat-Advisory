"""LLM-specific background tasks for compute-intensive operations"""

import asyncio
import logging
from typing import Dict, Any, Optional
from celery import current_task
from datetime import datetime

from app.celery_app import celery_app
from app.core.llm import get_llm_provider
from app.core.pipeline.dfd_extraction_service import extract_dfd_from_text, validate_dfd_components
from app.database import AsyncSessionLocal
from app.services import PipelineService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="extract_dfd_task")
def extract_dfd_task(self, pipeline_id: str, document_text: str, llm_config: Optional[Dict[str, Any]] = None):
    """
    Extract DFD components from document text using LLM
    
    Args:
        self: Celery task instance
        pipeline_id: Pipeline identifier
        document_text: Text content to analyze
        llm_config: Optional LLM configuration override
        
    Returns:
        Dict with DFD components and validation results
    """
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={
                'pipeline_id': pipeline_id,
                'status': 'Starting DFD extraction',
                'text_length': len(document_text),
                'started_at': datetime.utcnow().isoformat()
            }
        )
        
        # Run async DFD extraction
        result = asyncio.run(_extract_dfd_async(pipeline_id, document_text, llm_config))
        
        # Update final status
        current_task.update_state(
            state='SUCCESS',
            meta={
                'pipeline_id': pipeline_id,
                'status': 'DFD extraction completed',
                'quality_score': result.get('validation', {}).get('quality_score'),
                'components_found': len(result.get('dfd_components', {}).get('processes', [])),
                'completed_at': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"DFD extraction completed for pipeline {pipeline_id}")
        return result
        
    except Exception as exc:
        logger.error(f"DFD extraction failed for pipeline {pipeline_id}: {exc}")
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'pipeline_id': pipeline_id,
                'status': 'DFD extraction failed',
                'error': str(exc),
                'failed_at': datetime.utcnow().isoformat()
            }
        )
        
        # Retry with backoff
        if self.request.retries < self.max_retries:
            countdown = min(300, (2 ** self.request.retries) * 60)  # Exponential backoff, max 5 min
            logger.info(f"Retrying DFD extraction for pipeline {pipeline_id} in {countdown} seconds")
            raise self.retry(exc=exc, countdown=countdown)
        
        raise exc


async def _extract_dfd_async(pipeline_id: str, document_text: str, llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Async DFD extraction implementation"""
    
    # Get LLM provider
    provider = await get_llm_provider(step="dfd_extraction")
    
    # Extract DFD components
    dfd_components, token_usage = await extract_dfd_from_text(
        llm_provider=provider,
        document_text=document_text
    )
    
    logger.info(f"DFD extraction token usage: {token_usage['total_tokens']} tokens, ${token_usage['total_cost_usd']:.4f}")
    
    # Validate extraction
    validation_result = await validate_dfd_components(dfd_components)
    
    # Store results in database
    session = AsyncSessionLocal()
    try:
        service = PipelineService(session)
        
        # Update pipeline data
        await service.update_pipeline_data(
            pipeline_id,
            dfd_components=dfd_components.model_dump(),
            dfd_validation=validation_result
        )
        
        # Add step result
        await service.add_step_result(
            pipeline_id=pipeline_id,
            step_name="dfd_extraction",
            result_type="dfd_components",
            result_data={
                "dfd_components": dfd_components.model_dump(),
                "validation": validation_result,
                "extracted_at": datetime.utcnow().isoformat()
            },
            llm_provider=provider.__class__.__name__,
            llm_model=getattr(provider, 'model_name', 'unknown')
        )
        
    finally:
        await session.close()
    
    return {
        "dfd_components": dfd_components.model_dump(),
        "validation": validation_result,
        "extracted_at": datetime.utcnow().isoformat()
    }


@celery_app.task(bind=True, name="generate_threats_task")
def generate_threats_task(self, pipeline_id: str, dfd_components: Dict[str, Any], llm_config: Optional[Dict[str, Any]] = None):
    """
    Generate threats from DFD components using LLM
    
    Args:
        self: Celery task instance
        pipeline_id: Pipeline identifier
        dfd_components: DFD structure to analyze
        llm_config: Optional LLM configuration
        
    Returns:
        Dict with threat analysis results
    """
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'pipeline_id': pipeline_id,
                'status': 'Analyzing DFD for threats',
                'components_count': len(dfd_components.get('processes', [])),
                'started_at': datetime.utcnow().isoformat()
            }
        )
        
        result = asyncio.run(_generate_threats_async(pipeline_id, dfd_components, llm_config))
        
        current_task.update_state(
            state='SUCCESS',
            meta={
                'pipeline_id': pipeline_id,
                'status': 'Threat generation completed',
                'threats_found': len(result.get('threats', [])),
                'completed_at': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Threat generation completed for pipeline {pipeline_id}")
        return result
        
    except Exception as exc:
        logger.error(f"Threat generation failed for pipeline {pipeline_id}: {exc}")
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'pipeline_id': pipeline_id,
                'status': 'Threat generation failed',
                'error': str(exc),
                'failed_at': datetime.utcnow().isoformat()
            }
        )
        
        if self.request.retries < self.max_retries:
            countdown = min(600, (2 ** self.request.retries) * 120)  # Longer backoff for LLM tasks
            raise self.retry(exc=exc, countdown=countdown)
        
        raise exc


async def _generate_threats_async(pipeline_id: str, dfd_components: Dict[str, Any], llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Async threat generation implementation"""
    
    # TODO: Implement actual threat generation with LLM
    # For now, return placeholder threats based on DFD components
    
    threats = []
    processes = dfd_components.get('processes', [])
    data_flows = dfd_components.get('data_flows', [])
    
    # Generate threats based on processes
    for i, process in enumerate(processes):
        threats.append({
            "id": f"T{i+1:03d}",
            "name": f"Unauthorized access to {process}",
            "category": "Authentication",
            "severity": "High" if "server" in process.lower() else "Medium",
            "affected_component": process,
            "description": f"Potential unauthorized access to {process} component",
            "stride_category": "Spoofing",
            "likelihood": "Medium",
            "impact": "High",
            "mitigation_suggestions": [
                "Implement strong authentication",
                "Use principle of least privilege",
                "Monitor access logs"
            ]
        })
    
    # Store in database
    session = AsyncSessionLocal()
    try:
        service = PipelineService(session)
        
        result_data = {
            "threats": threats,
            "total_threats": len(threats),
            "high_severity": len([t for t in threats if t["severity"] == "High"]),
            "medium_severity": len([t for t in threats if t["severity"] == "Medium"]),
            "low_severity": len([t for t in threats if t["severity"] == "Low"]),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Update pipeline data
        await service.update_pipeline_data(pipeline_id, threats=threats)
        
        # Add step result
        await service.add_step_result(
            pipeline_id=pipeline_id,
            step_name="threat_generation",
            result_type="threats",
            result_data=result_data,
            llm_provider="placeholder",
            llm_model="placeholder"
        )
        
        return result_data
        
    finally:
        await session.close()


@celery_app.task(bind=True, name="refine_threats_task")
def refine_threats_task(self, pipeline_id: str, threats: list, refinement_criteria: Dict[str, Any]):
    """Refine and prioritize threats using LLM"""
    try:
        # Placeholder implementation
        result = {
            "refined_threats": threats,
            "refinement_applied": refinement_criteria,
            "refined_at": datetime.utcnow().isoformat()
        }
        
        # Store results would go here
        
        return result
        
    except Exception as exc:
        logger.error(f"Threat refinement failed for pipeline {pipeline_id}: {exc}")
        raise exc


@celery_app.task(bind=True, name="analyze_attack_paths_task") 
def analyze_attack_paths_task(self, pipeline_id: str, threats: list, dfd_components: Dict[str, Any]):
    """Analyze potential attack paths using LLM"""
    try:
        # Placeholder implementation
        result = {
            "attack_paths": [],
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        # Store results would go here
        
        return result
        
    except Exception as exc:
        logger.error(f"Attack path analysis failed for pipeline {pipeline_id}: {exc}")
        raise exc