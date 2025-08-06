"""
API endpoints for knowledge base management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from app.database import get_async_session
from app.services.ingestion_service import IngestionService
from app.tasks.knowledge_base_tasks import ingest_knowledge_base
from app.models import KnowledgeBaseEntry
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge-base", tags=["knowledge-base"])


class KnowledgeSourceRequest(BaseModel):
    """Request model for adding a knowledge source."""
    url: str
    source_name: str


class SearchRequest(BaseModel):
    """Request model for searching the knowledge base."""
    query: str
    limit: int = 5


class KnowledgeBaseStats(BaseModel):
    """Statistics about the knowledge base."""
    total_entries: int
    sources: Dict[str, int]
    last_updated: Optional[str]


@router.post("/ingest")
async def ingest_knowledge_source(
    request: KnowledgeSourceRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Trigger ingestion of a knowledge source.
    
    Args:
        request: Source URL and name
        background_tasks: FastAPI background tasks
        session: Database session
        
    Returns:
        Task information
    """
    try:
        # Queue the ingestion task
        task = ingest_knowledge_base.delay(request.url, request.source_name)
        
        logger.info(f"Queued ingestion task for {request.source_name} from {request.url}")
        
        return {
            "status": "queued",
            "task_id": task.id,
            "source_name": request.source_name,
            "message": f"Ingestion task queued for {request.source_name}"
        }
        
    except Exception as e:
        logger.error(f"Error queueing ingestion task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue ingestion: {str(e)}"
        )


@router.post("/search")
async def search_knowledge_base(
    request: SearchRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Search the knowledge base for similar content.
    
    Args:
        request: Search query and limit
        session: Database session
        
    Returns:
        List of similar entries
    """
    try:
        ingestion_service = IngestionService()
        results = await ingestion_service.search_similar(
            query=request.query,
            limit=request.limit
        )
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get statistics about the knowledge base.
    
    Returns:
        Knowledge base statistics
    """
    try:
        # Count total entries
        stmt = select(func.count(KnowledgeBaseEntry.id))
        result = await session.execute(stmt)
        total_entries = result.scalar() or 0
        
        # Count by source
        stmt = select(
            KnowledgeBaseEntry.source,
            func.count(KnowledgeBaseEntry.id).label('count')
        ).group_by(KnowledgeBaseEntry.source)
        
        result = await session.execute(stmt)
        sources = {row.source: row.count for row in result}
        
        # Get last update time
        stmt = select(func.max(KnowledgeBaseEntry.created_at))
        result = await session.execute(stmt)
        last_updated = result.scalar()
        
        return KnowledgeBaseStats(
            total_entries=total_entries,
            sources=sources,
            last_updated=last_updated.isoformat() if last_updated else None
        )
        
    except Exception as e:
        logger.error(f"Error getting knowledge base stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/initialize-default")
async def initialize_default_sources(
    background_tasks: BackgroundTasks
):
    """
    Initialize the knowledge base with default sources.
    
    Returns:
        List of queued ingestion tasks
    """
    try:
        default_sources = [
            {
                "name": "CISA_KEV",
                "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
            }
            # Add more default sources as needed
        ]
        
        tasks = []
        for source in default_sources:
            task = ingest_knowledge_base.delay(source["url"], source["name"])
            tasks.append({
                "source": source["name"],
                "task_id": task.id,
                "status": "queued"
            })
            logger.info(f"Queued ingestion for {source['name']}")
        
        return {
            "status": "success",
            "message": f"Queued {len(tasks)} default knowledge sources",
            "tasks": tasks
        }
        
    except Exception as e:
        logger.error(f"Error initializing default sources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize: {str(e)}"
        )


@router.delete("/source/{source_name}")
async def delete_knowledge_source(
    source_name: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete all entries from a specific knowledge source.
    
    Args:
        source_name: Name of the source to delete
        session: Database session
        
    Returns:
        Deletion result
    """
    try:
        from sqlalchemy import delete
        
        stmt = delete(KnowledgeBaseEntry).where(
            KnowledgeBaseEntry.source == source_name
        )
        result = await session.execute(stmt)
        await session.commit()
        
        deleted_count = result.rowcount
        
        logger.info(f"Deleted {deleted_count} entries from source {source_name}")
        
        return {
            "status": "success",
            "source": source_name,
            "deleted_entries": deleted_count,
            "message": f"Successfully deleted {deleted_count} entries from {source_name}"
        }
        
    except Exception as e:
        logger.error(f"Error deleting knowledge source: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete source: {str(e)}"
        )