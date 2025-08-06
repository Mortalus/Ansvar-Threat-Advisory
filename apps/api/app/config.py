"""Application configuration"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings with flexible configuration"""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_env: str = "development"
    environment: str = "development"  # Alternative name
    log_level: str = "INFO"
    
    # CORS - Extremely permissive for Docker deployment
    frontend_url: str = "http://localhost:3001"
    cors_origins: str = "*"  # Allow all origins for Docker deployment
    
    # Redis (for caching and Celery)
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 3600
    
    # Database 
    database_url: Optional[str] = None
    database_max_connections: int = 20
    database_ssl_require: bool = False
    
    # File Upload
    max_file_size_mb: int = 10
    allowed_file_types: str = "application/pdf,text/plain,text/markdown"
    allowed_extensions: str = "pdf,docx,txt"
    
    # Pipeline
    pipeline_timeout_seconds: int = 300
    max_concurrent_pipelines: int = 10
    
    # LLM Configuration
    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    
    # LLM Providers per step
    step1_llm_provider: str = "scaleway"
    step2_llm_provider: str = "scaleway"
    step3_llm_provider: str = "azure"
    step4_llm_provider: str = "azure"
    step5_llm_provider: str = "scaleway"
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    step1_ollama_model: str = "llama3:8b"
    step2_ollama_model: str = "llama3:8b"
    step3_ollama_model: str = "llama3:8b"
    step4_ollama_model: str = "llama3:8b"
    step5_ollama_model: str = "llama3:8b"
    
    # Azure OpenAI Configuration
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2024-02-15-preview"
    step1_azure_model: str = "gpt-4"
    step2_azure_model: str = "gpt-4"
    step3_azure_model: str = "gpt-4"
    step4_azure_model: str = "gpt-4"
    step5_azure_model: str = "gpt-4"
    
    # Scaleway Configuration
    scaleway_api_key: Optional[str] = None
    scw_api_key: Optional[str] = None  # Alternative env var
    scaleway_endpoint: str = "https://api.scaleway.ai/v1"
    step1_scaleway_model: str = "llama-3.3-70b-instruct"
    step2_scaleway_model: str = "llama-3.3-70b-instruct"
    step3_scaleway_model: str = "llama-3.3-70b-instruct"
    step4_scaleway_model: str = "llama-3.3-70b-instruct"
    step5_scaleway_model: str = "llama-3.3-70b-instruct"
    
    # Security
    secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow extra fields to prevent validation errors
        extra = "ignore"

# Create settings instance
settings = Settings()

# Handle alternative Scaleway API key
if not settings.scaleway_api_key and settings.scw_api_key:
    settings.scaleway_api_key = settings.scw_api_key

# Parse CORS origins if needed
def get_cors_origins():
    """Get CORS origins as a list"""
    if settings.cors_origins == "*":
        return ["*"]  # Allow all origins
    origins = settings.cors_origins.split(',')
    return [origin.strip() for origin in origins]