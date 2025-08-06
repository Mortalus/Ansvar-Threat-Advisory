from sqlalchemy import Column, Integer, String, Text, JSON
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