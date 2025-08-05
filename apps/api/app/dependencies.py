# app/dependencies.py

from typing import Generator
from app.core.pipeline.manager import PipelineManager
from app.config import get_settings

# Global pipeline manager instance
_pipeline_manager = None

def get_pipeline_manager() -> PipelineManager:
    """Get or create pipeline manager instance"""
    global _pipeline_manager
    if _pipeline_manager is None:
        settings = get_settings()
        _pipeline_manager = PipelineManager(settings)
    return _pipeline_manager
