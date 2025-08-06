"""LLM Provider Factory and Base Classes"""

import os
from typing import Optional
from app.core.llm.base import BaseLLMProvider
from app.core.llm.ollama import OllamaProvider
from app.core.llm.azure import AzureProvider
from app.core.llm.scaleway import ScalewayProvider
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def get_llm_provider(step: str = "default") -> BaseLLMProvider:
    """
    Get the appropriate LLM provider for a pipeline step.
    
    Args:
        step: The pipeline step name (e.g., 'dfd_extraction', 'threat_generation')
    
    Returns:
        An instance of the appropriate LLM provider
    
    Raises:
        ValueError: If no valid provider is configured
    """
    # Map step names to configuration keys
    step_mapping = {
        "dfd_extraction": "step1",
        "threat_generation": "step2", 
        "threat_refinement": "step3",
        "attack_path_analysis": "step4",
        "default": "step1"
    }
    
    step_prefix = step_mapping.get(step, "step1")
    
    # Get provider type from settings
    provider_type = getattr(settings, f"{step_prefix}_llm_provider", "ollama").lower()
    
    logger.info(f"Getting LLM provider for step '{step}': {provider_type}")
    
    try:
        if provider_type == "ollama":
            base_url = settings.ollama_base_url
            model = getattr(settings, f"{step_prefix}_ollama_model", "llama3:8b")
            
            return OllamaProvider(
                base_url=base_url,
                model=model
            )
        
        elif provider_type == "azure":
            api_key = settings.azure_openai_api_key
            endpoint = settings.azure_openai_endpoint
            api_version = settings.azure_openai_api_version
            model = getattr(settings, f"{step_prefix}_azure_model", "gpt-4")
            
            if not api_key or not endpoint:
                raise ValueError("Azure OpenAI credentials not configured")
            
            return AzureProvider(
                api_key=api_key,
                endpoint=endpoint,
                api_version=api_version,
                model=model
            )
        
        elif provider_type == "scaleway":
            api_key = settings.scaleway_api_key or settings.scw_api_key
            endpoint = settings.scaleway_endpoint
            model = getattr(settings, f"{step_prefix}_scaleway_model", "llama-3.3-70b-instruct")
            
            if not api_key:
                raise ValueError("Scaleway API key not configured (set SCALEWAY_API_KEY or SCW_API_KEY)")
            
            return ScalewayProvider(
                api_key=api_key,
                endpoint=endpoint,
                model=model
            )
        
        else:
            raise ValueError(f"Unknown LLM provider: {provider_type}")
    
    except Exception as e:
        logger.error(f"Failed to initialize LLM provider: {e}")
        raise

def test_llm_provider(provider: BaseLLMProvider) -> bool:
    """
    Test if an LLM provider is working correctly.
    
    Args:
        provider: The LLM provider to test
    
    Returns:
        True if the provider is working, False otherwise
    """
    try:
        import asyncio
        
        async def test():
            response = await provider.generate(
                prompt="Hello, please respond with 'OK' if you can read this.",
                system_prompt="You are a helpful assistant. Respond with exactly 'OK'."
            )
            return "ok" in response.content.lower()
        
        return asyncio.run(test())
    
    except Exception as e:
        logger.error(f"LLM provider test failed: {e}")
        return False

__all__ = [
    "BaseLLMProvider",
    "OllamaProvider", 
    "AzureProvider",
    "ScalewayProvider",
    "get_llm_provider",
    "test_llm_provider"
]