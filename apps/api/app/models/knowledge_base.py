from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from .base import BaseModel
import os

# Check if we're using PostgreSQL or SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = "postgresql" in DATABASE_URL

if USE_POSTGRES:
    from pgvector.sqlalchemy import Vector


class KnowledgeBaseEntry(BaseModel):
    __tablename__ = "knowledge_base_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False, index=True)  # e.g., 'MITRE_ATT&CK'
    technique_id = Column(String(50), index=True)
    content = Column(Text, nullable=False)
    
    # Use Vector for PostgreSQL, JSON for SQLite
    if USE_POSTGRES:
        embedding = Column(Vector(384))  # Dimension for 'all-MiniLM-L6-v2' model
    else:
        embedding = Column(JSON)  # Store as JSON array in SQLite


class CWEEntry(BaseModel):
    """
    Model for storing Common Weakness Enumeration (CWE) data with vector embeddings.
    Supports both PostgreSQL (with pgvector) and SQLite (with JSON embeddings).
    """
    __tablename__ = "cwe_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    cwe_id = Column(String(20), unique=True, nullable=False, index=True)  # e.g., 'CWE-89'
    name = Column(String(500), nullable=False, index=True)  # e.g., 'Improper Neutralization of Special Elements used in an SQL Command'
    description = Column(Text, nullable=False)  # Main description
    extended_description = Column(Text)  # Additional details if available
    
    # CWE-specific metadata
    weakness_abstraction = Column(String(50))  # Base, Variant, Class, Category
    status = Column(String(50))  # Draft, Incomplete, Stable, Deprecated
    likelihood_of_exploit = Column(String(20))  # High, Medium, Low
    
    # Component mapping hints for hybrid retrieval
    relevant_components = Column(JSON)  # ['web_service', 'database', 'api_gateway']
    
    # Use Vector for PostgreSQL, JSON for SQLite
    if USE_POSTGRES:
        embedding = Column(Vector(384))  # Dimension for 'all-MiniLM-L6-v2' model
    else:
        embedding = Column(JSON)  # Store as JSON array in SQLite
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    source_version = Column(String(50))  # Track CWE database version
    
    def __repr__(self):
        return f"<CWEEntry(cwe_id='{self.cwe_id}', name='{self.name[:50]}...')>"