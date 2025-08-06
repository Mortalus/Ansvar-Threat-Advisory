"""
Data ingestion service for populating the knowledge base with threat intelligence.
"""
import os
import json
import httpx
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import logging

from app.models.knowledge_base import KnowledgeBaseEntry
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Check if we're using PostgreSQL or SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = "postgresql" in DATABASE_URL


class IngestionService:
    """Service for ingesting and embedding threat intelligence data."""
    
    def __init__(self):
        # Initialize the sentence transformer model with error handling
        self.model = self._initialize_sentence_transformer()
    
    def _initialize_sentence_transformer(self):
        """Initialize SentenceTransformer with proper error handling."""
        try:
            # Try to initialize the model
            import os
            
            # Set cache directory with proper permissions
            cache_dir = os.getenv('SENTENCE_TRANSFORMERS_HOME', '/tmp/sentence_transformers_cache')
            os.makedirs(cache_dir, exist_ok=True)
            
            # Try to load the model
            model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=cache_dir)
            logger.info("Successfully initialized SentenceTransformer model")
            return model
            
        except Exception as e:
            logger.warning(f"Failed to initialize SentenceTransformer: {e}")
            logger.info("Creating mock embedder for development/testing")
            return MockEmbedder()

class MockEmbedder:
    """Mock embedder for when SentenceTransformer fails to initialize."""
    
    def encode(self, text):
        """Generate a simple mock embedding based on text hash."""
        import hashlib
        import numpy as np
        
        # Create a deterministic embedding from text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        # Convert hex to numbers and create 384-dimensional vector (same as all-MiniLM-L6-v2)
        embedding = []
        for i in range(0, len(text_hash), 2):
            # Convert hex pair to float between -1 and 1
            val = int(text_hash[i:i+2], 16) / 127.5 - 1.0
            embedding.append(val)
        
        # Pad or truncate to 384 dimensions
        while len(embedding) < 384:
            embedding.extend(embedding)
        embedding = embedding[:384]
        
        return np.array(embedding)
        
    async def ingest_from_url(self, url: str, source_name: str) -> Dict[str, Any]:
        """
        Ingest data from a URL, process it, and store in the knowledge base.
        
        Args:
            url: URL to fetch data from
            source_name: Name of the source (e.g., 'MITRE_ATT&CK', 'CISA_KEV')
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            # Fetch data from URL
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                data = response.json()
            
            # Process based on source type
            if source_name == "CISA_KEV":
                entries = await self._process_cisa_kev(data, source_name)
            elif source_name == "MITRE_ATT&CK":
                entries = await self._process_mitre_attack(data, source_name)
            else:
                # Generic processing for unknown sources
                entries = await self._process_generic(data, source_name)
            
            # Store entries in database
            async with AsyncSessionLocal() as session:
                # Clear existing entries for this source
                await session.execute(
                    delete(KnowledgeBaseEntry).where(
                        KnowledgeBaseEntry.source == source_name
                    )
                )
                
                # Add new entries
                for entry in entries:
                    session.add(entry)
                
                await session.commit()
            
            return {
                "status": "success",
                "source": source_name,
                "entries_processed": len(entries),
                "message": f"Successfully ingested {len(entries)} entries from {source_name}"
            }
            
        except Exception as e:
            logger.error(f"Error ingesting data from {url}: {str(e)}")
            return {
                "status": "error",
                "source": source_name,
                "message": f"Failed to ingest data: {str(e)}"
            }
    
    async def _process_cisa_kev(self, data: Dict, source_name: str) -> List[KnowledgeBaseEntry]:
        """Process CISA Known Exploited Vulnerabilities data."""
        entries = []
        
        vulnerabilities = data.get("vulnerabilities", [])
        for vuln in vulnerabilities:
            # Create searchable content from vulnerability data
            content = f"""
            CVE ID: {vuln.get('cveID', 'Unknown')}
            Vendor: {vuln.get('vendorProject', 'Unknown')}
            Product: {vuln.get('product', 'Unknown')}
            Vulnerability Name: {vuln.get('vulnerabilityName', 'Unknown')}
            Date Added: {vuln.get('dateAdded', 'Unknown')}
            Description: {vuln.get('shortDescription', 'Unknown')}
            Required Action: {vuln.get('requiredAction', 'Unknown')}
            Due Date: {vuln.get('dueDate', 'Unknown')}
            """
            
            # Generate embedding
            embedding = self.model.encode(content).tolist()
            
            # Create entry
            entry = KnowledgeBaseEntry(
                source=source_name,
                technique_id=vuln.get('cveID', 'Unknown'),
                content=content.strip(),
                embedding=embedding if not USE_POSTGRES else embedding  # JSON for SQLite, Vector for PostgreSQL
            )
            entries.append(entry)
        
        return entries
    
    async def _process_mitre_attack(self, data: Dict, source_name: str) -> List[KnowledgeBaseEntry]:
        """Process MITRE ATT&CK framework data."""
        entries = []
        
        # MITRE ATT&CK typically comes in STIX format
        objects = data.get("objects", [])
        for obj in objects:
            if obj.get("type") == "attack-pattern":
                # Create searchable content from technique
                content = f"""
                Technique: {obj.get('name', 'Unknown')}
                ID: {obj.get('external_references', [{}])[0].get('external_id', 'Unknown')}
                Description: {obj.get('description', 'Unknown')}
                Platforms: {', '.join(obj.get('x_mitre_platforms', []))}
                Tactics: {', '.join([phase.get('phase_name', '') for phase in obj.get('kill_chain_phases', [])])}
                """
                
                # Generate embedding
                embedding = self.model.encode(content).tolist()
                
                # Create entry
                entry = KnowledgeBaseEntry(
                    source=source_name,
                    technique_id=obj.get('external_references', [{}])[0].get('external_id', 'Unknown'),
                    content=content.strip(),
                    embedding=embedding
                )
                entries.append(entry)
        
        return entries
    
    async def _process_generic(self, data: Any, source_name: str) -> List[KnowledgeBaseEntry]:
        """Generic processing for unknown data formats."""
        entries = []
        
        # Convert data to string if not already
        if isinstance(data, dict):
            content = json.dumps(data, indent=2)
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                content = json.dumps(item, indent=2) if isinstance(item, dict) else str(item)
                
                # Generate embedding
                embedding = self.model.encode(content).tolist()
                
                # Create entry
                entry = KnowledgeBaseEntry(
                    source=source_name,
                    technique_id=f"{source_name}_{idx}",
                    content=content,
                    embedding=embedding
                )
                entries.append(entry)
        else:
            content = str(data)
            embedding = self.model.encode(content).tolist()
            
            entry = KnowledgeBaseEntry(
                source=source_name,
                technique_id=f"{source_name}_0",
                content=content,
                embedding=embedding
            )
            entries.append(entry)
        
        return entries
    
    async def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar entries in the knowledge base.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            List of similar entries with their content and scores
        """
        # Generate embedding for query
        query_embedding = self.model.encode(query).tolist()
        
        async with AsyncSessionLocal() as session:
            if USE_POSTGRES:
                # Use pgvector for similarity search
                from pgvector.sqlalchemy import Vector
                from sqlalchemy import func
                
                # Find similar entries using L2 distance
                stmt = (
                    select(KnowledgeBaseEntry)
                    .order_by(
                        KnowledgeBaseEntry.embedding.l2_distance(query_embedding)
                    )
                    .limit(limit)
                )
            else:
                # For SQLite, fetch all and compute similarity in Python
                stmt = select(KnowledgeBaseEntry)
            
            result = await session.execute(stmt)
            entries = result.scalars().all()
            
            if not USE_POSTGRES:
                # Compute cosine similarity for SQLite
                import numpy as np
                
                def cosine_similarity(a, b):
                    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                
                # Calculate similarities and sort
                similarities = []
                for entry in entries:
                    score = cosine_similarity(query_embedding, entry.embedding)
                    similarities.append((entry, score))
                
                # Sort by similarity and take top N
                similarities.sort(key=lambda x: x[1], reverse=True)
                entries = [entry for entry, _ in similarities[:limit]]
            
            # Convert to dictionaries
            results = []
            for entry in entries:
                results.append({
                    "id": entry.id,
                    "source": entry.source,
                    "technique_id": entry.technique_id,
                    "content": entry.content
                })
            
            return results