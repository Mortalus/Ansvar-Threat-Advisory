"""
Project and Session models for threat modeling pipeline.
Supports project management, session history, and session branching.
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class Project(Base):
    """
    A threat modeling project that can have multiple sessions.
    """
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)  # Future: user management
    
    # Project settings
    default_llm_provider = Column(String(50), nullable=True)
    tags = Column(Text, nullable=True)  # JSON string for categorizing projects
    
    # Relationships
    sessions = relationship("ProjectSession", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class ProjectSession(Base):
    """
    A session within a project. Supports branching and continuation.
    Each session represents a complete threat modeling pipeline run.
    """
    __tablename__ = "project_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    
    # Session identification
    name = Column(String(255), nullable=False)  # e.g., "Initial Analysis", "Updated with New Features"
    description = Column(Text, nullable=True)
    
    # Session branching
    parent_session_id = Column(String(36), ForeignKey("project_sessions.id"), nullable=True)
    branch_point = Column(String(50), nullable=True)  # Which step was branched from
    is_main_branch = Column(Boolean, default=True)
    
    # Pipeline data
    pipeline_id = Column(String(36), ForeignKey("pipelines.id"), nullable=True)
    
    # Session state
    status = Column(String(50), default="active")  # active, completed, archived
    completion_percentage = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Session metadata
    document_name = Column(String(255), nullable=True)
    document_size = Column(Integer, nullable=True)
    total_threats_found = Column(Integer, default=0)
    risk_level_summary = Column(Text, nullable=True)  # JSON string: {"Critical": 2, "High": 5, etc.}
    
    # Relationships
    project = relationship("Project", back_populates="sessions")
    pipeline = relationship("Pipeline", foreign_keys=[pipeline_id])
    parent_session = relationship("ProjectSession", remote_side=[id])
    child_sessions = relationship("ProjectSession", remote_side=[parent_session_id])
    
    def __repr__(self):
        return f"<ProjectSession(id={self.id}, name='{self.name}', project='{self.project.name if self.project else 'Unknown'}')>"
    
    @property
    def full_name(self):
        """Generate a full session name including branch info."""
        if self.parent_session:
            return f"{self.name} (branched from {self.parent_session.name})"
        return self.name
    
    @property
    def session_path(self):
        """Generate the full path from root to this session."""
        path = []
        current = self
        while current:
            path.insert(0, current.name)
            current = current.parent_session
        return " → ".join(path)


class SessionSnapshot(Base):
    """
    Snapshots of session data at different pipeline steps.
    Allows for detailed branching and rollback capabilities.
    """
    __tablename__ = "session_snapshots"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("project_sessions.id"), nullable=False)
    
    # Snapshot identification
    step_name = Column(String(50), nullable=False)  # dfd_extraction, threat_generation, etc.
    snapshot_name = Column(String(255), nullable=True)
    
    # Snapshot data
    pipeline_state = Column(Text, nullable=False)  # JSON string: Complete pipeline state at this step
    step_results = Column(Text, nullable=True)  # JSON string: Specific results from this step
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_action = Column(String(100), nullable=True)  # "auto_save", "manual_save", "branch_point"
    
    # Relationships
    session = relationship("ProjectSession", foreign_keys=[session_id])
    
    def __repr__(self):
        return f"<SessionSnapshot(id={self.id}, step='{self.step_name}', session='{self.session.name if self.session else 'Unknown'}')>"
