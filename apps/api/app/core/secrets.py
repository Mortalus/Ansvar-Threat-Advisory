"""
Secure secrets management for Docker and environment-based deployments.
Handles reading secrets from Docker secrets files or environment variables.
"""

import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def read_secret(secret_name: str, env_var_name: Optional[str] = None) -> Optional[str]:
    """
    Read a secret from Docker secrets or environment variables.
    
    Priority:
    1. Docker secrets file (/run/secrets/<secret_name>)
    2. Environment variable (env_var_name or secret_name)
    
    Args:
        secret_name: Name of the secret file in /run/secrets/
        env_var_name: Optional environment variable name (defaults to secret_name.upper())
    
    Returns:
        Secret value or None if not found
    """
    # Try Docker secrets first
    secrets_path = Path(f"/run/secrets/{secret_name}")
    if secrets_path.exists():
        try:
            secret_value = secrets_path.read_text().strip()
            if secret_value:
                logger.info(f"🔐 Secret '{secret_name}' loaded from Docker secrets")
                return secret_value
        except Exception as e:
            logger.warning(f"Failed to read Docker secret '{secret_name}': {e}")
    
    # Fall back to environment variable
    env_name = env_var_name or secret_name.upper()
    env_value = os.getenv(env_name)
    if env_value:
        logger.info(f"🔑 Secret '{secret_name}' loaded from environment variable '{env_name}'")
        return env_value
    
    logger.warning(f"⚠️ Secret '{secret_name}' not found in Docker secrets or environment")
    return None

def get_scaleway_api_key() -> Optional[str]:
    """Get Scaleway API key from secure storage"""
    return read_secret("scaleway_api_key", "SCALEWAY_API_KEY") or read_secret("scaleway_api_key", "SCW_API_KEY")

def get_azure_api_key() -> Optional[str]:
    """Get Azure OpenAI API key from secure storage"""
    return read_secret("azure_api_key", "AZURE_OPENAI_API_KEY")

def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from secure storage"""
    return read_secret("openai_api_key", "OPENAI_API_KEY")