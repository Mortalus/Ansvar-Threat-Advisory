"""
Application dependencies and shared instances
"""
from app.core.pipeline.manager import PipelineManager

# Create a singleton instance of PipelineManager
# In production, this should be replaced with a proper database
pipeline_manager_instance = PipelineManager()

def get_pipeline_manager() -> PipelineManager:
    """
    Dependency to get the pipeline manager instance.
    Returns the same instance for all requests.
    """
    return pipeline_manager_instance