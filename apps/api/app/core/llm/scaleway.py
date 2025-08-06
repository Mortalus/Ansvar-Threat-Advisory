"""Scaleway LLM Provider"""

import httpx
import json
from typing import Optional, Dict, Any
from app.core.llm.base import BaseLLMProvider, LLMResponse
import logging

logger = logging.getLogger(__name__)

class ScalewayProvider(BaseLLMProvider):
    """Provider for Scaleway AI models"""
    
    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.scaleway.ai/v1",
        model: str = "llama-3.1-70b"
    ):
        super().__init__(model)
        self.api_key = api_key
        self.endpoint = endpoint.rstrip('/')
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=300.0  # 5 minute timeout
        )
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate response using Scaleway AI"""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            response = await self.client.post(
                f"{self.endpoint}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse Scaleway response format
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            usage = data.get("usage", {})
            
            return LLMResponse(
                content=message.get("content", ""),
                model=data.get("model", self.model),
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                },
                metadata={
                    "finish_reason": choice.get("finish_reason"),
                    "id": data.get("id")
                }
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Scaleway API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to generate with Scaleway: {e}")
            raise
    
    async def validate_connection(self) -> bool:
        """Check if Scaleway AI is accessible"""
        try:
            # Try a simple completion
            response = await self.generate(
                prompt="Hello",
                max_tokens=5
            )
            return len(response.content) > 0
            
        except Exception as e:
            logger.error(f"Failed to validate Scaleway connection: {e}")
            return False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()