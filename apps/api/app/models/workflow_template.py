"""
Workflow Template Database Models

Defines database schema for admin-configurable workflow templates
that specify sequences of agent execution steps with automation rules.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from ..database import Base


class WorkflowTemplate(Base):
    """
    Admin-created workflow templates that define sequences of agent steps
    """
    __tablename__ = "workflow_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    version = Column(String(20), default="1.0.0")
    
    # Template configuration
    steps = Column(JSON, nullable=False)  # List of WorkflowStep configurations
    automation_settings = Column(JSON, default={})  # Global automation rules
    client_access_rules = Column(JSON, default={})  # Access control settings
    
    # Metadata
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship("WorkflowExecution", back_populates="template")


class WorkflowExecution(Base):
    """
    Individual workflow instances executing a template for specific clients
    """
    __tablename__ = "workflow_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey('workflow_templates.id'), nullable=False)
    
    # Client information
    client_id = Column(String(255))
    client_email = Column(String(255))
    client_organization = Column(String(255))
    
    # Execution state
    current_step = Column(Integer, default=0)
    status = Column(String(50), default='pending')  # pending, running, completed, failed, paused
    data = Column(JSON, default={})  # Workflow execution data and results
    
    # Automation overrides for this execution
    automation_overrides = Column(JSON, default={})
    
    # Tracking
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    template = relationship("WorkflowTemplate", back_populates="executions")
    step_executions = relationship("WorkflowStepExecution", back_populates="workflow_execution")


class WorkflowStepExecution(Base):
    """
    Individual step executions within a workflow
    """
    __tablename__ = "workflow_step_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey('workflow_executions.id'), nullable=False)
    
    # Step identification
    step_index = Column(Integer, nullable=False)
    step_name = Column(String(255), nullable=False)
    agent_name = Column(String(255))
    
    # Execution details
    status = Column(String(50), default='pending')  # pending, running, completed, failed, skipped, review_required
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})
    
    # Automation and review
    automated = Column(Boolean, default=False)
    confidence_score = Column(Float)
    requires_review = Column(Boolean, default=False)
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime)
    review_status = Column(String(50))  # approved, rejected, modified
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time_ms = Column(Integer)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    workflow_execution = relationship("WorkflowExecution", back_populates="step_executions")


# Pydantic models for API serialization

class WorkflowStepConfig(BaseModel):
    """Configuration for a single workflow step"""
    id: str
    name: str
    description: str
    agent_type: str
    required_inputs: List[str] = []
    optional_parameters: Dict[str, Any] = {}
    automation_enabled: bool = True
    confidence_threshold: float = 0.8
    review_required: bool = False
    timeout_minutes: int = 30
    retry_limit: int = 3


class AutomationSettings(BaseModel):
    """Global automation settings for a workflow"""
    enabled: bool = True
    confidence_threshold: float = 0.85
    max_auto_approvals_per_day: int = 50
    business_hours_only: bool = False
    notification_level: str = "summary"  # none, summary, detailed, realtime
    fallback_to_manual: bool = True


class ClientAccessRules(BaseModel):
    """Access control rules for client workflow execution"""
    authentication_method: str = "token"  # token, sso, both
    token_expiry_days: int = 30
    ip_restrictions: List[str] = []
    allowed_actions: List[str] = ["view", "edit", "export"]
    data_retention_days: int = 90
    requires_approval: bool = False


class WorkflowTemplateCreate(BaseModel):
    """Request model for creating workflow templates"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    steps: List[WorkflowStepConfig]
    automation_settings: AutomationSettings = AutomationSettings()
    client_access_rules: ClientAccessRules = ClientAccessRules()
    is_default: bool = False


class WorkflowTemplateUpdate(BaseModel):
    """Request model for updating workflow templates"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    steps: Optional[List[WorkflowStepConfig]] = None
    automation_settings: Optional[AutomationSettings] = None
    client_access_rules: Optional[ClientAccessRules] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class WorkflowExecutionCreate(BaseModel):
    """Request model for starting workflow execution"""
    template_id: str
    client_id: Optional[str] = None
    client_email: Optional[str] = None
    client_organization: Optional[str] = None
    automation_overrides: Dict[str, Any] = {}
    initial_data: Dict[str, Any] = {}


class WorkflowStepAction(BaseModel):
    """Request model for step actions (approve, reject, retry)"""
    action: str = Field(..., pattern="^(approve|reject|retry|skip)$")
    data: Dict[str, Any] = {}
    comment: Optional[str] = None