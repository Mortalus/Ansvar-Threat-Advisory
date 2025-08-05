import httpx
from typing import Optional
from app.core.llm.base import BaseLLMProvider, LLMResponse
import logging

logger = logging.getLogger(__name__)

class ScalewayProvider(BaseLLMProvider):
    """Scaleway AI provider implementation"""
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        url = f"{self.config['endpoint']}/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 2000),
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=self.config["model"],
                    provider="scaleway",
                    usage=data.get("usage")
                )
            except Exception as e:
                logger.error(f"Scaleway generation error: {e}")
                raise
    
    async def validate_connection(self) -> bool:
        url = f"{self.config['endpoint']}/models"
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=5.0)
                return response.status_code == 200
            except:
                return False
