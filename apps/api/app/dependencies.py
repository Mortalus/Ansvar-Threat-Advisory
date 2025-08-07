"""
Application dependencies and shared instances
"""
from app.core.pipeline.manager import PipelineManager
from app.database import get_async_session, check_connection_health
import logging

logger = logging.getLogger(__name__)

# Create a singleton instance of PipelineManager with bulletproof session management
pipeline_manager_instance = PipelineManager()

async def get_pipeline_manager() -> PipelineManager:
    """
    BULLETPROOF dependency to get the pipeline manager instance.
    Includes proactive connection health monitoring and auto-recovery.
    """
    # Proactive health check before returning manager
    try:
        is_healthy, recovery_attempted = await check_connection_health()
        if not is_healthy:
            logger.warning("⚠️ Database connection unhealthy - PipelineManager may have reduced functionality")
        elif recovery_attempted:
            logger.info("✅ Database connection recovered - PipelineManager ready")
    except Exception as health_error:
        logger.error(f"❌ Pipeline manager health check failed: {health_error}")
        # Continue anyway - the resilient session creation will handle issues
    
    return pipeline_manager_instance

# Re-export database session dependency for convenience
get_db = get_async_session  # Alias for consistency with agent_management.py

__all__ = ['get_pipeline_manager', 'get_async_session', 'get_db']