"""
Database model for prompt versioning and management.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from .base import BaseModel


class Prompt(BaseModel):
    """Model for storing and versioning prompt templates."""
    
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)  # e.g., 'threat_generation'
    version = Column(Integer, nullable=False, default=1)
    template_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Ensure unique combination of name and version
    __table_args__ = (
        UniqueConstraint('name', 'version', name='_name_version_uc'),
    )