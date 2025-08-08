"""
LLM Service wrapper for workflow manager compatibility
"""

from app.core.llm import get_llm_provider
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """
    Simple wrapper around the LLM provider for workflow manager compatibility.
    This maintains backward compatibility with the workflow manager.
    """
    
    def __init__(self):
        self._provider = None
    
    async def get_provider(self, step: str = "default"):
        """Get the configured LLM provider"""
        if self._provider is None:
            self._provider = await get_llm_provider(step=step)
        return self._provider
    
    async def generate(self, prompt: str, step: str = "default", **kwargs):
        """Generate text using the LLM provider"""
        provider = await self.get_provider(step)
        return await provider.generate(prompt, **kwargs)
    
    async def validate_connection(self, step: str = "default"):
        """Validate the LLM provider connection"""
        provider = await self.get_provider(step)
        return await provider.validate_connection()