"""
Data ingestion service for populating the knowledge base with threat intelligence.
"""
import os
import json
import xml.etree.ElementTree as ET
import httpx
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import logging

from app.models.knowledge_base import KnowledgeBaseEntry, CWEEntry
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Check if we're using PostgreSQL or SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = "postgresql" in DATABASE_URL


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


class IngestionService:
    """Service for ingesting and embedding threat intelligence data."""
    
    def __init__(self):
        # Initialize the sentence transformer model with error handling
        self.model = self._initialize_sentence_transformer()
    
    def _initialize_sentence_transformer(self):
        """Initialize SentenceTransformer with proper error handling."""
        try:
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

    # Component type to CWE mapping for hybrid retrieval
    COMPONENT_CWE_MAPPING = {
        'web_service': [79, 89, 200, 352, 862, 918, 942],  # XSS, SQLi, Info Disclosure, CSRF, Missing Auth, SSRF, CORS
        'database': [89, 200, 732, 284, 319, 327],         # SQLi, Info Disclosure, Permissions, Access Control, Cleartext, Crypto
        'api_gateway': [352, 863, 918, 942, 287, 209],     # CSRF, Auth Bypass, SSRF, CORS, Authentication, Info Exposure
        'authentication': [287, 306, 798, 863, 284],       # Authentication, Missing Auth, Weak Creds, Auth Bypass, Access Control
        'data_store': [200, 732, 319, 327, 264],          # Info Disclosure, Permissions, Cleartext, Broken Crypto, Time-of-check
        'external_entity': [20, 918, 346, 770],           # Path Traversal, SSRF, Origin Validation, Missing Certs
        'process': [94, 77, 78, 502, 269],                # Code Injection, Command Injection, OS Command, Deserialization, Privilege Management
        'trust_boundary': [284, 346, 350, 441],           # Access Control, Origin Validation, Host Validation, Web Parameter Tampering
        'default': [79, 89, 200, 287, 352, 863]           # Common web vulnerabilities
    }

    async def ingest_cwe_from_xml(self, xml_file_path: str = None, xml_url: str = None) -> Dict[str, Any]:
        """
        Ingest CWE data from XML file or URL and store in database with error handling.
        
        Args:
            xml_file_path: Path to local CWE XML file
            xml_url: URL to download CWE XML from (default: official MITRE CWE)
            
        Returns:
            Dictionary with ingestion results
        """
        default_cwe_url = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"
        
        try:
            # Get XML content
            if xml_file_path and os.path.exists(xml_file_path):
                logger.info(f"Reading CWE data from local file: {xml_file_path}")
                with open(xml_file_path, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
            else:
                # Download from URL
                url = xml_url or default_cwe_url
                logger.info(f"Downloading CWE data from: {url}")
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    # Handle ZIP file
                    if url.endswith('.zip'):
                        import zipfile
                        import io
                        
                        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                            # Find the XML file in the ZIP
                            xml_files = [name for name in zip_file.namelist() if name.endswith('.xml')]
                            if not xml_files:
                                raise Exception("No XML file found in ZIP archive")
                            
                            xml_content = zip_file.read(xml_files[0]).decode('utf-8')
                    else:
                        xml_content = response.text
            
            # Parse XML
            logger.info("Parsing CWE XML data...")
            root = ET.fromstring(xml_content)
            
            # Find namespace
            namespace = {'cwe': 'http://cwe.mitre.org/cwe-6'}
            if not root.tag.startswith('{'):
                namespace = {}  # No namespace
            
            # Extract CWE entries
            entries = await self._process_cwe_xml(root, namespace)
            
            # Store in database with error handling
            async with AsyncSessionLocal() as session:
                try:
                    # Clear existing CWE entries
                    await session.execute(delete(CWEEntry))
                    logger.info("Cleared existing CWE entries")
                    
                    # Add new entries in batches
                    batch_size = 100
                    total_entries = len(entries)
                    
                    for i in range(0, total_entries, batch_size):
                        batch = entries[i:i + batch_size]
                        for entry in batch:
                            session.add(entry)
                        
                        await session.commit()
                        logger.info(f"Committed batch {i//batch_size + 1}: {len(batch)} entries")
                    
                    logger.info(f"Successfully stored {total_entries} CWE entries")
                    
                except Exception as db_error:
                    await session.rollback()
                    logger.error(f"Database error during CWE ingestion: {db_error}")
                    raise
            
            return {
                "status": "success",
                "source": "CWE",
                "entries_processed": len(entries),
                "message": f"Successfully ingested {len(entries)} CWE entries",
                "source_version": root.get("Version", "unknown")
            }
            
        except Exception as e:
            error_msg = f"Error ingesting CWE data: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "source": "CWE", 
                "message": error_msg,
                "entries_processed": 0
            }
    
    async def _process_cwe_xml(self, root: ET.Element, namespace: Dict[str, str]) -> List[CWEEntry]:
        """Process CWE XML and create CWEEntry objects with error handling."""
        entries = []
        
        # Find weakness elements
        weakness_xpath = ".//cwe:Weakness" if namespace else ".//Weakness"
        weaknesses = root.findall(weakness_xpath, namespace)
        
        logger.info(f"Found {len(weaknesses)} CWE weaknesses to process")
        
        for weakness in weaknesses:
            try:
                cwe_id = weakness.get('ID')
                if not cwe_id:
                    continue
                
                name = weakness.get('Name', '')
                abstraction = weakness.get('Abstraction', '')
                status = weakness.get('Status', '')
                
                # Get description
                description = ""
                desc_elem = weakness.find('cwe:Description' if namespace else 'Description', namespace)
                if desc_elem is not None:
                    description = desc_elem.text or ""
                
                # Get extended description
                extended_desc = ""
                ext_desc_elem = weakness.find('cwe:Extended_Description' if namespace else 'Extended_Description', namespace)
                if ext_desc_elem is not None:
                    extended_desc = ext_desc_elem.text or ""
                
                # Get likelihood of exploit
                likelihood = ""
                likelihood_elem = weakness.find('cwe:Likelihood_Of_Exploit' if namespace else 'Likelihood_Of_Exploit', namespace)
                if likelihood_elem is not None:
                    likelihood = likelihood_elem.text or ""
                
                # Determine relevant components based on CWE patterns
                relevant_components = self._determine_relevant_components(name, description, cwe_id)
                
                # Create content for embedding
                content = f"""
                CWE-{cwe_id}: {name}
                Abstraction: {abstraction}
                Status: {status}
                Description: {description}
                Extended Description: {extended_desc}
                Likelihood of Exploit: {likelihood}
                Relevant Components: {', '.join(relevant_components)}
                """.strip()
                
                # Generate embedding with error handling
                try:
                    embedding = self.model.encode(content).tolist()
                except Exception as embed_error:
                    logger.warning(f"Failed to generate embedding for CWE-{cwe_id}: {embed_error}")
                    embedding = [0.0] * 384  # Fallback embedding
                
                # Create CWE entry
                entry = CWEEntry(
                    cwe_id=f"CWE-{cwe_id}",
                    name=name,
                    description=description,
                    extended_description=extended_desc,
                    weakness_abstraction=abstraction,
                    status=status,
                    likelihood_of_exploit=likelihood,
                    relevant_components=relevant_components,
                    embedding=embedding,
                    source_version=root.get("Version", "unknown")
                )
                
                entries.append(entry)
                
            except Exception as e:
                logger.warning(f"Error processing CWE weakness {weakness.get('ID', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(entries)} CWE entries")
        return entries
    
    def _determine_relevant_components(self, name: str, description: str, cwe_id: str) -> List[str]:
        """Determine which component types this CWE is relevant for."""
        relevant = []
        name_lower = name.lower()
        desc_lower = description.lower()
        combined = f"{name_lower} {desc_lower}"
        
        # Web service indicators
        if any(term in combined for term in ['web', 'http', 'url', 'cross-site', 'xss', 'csrf', 'cors']):
            relevant.append('web_service')
        
        # Database indicators  
        if any(term in combined for term in ['sql', 'database', 'query', 'injection']):
            relevant.append('database')
        
        # API indicators
        if any(term in combined for term in ['api', 'rest', 'endpoint', 'service']):
            relevant.append('api_gateway')
        
        # Authentication indicators
        if any(term in combined for term in ['auth', 'login', 'credential', 'password', 'session']):
            relevant.append('authentication')
        
        # Data storage indicators
        if any(term in combined for term in ['file', 'data', 'storage', 'cache', 'store']):
            relevant.append('data_store')
        
        # Process indicators
        if any(term in combined for term in ['process', 'execution', 'command', 'code']):
            relevant.append('process')
        
        # Trust boundary indicators
        if any(term in combined for term in ['boundary', 'network', 'access control', 'permission']):
            relevant.append('trust_boundary')
        
        # Default to common components if no specific match
        if not relevant:
            relevant.append('default')
        
        return relevant

    async def get_relevant_cwe_entries(self, component_type: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant CWE entries for a component type using hybrid approach.
        
        Args:
            component_type: Type of component (e.g., 'web_service', 'database')
            query: Search query for semantic similarity
            limit: Maximum number of results
            
        Returns:
            List of relevant CWE entries with metadata
        """
        try:
            # Get relevant CWE IDs for component type
            relevant_cwe_ids = self.COMPONENT_CWE_MAPPING.get(component_type, self.COMPONENT_CWE_MAPPING['default'])
            
            # Generate query embedding
            query_embedding = self.model.encode(query).tolist()
            
            async with AsyncSessionLocal() as session:
                if USE_POSTGRES:
                    # Use pgvector for hybrid search
                    from pgvector.sqlalchemy import Vector
                    from sqlalchemy import func, and_, or_
                    
                    # Create CWE ID filters
                    cwe_filters = [CWEEntry.cwe_id == f"CWE-{cwe_id}" for cwe_id in relevant_cwe_ids]
                    
                    stmt = (
                        select(CWEEntry)
                        .where(or_(*cwe_filters))
                        .order_by(CWEEntry.embedding.l2_distance(query_embedding))
                        .limit(limit)
                    )
                else:
                    # SQLite fallback
                    from sqlalchemy import or_
                    
                    cwe_filters = [CWEEntry.cwe_id == f"CWE-{cwe_id}" for cwe_id in relevant_cwe_ids]
                    stmt = (
                        select(CWEEntry)
                        .where(or_(*cwe_filters))
                    )
                
                result = await session.execute(stmt)
                entries = result.scalars().all()
                
                if not USE_POSTGRES and entries:
                    # Compute cosine similarity for SQLite
                    import numpy as np
                    
                    def cosine_similarity(a, b):
                        try:
                            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                        except:
                            return 0.0
                    
                    # Calculate similarities and sort
                    similarities = []
                    for entry in entries:
                        try:
                            score = cosine_similarity(query_embedding, entry.embedding)
                            similarities.append((entry, score))
                        except:
                            similarities.append((entry, 0.0))
                    
                    # Sort by similarity and take top N
                    similarities.sort(key=lambda x: x[1], reverse=True)
                    entries = [entry for entry, _ in similarities[:limit]]
                
                # Convert to dictionaries
                results = []
                for entry in entries:
                    results.append({
                        "cwe_id": entry.cwe_id,
                        "name": entry.name,
                        "description": entry.description,
                        "weakness_abstraction": entry.weakness_abstraction,
                        "likelihood_of_exploit": entry.likelihood_of_exploit,
                        "relevant_components": entry.relevant_components
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error retrieving relevant CWE entries: {e}")
            return []

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
                embedding=embedding
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