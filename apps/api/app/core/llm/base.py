"""Base classes for LLM providers"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class LLMResponse(BaseModel):
    """Standard response from LLM providers"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, model: str = "default"):
        self.model = model
        self.client = None  # Will be set by specific implementations
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            LLMResponse with the generated content
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Check if the provider is accessible and configured correctly.
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        system_prompt: Optional[str] = None,
        max_retries: int = 3
    ) -> BaseModel:
        """
        Generate a structured response using the specified Pydantic model.
        
        Args:
            prompt: The user prompt
            response_model: Pydantic model for response structure
            system_prompt: Optional system prompt
            max_retries: Number of retries for validation
        
        Returns:
            Instance of response_model with parsed data
        """
        # Default implementation - specific providers can override
        for attempt in range(max_retries):
            try:
                response = await self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt or "You are a helpful assistant that outputs valid JSON.",
                    temperature=0.1  # Low temperature for structured output
                )
                
                # Try to parse the response as JSON
                import json
                data = json.loads(response.content)
                return response_model(**data)
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
        
        raise ValueError("Failed to generate structured response")