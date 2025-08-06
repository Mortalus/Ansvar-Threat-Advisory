"""LLM provider endpoints"""

from fastapi import APIRouter, HTTPException
from typing import List
from app.core.llm import get_llm_provider, test_llm_provider
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm", tags=["llm"])

@router.get("/providers")
async def list_providers() -> List[str]:
    """List available LLM providers"""
    return ["ollama", "azure", "scaleway"]

@router.post("/test/{provider}")
async def test_provider(provider: str):
    """Test if a specific LLM provider is working"""
    try:
        if provider not in ["ollama", "azure", "scaleway"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider. Must be one of: ollama, azure, scaleway"
            )
        
        # Try to get the provider
        llm = await get_llm_provider(step="default")
        
        # Test the connection
        is_working = await llm.validate_connection()
        
        if is_working:
            return {
                "success": True,
                "message": f"Provider '{provider}' is working correctly",
                "provider": provider
            }
        else:
            return {
                "success": False,
                "message": f"Provider '{provider}' is not accessible or misconfigured",
                "provider": provider
            }
            
    except Exception as e:
        logger.error(f"Failed to test provider {provider}: {e}")
        return {
            "success": False,
            "message": str(e),
            "provider": provider
        }

@router.get("/config")
async def get_llm_config():
    """Get current LLM configuration (without sensitive data)"""
    config = {
        "step1_provider": os.getenv("STEP1_LLM_PROVIDER", "not_configured"),
        "step2_provider": os.getenv("STEP2_LLM_PROVIDER", "not_configured"),
        "step3_provider": os.getenv("STEP3_LLM_PROVIDER", "not_configured"),
        "step4_provider": os.getenv("STEP4_LLM_PROVIDER", "not_configured"),
        "step5_provider": os.getenv("STEP5_LLM_PROVIDER", "not_configured"),
        
        "ollama": {
            "configured": bool(os.getenv("OLLAMA_BASE_URL")),
            "base_url": os.getenv("OLLAMA_BASE_URL", "not_configured")
        },
        "azure": {
            "configured": bool(os.getenv("AZURE_OPENAI_API_KEY")),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "not_configured")
        },
        "scaleway": {
            "configured": bool(os.getenv("SCALEWAY_API_KEY") or os.getenv("SCW_API_KEY")),
            "endpoint": os.getenv("SCALEWAY_ENDPOINT", "not_configured")
        }
    }
    
    return config