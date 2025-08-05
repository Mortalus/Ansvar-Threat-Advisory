from openai import AsyncAzureOpenAI
from typing import Optional
from app.core.llm.base import BaseLLMProvider, LLMResponse
import logging

logger = logging.getLogger(__name__)

class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI provider implementation"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.client = AsyncAzureOpenAI(
            api_key=config["api_key"],
            api_version=config["api_version"],
            azure_endpoint=config["endpoint"]
        )
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config["model"],
                messages=messages,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 2000)
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.config["model"],
                provider="azure",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )
        except Exception as e:
            logger.error(f"Azure OpenAI generation error: {e}")
            raise
    
    async def validate_connection(self) -> bool:
        try:
            models = await self.client.models.list()
            return True
        except:
            return False