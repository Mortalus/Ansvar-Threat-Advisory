"""
Application dependencies and shared instances
"""
from app.core.pipeline.manager import PipelineManager
from app.database import get_async_session

# Create a singleton instance of PipelineManager
# In production, this should be replaced with a proper database
pipeline_manager_instance = PipelineManager()

def get_pipeline_manager() -> PipelineManager:
    """
    Dependency to get the pipeline manager instance.
    Returns the same instance for all requests.
    """
    return pipeline_manager_instance

# Re-export database session dependency for convenience
__all__ = ['get_pipeline_manager', 'get_async_session']