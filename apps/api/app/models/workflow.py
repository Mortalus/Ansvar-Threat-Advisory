"""
Workflow Engine Models

Provides modular workflow execution with versioned artifacts and DAG support.
Implements defensive programming patterns for enterprise robustness.
"""

import enum
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from sqlalchemy import (
    Column, String, Integer, ForeignKey, DateTime, Boolean, 
    Text, JSON, LargeBinary, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from .base import BaseModel
from .user import User


class WorkflowStatus(str, enum.Enum):
    """Workflow execution status with clear state transitions"""
    CREATED = "created"           # Initial state
    RUNNING = "running"           # Currently executing
    PAUSED = "paused"             # Temporarily halted by user
    COMPLETED = "completed"       # Successfully finished
    FAILED = "failed"             # Failed with unrecoverable error
    CANCELLED = "cancelled"       # User cancelled execution
    TIMEOUT = "timeout"           # Exceeded time limits


class StepStatus(str, enum.Enum):
    """Individual step execution status"""
    PENDING = "pending"           # Waiting to execute
    READY = "ready"               # Dependencies met, ready to run
    RUNNING = "running"           # Currently executing
    AWAITING_REVIEW = "awaiting_review"  # Needs manual review
    COMPLETED = "completed"       # Successfully finished
    FAILED = "failed"             # Failed execution
    SKIPPED = "skipped"           # Skipped due to conditions
    RETRYING = "retrying"         # In retry cycle


class WorkflowTemplate(BaseModel):
    """
    Workflow template defining reusable DAG structures.
    
    Only administrators can create/modify templates.
    Immutable after creation except via versioning.
    """
    __tablename__ = "workflow_templates"

    # Core identification
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    version = Column(String(50), nullable=False, default="1.0.0")
    
    # DAG definition stored as JSONB for performance and validation
    definition = Column(JSONB, nullable=False)
    
    # Metadata and constraints
    category = Column(String(100), index=True)  # e.g., "threat_modeling", "security_audit"
    tags = Column(JSONB)  # Array of searchable tags
    
    # Access control and lifecycle
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_template = Column(Boolean, default=False, nullable=False)  # Cannot be deleted
    
    # Performance and resource planning
    estimated_duration_minutes = Column(Integer)
    max_parallel_steps = Column(Integer, default=3)
    requires_review = Column(Boolean, default=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    runs = relationship("WorkflowRun", back_populates="template", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_template_name_version'),
        CheckConstraint('char_length(name) >= 3', name='chk_template_name_length'),
        CheckConstraint('max_parallel_steps > 0', name='chk_max_parallel_positive'),
        CheckConstraint('estimated_duration_minutes IS NULL OR estimated_duration_minutes > 0', 
                       name='chk_duration_positive'),
        Index('idx_template_active_category', 'is_active', 'category'),
    )
    
    @validates('definition')
    def validate_definition(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        """Defensive validation of workflow definition structure"""
        if not isinstance(value, dict):
            raise ValueError("Workflow definition must be a dictionary")
        
        if 'steps' not in value:
            raise ValueError("Workflow definition must contain 'steps' key")
        
        steps = value.get('steps', {})
        if not isinstance(steps, dict) or len(steps) == 0:
            raise ValueError("Steps must be a non-empty dictionary")
        
        # Validate each step has required fields
        for step_id, step_config in steps.items():
            if not isinstance(step_config, dict):
                raise ValueError(f"Step {step_id} configuration must be a dictionary")
            
            required_fields = ['agent_type']
            for field in required_fields:
                if field not in step_config:
                    raise ValueError(f"Step {step_id} missing required field: {field}")
            
            # Validate depends_on is a list if present
            if 'depends_on' in step_config and not isinstance(step_config['depends_on'], list):
                raise ValueError(f"Step {step_id} depends_on must be a list")
        
        return value
    
    @validates('name')
    def validate_name(self, key: str, value: str) -> str:
        """Validate template name"""
        if not value or len(value.strip()) < 3:
            raise ValueError("Template name must be at least 3 characters long")
        return value.strip()
    
    def __repr__(self):
        return f"<WorkflowTemplate(id={self.id}, name='{self.name}', version='{self.version}')>"


class WorkflowRun(BaseModel):
    """
    Individual execution of a workflow template.
    
    Maintains audit trail by storing template definition snapshot.
    Supports rollback and retry through versioned artifacts.
    """
    __tablename__ = "workflow_runs"

    # Core identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    run_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True, nullable=False)
    
    # Template relationship and snapshot
    template_id = Column(Integer, ForeignKey("workflow_templates.id"), nullable=False, index=True)
    template_version = Column(String(50), nullable=False)  # Snapshot for audit
    run_definition = Column(JSONB, nullable=False)  # Template definition at time of creation
    
    # Execution state
    status = Column(String(20), nullable=False, default=WorkflowStatus.CREATED, index=True)
    current_step_id = Column(String(100))  # Currently executing step
    
    # User context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Execution metadata
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    paused_at = Column(DateTime(timezone=True))
    
    # Error handling and diagnostics
    error_message = Column(Text)
    error_details = Column(JSONB)  # Stack traces, context
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Performance tracking
    total_steps = Column(Integer)
    completed_steps = Column(Integer, default=0, nullable=False)
    failed_steps = Column(Integer, default=0, nullable=False)
    
    # Configuration overrides
    auto_continue = Column(Boolean, default=False)  # Auto-run without manual review
    timeout_minutes = Column(Integer, default=240)  # 4 hour default timeout
    
    # Relationships
    template = relationship("WorkflowTemplate", back_populates="runs")
    user = relationship("User", foreign_keys=[user_id])
    artifacts = relationship("WorkflowArtifact", back_populates="run", cascade="all, delete-orphan")
    step_executions = relationship("WorkflowStepExecution", back_populates="run", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('created', 'running', 'paused', 'completed', 'failed', 'cancelled', 'timeout')", 
                       name='chk_valid_status'),
        CheckConstraint('retry_count >= 0', name='chk_retry_count_positive'),
        CheckConstraint('max_retries >= 0', name='chk_max_retries_positive'),
        CheckConstraint('total_steps IS NULL OR total_steps > 0', name='chk_total_steps_positive'),
        CheckConstraint('completed_steps >= 0', name='chk_completed_steps_positive'),
        CheckConstraint('failed_steps >= 0', name='chk_failed_steps_positive'),
        CheckConstraint('timeout_minutes > 0', name='chk_timeout_positive'),
        Index('idx_run_status_user', 'status', 'user_id'),
        Index('idx_run_template_status', 'template_id', 'status'),
    )
    
    @validates('status')
    def validate_status(self, key: str, value: str) -> str:
        """Validate status transitions"""
        if value not in [status.value for status in WorkflowStatus]:
            raise ValueError(f"Invalid workflow status: {value}")
        return value
    
    @validates('run_definition')
    def validate_run_definition(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        """Validate run definition structure"""
        if not isinstance(value, dict) or 'steps' not in value:
            raise ValueError("Run definition must contain steps")
        return value
    
    def is_active(self) -> bool:
        """Check if workflow is currently active"""
        return self.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]
    
    def is_terminal(self) -> bool:
        """Check if workflow is in a terminal state"""
        return self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, 
                              WorkflowStatus.CANCELLED, WorkflowStatus.TIMEOUT]
    
    def can_retry(self) -> bool:
        """Check if workflow can be retried"""
        return (self.status == WorkflowStatus.FAILED and 
                self.retry_count < self.max_retries)
    
    def get_progress_percentage(self) -> float:
        """Calculate completion percentage"""
        if not self.total_steps or self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100.0
    
    def __repr__(self):
        return f"<WorkflowRun(id={self.id}, run_id={self.run_id}, status='{self.status}')>"


class WorkflowStepExecution(BaseModel):
    """
    Individual step execution within a workflow run.
    
    Tracks step-level status, timing, and error details.
    Enables granular retry and rollback capabilities.
    """
    __tablename__ = "workflow_step_executions"

    # Core identification
    run_id = Column(Integer, ForeignKey("workflow_runs.id"), nullable=False, index=True)
    step_id = Column(String(100), nullable=False, index=True)  # Step identifier from definition
    step_name = Column(String(255))
    
    # Agent execution details
    agent_type = Column(String(100), nullable=False)
    agent_version = Column(String(50))
    
    # Execution state
    status = Column(String(20), nullable=False, default=StepStatus.PENDING, index=True)
    execution_order = Column(Integer)  # Order in execution sequence
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSONB)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Input/Output tracking
    input_artifacts = Column(JSONB)  # List of artifact IDs used as input
    output_artifacts = Column(JSONB)  # List of artifact IDs produced
    
    # Configuration
    prompt_override = Column(Text)  # User-provided prompt override
    configuration = Column(JSONB)   # Step-specific configuration
    
    # Relationships
    run = relationship("WorkflowRun", back_populates="step_executions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('run_id', 'step_id', name='uq_run_step'),
        CheckConstraint("status IN ('pending', 'ready', 'running', 'awaiting_review', 'completed', 'failed', 'skipped', 'retrying')", 
                       name='chk_valid_step_status'),
        CheckConstraint('retry_count >= 0', name='chk_step_retry_count_positive'),
        CheckConstraint('duration_seconds IS NULL OR duration_seconds >= 0', name='chk_duration_positive'),
        Index('idx_step_run_status', 'run_id', 'status'),
        Index('idx_step_agent_type', 'agent_type'),
    )
    
    @validates('status')
    def validate_status(self, key: str, value: str) -> str:
        """Validate step status"""
        if value not in [status.value for status in StepStatus]:
            raise ValueError(f"Invalid step status: {value}")
        return value
    
    def is_terminal(self) -> bool:
        """Check if step is in terminal state"""
        return self.status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]
    
    def can_retry(self) -> bool:
        """Check if step can be retried"""
        return self.status == StepStatus.FAILED
    
    def __repr__(self):
        return f"<WorkflowStepExecution(id={self.id}, step_id='{self.step_id}', status='{self.status}')>"


class WorkflowArtifact(BaseModel):
    """
    Versioned artifacts produced by workflow steps.
    
    Enables rollback, retry, and audit capabilities.
    Supports both JSON and binary data storage.
    """
    __tablename__ = "workflow_artifacts"

    # Core identification
    run_id = Column(Integer, ForeignKey("workflow_runs.id"), nullable=False, index=True)
    producing_step_id = Column(String(100), nullable=False, index=True)
    
    # Artifact metadata
    name = Column(String(255), nullable=False, index=True)  # e.g., "cleaned_text", "threats"
    artifact_type = Column(String(100), nullable=False, index=True)  # e.g., "text", "json", "binary"
    description = Column(Text)
    
    # Versioning
    version = Column(Integer, nullable=False, default=1)
    is_latest = Column(Boolean, default=True, nullable=False, index=True)
    
    # Content storage (mutually exclusive)
    content_json = Column(JSONB)      # For structured data
    content_text = Column(Text)       # For text data
    content_binary = Column(LargeBinary)  # For binary data
    
    # Metadata
    size_bytes = Column(Integer)
    content_hash = Column(String(64))  # SHA-256 for integrity
    mime_type = Column(String(100))
    
    # Lifecycle
    expires_at = Column(DateTime(timezone=True))  # Optional expiration
    is_sensitive = Column(Boolean, default=False)  # PII/sensitive data flag
    
    # Relationships
    run = relationship("WorkflowRun", back_populates="artifacts")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('run_id', 'name', 'version', name='uq_artifact_version'),
        CheckConstraint('version > 0', name='chk_version_positive'),
        CheckConstraint('size_bytes IS NULL OR size_bytes >= 0', name='chk_size_positive'),
        CheckConstraint('char_length(name) >= 1', name='chk_artifact_name_length'),
        # Ensure only one content field is used
        CheckConstraint(
            '(content_json IS NOT NULL)::int + (content_text IS NOT NULL)::int + (content_binary IS NOT NULL)::int = 1',
            name='chk_single_content_type'
        ),
        Index('idx_artifact_run_name_latest', 'run_id', 'name', 'is_latest'),
        Index('idx_artifact_type_step', 'artifact_type', 'producing_step_id'),
    )
    
    @validates('name')
    def validate_name(self, key: str, value: str) -> str:
        """Validate artifact name"""
        if not value or len(value.strip()) == 0:
            raise ValueError("Artifact name cannot be empty")
        return value.strip()
    
    @validates('artifact_type')
    def validate_artifact_type(self, key: str, value: str) -> str:
        """Validate artifact type"""
        allowed_types = ['text', 'json', 'binary', 'image', 'document']
        if value not in allowed_types:
            raise ValueError(f"Artifact type must be one of: {allowed_types}")
        return value
    
    def get_content(self) -> Any:
        """Get the appropriate content based on type"""
        if self.content_json is not None:
            return self.content_json
        elif self.content_text is not None:
            return self.content_text
        elif self.content_binary is not None:
            return self.content_binary
        return None
    
    def set_content(self, content: Any, content_type: str = None) -> None:
        """Set content with automatic type detection"""
        # Clear all content fields first
        self.content_json = None
        self.content_text = None
        self.content_binary = None
        
        if isinstance(content, (dict, list)):
            self.content_json = content
            self.artifact_type = content_type or 'json'
        elif isinstance(content, str):
            self.content_text = content
            self.artifact_type = content_type or 'text'
        elif isinstance(content, bytes):
            self.content_binary = content
            self.artifact_type = content_type or 'binary'
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")
        
        # Update size
        if self.content_text:
            self.size_bytes = len(self.content_text.encode('utf-8'))
        elif self.content_binary:
            self.size_bytes = len(self.content_binary)
        else:
            import json
            self.size_bytes = len(json.dumps(self.content_json).encode('utf-8'))
    
    def is_expired(self) -> bool:
        """Check if artifact has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
    
    def __repr__(self):
        return f"<WorkflowArtifact(id={self.id}, name='{self.name}', version={self.version}, latest={self.is_latest})>"


# Add workflow permissions to the existing PermissionType enum (this would be added to rbac.py)
class WorkflowPermissionType(str, enum.Enum):
    """Additional permissions for workflow engine"""
    # Template Management (Admin only)
    WORKFLOW_TEMPLATE_CREATE = "workflow_template:create"
    WORKFLOW_TEMPLATE_VIEW = "workflow_template:view"
    WORKFLOW_TEMPLATE_EDIT = "workflow_template:edit"
    WORKFLOW_TEMPLATE_DELETE = "workflow_template:delete"
    
    # Workflow Execution (Users)
    WORKFLOW_RUN_CREATE = "workflow_run:create"
    WORKFLOW_RUN_VIEW = "workflow_run:view"
    WORKFLOW_RUN_CONTROL = "workflow_run:control"  # Start/stop/pause
    WORKFLOW_RUN_DELETE = "workflow_run:delete"
    
    # Artifact Access
    WORKFLOW_ARTIFACT_VIEW = "workflow_artifact:view"
    WORKFLOW_ARTIFACT_DOWNLOAD = "workflow_artifact:download"