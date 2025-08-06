# RAG-Powered Threat Modeling Implementation

## 🎯 Overview

This document describes the implementation of a **Retrieval-Augmented Generation (RAG) pipeline** for the Threat Modeling application, transforming it from a simple LLM-powered tool into an intelligent system that grounds its threat analysis in real threat intelligence data.

## 🏗️ Architecture

### Phase 1: RAG Pipeline
- **pgvector Database**: Vector storage for threat intelligence embeddings
- **Knowledge Base**: Ingestion service for threat intelligence (CISA KEV, MITRE ATT&CK)
- **Vector Search**: Similarity search to find relevant threat context
- **Enhanced Threat Generation**: LLM generation augmented with retrieved threat intelligence

### Phase 2: Model & Prompt Versioning  
- **Prompt Management**: Versioned prompt templates for reproducible results
- **Model Tracking**: Track which models and prompts were used for each result
- **Version Control**: Full traceability of AI-generated content

### Phase 3: Human Feedback Loop
- **Feedback Collection**: Capture user validation of generated threats
- **Action Tracking**: Record ACCEPTED, EDITED, or DELETED actions
- **Continuous Improvement**: Build dataset for future model fine-tuning

## 📊 Database Schema

### New Tables

#### `knowledge_base_entries`
Stores threat intelligence data with vector embeddings:
```sql
- id (Primary Key)
- source (CISA_KEV, MITRE_ATT&CK, etc.)
- technique_id (CVE-ID, ATT&CK Technique ID)
- content (Searchable text content)
- embedding (Vector[384] for pgvector, JSON for SQLite)
- created_at, updated_at
```

#### `prompts`
Versioned prompt templates:
```sql
- id (Primary Key)
- name (threat_generation, dfd_extraction, etc.)
- version (Integer, auto-incremented per name)
- template_text (Prompt template with placeholders)
- is_active (Boolean, only one active per name)
- created_at, updated_at
```

#### `threat_feedback`
Human feedback on generated threats:
```sql
- id (Primary Key)
- threat_id (Reference to generated threat)
- pipeline_id (Foreign Key to pipelines table)
- action (ACCEPTED, EDITED, DELETED)
- edited_content (If action=EDITED)
- original_threat (JSON of original threat)
- feedback_reason (Optional explanation)
- confidence_rating (1-5 scale)
- user_id (For future auth implementation)
- feedback_at (Timestamp)
```

#### Enhanced `pipeline_step_results`
Added versioning fields:
```sql
- prompt_id (Foreign Key to prompts table)
- embedding_model (Model used for embeddings)
- llm_model (LLM model used)
```

## 🔄 RAG Workflow

### 1. Knowledge Base Ingestion
```python
# Automatic daily updates via Celery Beat
POST /api/knowledge-base/initialize-default
POST /api/knowledge-base/ingest
{
  "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
  "source_name": "CISA_KEV"
}
```

### 2. Threat Generation with RAG
```python
# Enhanced pipeline step execution
1. Extract DFD components from document
2. For each component:
   a. Formulate search query based on component type and description
   b. Search knowledge base using vector similarity (top 5 results)
   c. Retrieve active prompt template from database
   d. Build augmented prompt with component info + threat intelligence context
   e. Generate threats using LLM with retrieved context
   f. Store results with versioning metadata
```

### 3. Human Feedback Collection
```python
# Submit feedback on generated threats
POST /api/threats/{threat_id}/feedback?pipeline_id={pipeline_id}
{
  "action": "EDITED",
  "edited_content": "More specific threat description...",
  "feedback_reason": "Original was too generic",
  "confidence_rating": 4,
  "original_threat": {...}
}
```

## 🚀 API Endpoints

### Knowledge Base Management
- `POST /api/knowledge-base/ingest` - Trigger data ingestion
- `POST /api/knowledge-base/search` - Search for similar content
- `GET /api/knowledge-base/stats` - Get knowledge base statistics
- `POST /api/knowledge-base/initialize-default` - Load default sources
- `DELETE /api/knowledge-base/source/{name}` - Remove source data

### Threat Feedback
- `POST /api/threats/{threat_id}/feedback` - Submit threat validation
- `GET /api/threats/{threat_id}/feedback` - Get feedback history
- `GET /api/threats/pipeline/{pipeline_id}/feedback` - Get all pipeline feedback
- `GET /api/threats/feedback/stats` - Aggregated feedback statistics

### Background Tasks (Enhanced)
- `POST /api/tasks/execute-step` - Queue pipeline steps with RAG
- `GET /api/tasks/status/{task_id}` - Monitor ingestion progress

## 🧪 Testing & Validation

### Running Tests
```bash
cd apps/api
source venv/bin/activate
python test_rag_implementation.py
```

### API Demo
```bash
cd apps/api
python example_api_usage.py
```

### Docker Deployment
```bash
# Start complete stack with RAG capabilities
./docker-start.sh

# Access services
# API: http://localhost:8000/docs
# Frontend: http://localhost:3001
# Task Monitor: http://localhost:5555
```

## 📈 Key Improvements

### Intelligence Enhancement
- **Contextual Threats**: Generated threats are now grounded in real threat intelligence
- **Current Threats**: Knowledge base updates daily with latest vulnerability data
- **Specific Guidance**: Mitigation recommendations based on actual attack patterns

### Reproducibility & Traceability
- **Version Control**: Every generated threat includes prompt version and model info
- **Audit Trail**: Full traceability of what information influenced each threat
- **Reproducible Results**: Same inputs + same versions = same outputs

### Continuous Learning
- **Feedback Loop**: Capture expert validation to improve future generations
- **Quality Metrics**: Track acceptance rates and user confidence
- **Improvement Dataset**: Build dataset for future model fine-tuning

### Operational Excellence
- **Background Processing**: Knowledge base updates don't block user requests
- **Monitoring**: Comprehensive statistics and health checks
- **Scalable**: Vector database supports millions of threat intelligence entries

## 🔧 Configuration

### Environment Variables
```bash
# Database (supports both PostgreSQL with pgvector and SQLite)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/threat_modeling

# Embedding Model (default: all-MiniLM-L6-v2)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Knowledge Sources
CISA_KEV_URL=https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
```

### Celery Beat Schedule
```python
# Daily knowledge base updates at 2 AM
beat_schedule = {
    'update-knowledge-bases-daily': {
        'task': 'tasks.update_all_knowledge_bases',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

## 🎯 Production Readiness

### Security
- ✅ Non-root Docker containers
- ✅ Input validation and sanitization
- ✅ SQL injection prevention via SQLAlchemy
- ✅ Rate limiting on expensive operations

### Performance
- ✅ Async/await throughout for high concurrency
- ✅ Database connection pooling
- ✅ Vector indexing for fast similarity search
- ✅ Background processing for heavy operations

### Monitoring
- ✅ Comprehensive logging with structured messages
- ✅ Health check endpoints for all services
- ✅ Task monitoring via Celery Flower
- ✅ Database and knowledge base statistics

### Scalability
- ✅ Horizontal Celery worker scaling
- ✅ Database-backed persistence
- ✅ Stateless API design
- ✅ CDN-ready static assets

## 🔮 Future Enhancements

### Advanced RAG Techniques
- **Hybrid Search**: Combine vector similarity with keyword matching
- **Re-ranking**: Use cross-encoder models to improve relevance
- **Multi-hop Reasoning**: Chain multiple knowledge lookups
- **Dynamic Prompts**: Adjust prompts based on threat context

### Model Improvements  
- **Fine-tuning**: Use collected feedback to fine-tune domain-specific models
- **Ensemble Methods**: Combine multiple threat generation approaches
- **Confidence Scoring**: Provide confidence intervals for generated threats
- **Bias Detection**: Monitor and mitigate model biases

### Integration Expansion
- **MITRE ATT&CK**: Full ATT&CK framework integration
- **CVE Database**: Direct CVE lookup and correlation
- **Threat Feeds**: Integration with commercial threat intelligence
- **SIEM Integration**: Push threats to security monitoring systems

## 📚 Usage Examples

### Basic RAG Threat Generation
```python
# 1. System automatically ingests threat intelligence daily
# 2. User uploads system documentation
# 3. Pipeline extracts DFD components
# 4. For each component, system:
#    - Searches knowledge base for relevant threats
#    - Augments LLM prompt with threat intelligence
#    - Generates contextually-aware threats
# 5. User reviews and provides feedback
# 6. Feedback improves future generations
```

### Knowledge Base Search
```python
import httpx

async def search_threats(query: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/knowledge-base/search",
            json={"query": query, "limit": 5}
        )
        return response.json()

# Find threats related to authentication
results = await search_threats("authentication bypass vulnerability")
```

### Feedback Collection
```python
# Submit expert feedback on generated threat
feedback = {
    "action": "EDITED",
    "edited_content": "SQL injection via user login form with insufficient input validation",
    "feedback_reason": "Made threat more specific to our authentication system",
    "confidence_rating": 5,
    "original_threat": original_threat_data
}

response = await client.post(f"/api/threats/{threat_id}/feedback", json=feedback)
```

## 🎉 Conclusion

The RAG implementation transforms the Threat Modeling Pipeline from a basic LLM application into a sophisticated threat intelligence system that:

- **Grounds threats in reality** using current vulnerability data
- **Provides full traceability** through versioning and audit trails  
- **Continuously improves** through human feedback collection
- **Scales for enterprise use** with production-ready architecture

This foundation enables organizations to generate more accurate, actionable, and up-to-date threat models while building a continuous improvement loop that enhances the system over time.

---

**Ready for Production** ✅  
**Privacy-First** ✅  
**Enterprise-Grade** ✅  
**Continuously Improving** ✅