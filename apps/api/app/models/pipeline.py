"""Pipeline models for storing threat modeling pipeline data"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
import uuid
import enum
from .base import BaseModel

class PipelineStatus(str, enum.Enum):
    """Pipeline status enumeration"""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(str, enum.Enum):
    """Pipeline step status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class Pipeline(BaseModel):
    """Main pipeline model representing a complete threat modeling session"""
    __tablename__ = "pipelines"
    
    # Unique pipeline identifier
    pipeline_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Pipeline metadata
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(PipelineStatus), default=PipelineStatus.CREATED, nullable=False)
    
    # Document information
    document_text = Column(Text, nullable=True)
    document_files = Column(JSON, nullable=True)  # List of uploaded file info
    text_length = Column(Integer, nullable=True)
    
    # Pipeline results (stored as JSON/JSONB)
    extracted_security_data = Column(JSON, nullable=True)  # STRIDE-focused extracted data
    extraction_metadata = Column(JSON, nullable=True)     # Extraction process metadata
    dfd_components = Column(JSON, nullable=True)
    dfd_validation = Column(JSON, nullable=True)
    threats = Column(JSON, nullable=True)
    refined_threats = Column(JSON, nullable=True)
    attack_paths = Column(JSON, nullable=True)
    
    # Timing information
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Owner relationship (for future multi-user support)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="pipelines")
    
    # Multi-tenancy support for client data segregation
    client_id = Column(String(100), nullable=True, index=True)  # Links to external client organization
    
    # Pipeline steps relationship
    steps = relationship("PipelineStep", back_populates="pipeline", cascade="all, delete-orphan", order_by="PipelineStep.step_number")
    
    def __repr__(self):
        return f"<Pipeline(id={self.id}, pipeline_id='{self.pipeline_id}', status='{self.status}')>"

class PipelineStep(BaseModel):
    """Individual pipeline step model"""
    __tablename__ = "pipeline_steps"
    
    # Step identification
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    step_name = Column(String(100), nullable=False)  # e.g., 'document_upload', 'dfd_extraction'
    step_number = Column(Integer, nullable=False)  # Order of execution
    
    # Step status and timing
    status = Column(Enum(StepStatus), default=StepStatus.PENDING, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Step configuration (LLM provider, model, etc.)
    config = Column(JSON, nullable=True)
    
    # Relationships
    pipeline = relationship("Pipeline", back_populates="steps")
    results = relationship("PipelineStepResult", back_populates="step", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PipelineStep(id={self.id}, step_name='{self.step_name}', status='{self.status}')>"

class PipelineStepResult(BaseModel):
    """Results and outputs from individual pipeline steps"""
    __tablename__ = "pipeline_step_results"
    
    # Step relationship
    step_id = Column(Integer, ForeignKey("pipeline_steps.id"), nullable=False)
    
    # Result data
    result_type = Column(String(50), nullable=False)  # e.g., 'dfd_components', 'threats', 'validation'
    result_data = Column(JSON, nullable=False)  # The actual result data
    
    # Metadata
    processing_time_seconds = Column(Integer, nullable=True)
    llm_provider = Column(String(50), nullable=True)
    llm_model = Column(String(100), nullable=True)
    token_usage = Column(JSON, nullable=True)  # Track token consumption
    
    # Versioning fields
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=True)
    embedding_model = Column(String(100), nullable=True)  # For RAG steps
    
    # Quality metrics
    confidence_score = Column(Integer, nullable=True)  # 0-100
    validation_passed = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    step = relationship("PipelineStep", back_populates="results")
    
    def __repr__(self):
        return f"<PipelineStepResult(id={self.id}, result_type='{self.result_type}')>"