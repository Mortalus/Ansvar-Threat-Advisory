"""Azure OpenAI LLM Provider"""

from typing import Optional
from openai import AsyncAzureOpenAI
from app.core.llm.base import BaseLLMProvider, LLMResponse
import logging

logger = logging.getLogger(__name__)

class AzureProvider(BaseLLMProvider):
    """Provider for Azure OpenAI models"""
    
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        api_version: str = "2024-02-15-preview",
        model: str = "gpt-4"
    ):
        super().__init__(model)
        self.api_key = api_key
        self.endpoint = endpoint
        self.api_version = api_version
        
        # Initialize Azure OpenAI client
        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate response using Azure OpenAI"""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "id": response.id
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate with Azure OpenAI: {e}")
            raise
    
    async def validate_connection(self) -> bool:
        """Check if Azure OpenAI is accessible"""
        try:
            # Try a simple completion
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate Azure OpenAI connection: {e}")
            return False