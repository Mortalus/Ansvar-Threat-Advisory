"""
Database model for capturing user feedback on generated threats.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import BaseModel


class ValidationAction(str, enum.Enum):
    """Actions that users can take on generated threats."""
    ACCEPTED = "accepted"
    EDITED = "edited"
    DELETED = "deleted"


class ThreatFeedback(BaseModel):
    """Model for storing user feedback on generated threats."""
    
    __tablename__ = "threat_feedback"
    
    # Threat identification
    threat_id = Column(String(100), nullable=False, index=True)  # ID of the threat being validated
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    
    # Validation action
    action = Column(SQLEnum(ValidationAction), nullable=False)
    
    # Edited content (if action is EDITED)
    edited_content = Column(Text, nullable=True)
    
    # Original threat data (for reference)
    original_threat = Column(Text, nullable=False)  # JSON string of original threat
    
    # User who provided feedback (nullable for now, until auth is implemented)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Feedback metadata
    feedback_reason = Column(Text, nullable=True)  # Optional reason for the action
    confidence_rating = Column(Integer, nullable=True)  # User's confidence in the threat (1-5)
    
    # Timing
    feedback_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    pipeline = relationship("Pipeline", backref="threat_feedback")
    user = relationship("User", backref="threat_feedback")
    
    def __repr__(self):
        return f"<ThreatFeedback(threat_id='{self.threat_id}', action='{self.action}')>"