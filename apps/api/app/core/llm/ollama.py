import httpx
from typing import Optional
from app.core.llm.base import BaseLLMProvider, LLMResponse
import logging

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider implementation"""
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        url = f"{self.config['base_url']}/api/generate"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.config["model"],
            "prompt": prompt,
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 2000),
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                
                return LLMResponse(
                    content=data.get("response", ""),
                    model=self.config["model"],
                    provider="ollama"
                )
            except Exception as e:
                logger.error(f"Ollama generation error: {e}")
                raise
    
    async def validate_connection(self) -> bool:
        url = f"{self.config['base_url']}/api/tags"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=5.0)
                return response.status_code == 200
            except:
                return False