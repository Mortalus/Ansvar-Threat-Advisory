"""
Celery tasks for knowledge base management and ingestion.
"""
from typing import Dict, Any
from celery import current_task
from app.celery_app import celery_app
from app.services.ingestion_service import IngestionService
import asyncio
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.ingest_knowledge_base", bind=True)
def ingest_knowledge_base(self, url: str, source_name: str) -> Dict[str, Any]:
    """
    Celery task to ingest threat intelligence data into the knowledge base.
    
    Args:
        url: URL to fetch data from
        source_name: Name of the source (e.g., 'MITRE_ATT&CK', 'CISA_KEV')
        
    Returns:
        Dictionary with ingestion results
    """
    try:
        # Update task state
        current_task.update_state(
            state='PROGRESS',
            meta={'status': f'Starting ingestion from {source_name}...'}
        )
        
        # Create ingestion service
        service = IngestionService()
        
        # Run the async ingestion in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                service.ingest_from_url(url, source_name)
            )
        finally:
            loop.close()
        
        # Update task state with result
        current_task.update_state(
            state='SUCCESS',
            meta=result
        )
        
        logger.info(f"Successfully ingested data from {source_name}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in knowledge base ingestion task: {str(e)}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise


@celery_app.task(name="tasks.update_all_knowledge_bases")
def update_all_knowledge_bases() -> Dict[str, Any]:
    """
    Periodic task to update all configured knowledge bases.
    This can be scheduled with Celery Beat.
    """
    sources = [
        {
            "name": "CISA_KEV",
            "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        },
        # Add more sources as needed
        # {
        #     "name": "MITRE_ATT&CK",
        #     "url": "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
        # }
    ]
    
    results = []
    for source in sources:
        try:
            # Queue individual ingestion tasks
            task = ingest_knowledge_base.delay(source["url"], source["name"])
            results.append({
                "source": source["name"],
                "task_id": task.id,
                "status": "queued"
            })
        except Exception as e:
            results.append({
                "source": source["name"],
                "status": "error",
                "error": str(e)
            })
    
    return {
        "status": "success",
        "message": f"Queued {len(results)} knowledge base updates",
        "tasks": results
    }