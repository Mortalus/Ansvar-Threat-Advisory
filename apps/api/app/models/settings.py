"""Database models for settings and prompt templates"""

from sqlalchemy import Column, String, Boolean, Text, DateTime, Index
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from app.database import Base

class SystemPromptTemplate(Base):
    """Database model for customizable system prompt templates"""
    __tablename__ = "system_prompt_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    step_name = Column(String(100), nullable=False, index=True)  # e.g., "threat_generation", "dfd_extraction"
    agent_type = Column(String(100), nullable=True, index=True)  # e.g., "architectural_risk", "business_financial" 
    system_prompt = Column(Text, nullable=False)  # The actual prompt text
    description = Column(Text, nullable=True)  # Human-readable description
    is_active = Column(Boolean, default=True, nullable=False)  # Whether this template is currently active
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Ensure only one active template per step/agent combination
    __table_args__ = (
        Index('ix_step_agent_active', 'step_name', 'agent_type', 'is_active'),
    )

# Pydantic models for API
class SystemPromptTemplateBase(BaseModel):
    step_name: str
    agent_type: Optional[str] = None
    system_prompt: str
    description: str
    is_active: bool = True

class SystemPromptTemplateCreate(SystemPromptTemplateBase):
    pass

class SystemPromptTemplateUpdate(BaseModel):
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class SystemPromptTemplateInDB(SystemPromptTemplateBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True