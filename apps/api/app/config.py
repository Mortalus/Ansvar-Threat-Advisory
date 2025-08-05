from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
from functools import lru_cache
import os

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    
    # File Upload
    max_file_size_mb: int = 10
    allowed_extensions: list[str] = ["pdf", "docx", "txt"]
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # LLM General Settings
    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    
    # Azure OpenAI Configuration
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2024-02-15-preview"
    
    # Scaleway Configuration
    scaleway_api_key: Optional[str] = None
    scaleway_endpoint: str = "https://api.scaleway.ai/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_step_config(self, step_num: int) -> Dict[str, Any]:
        """Get configuration for a specific pipeline step"""
        provider = os.getenv(f"STEP{step_num}_LLM_PROVIDER", "ollama")
        
        config = {
            "provider": provider,
            "temperature": self.default_temperature,
            "max_tokens": self.default_max_tokens
        }
        
        if provider == "ollama":
            config["model"] = os.getenv(f"STEP{step_num}_OLLAMA_MODEL", "llama2")
            config["base_url"] = self.ollama_base_url
        elif provider == "azure":
            config["model"] = os.getenv(f"STEP{step_num}_AZURE_MODEL", "gpt-4")
            config["api_key"] = self.azure_openai_api_key
            config["endpoint"] = self.azure_openai_endpoint
            config["api_version"] = self.azure_openai_api_version
        elif provider == "scaleway":
            config["model"] = os.getenv(f"STEP{step_num}_SCALEWAY_MODEL", "llama-3.1-70b")
            config["api_key"] = self.scaleway_api_key
            config["endpoint"] = self.scaleway_endpoint
            
        return config

@lru_cache()
def get_settings():
    return Settings()