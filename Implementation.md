Of course. Based on the documented architecture and the goal of creating a robust, new implementation, here is a clear and actionable step-by-step plan for a developer.

This plan presumes a clean slate for the new functionality and does not rely on the specific logic within the provided Python files, instead focusing on building the features correctly within the existing architectural patterns.

Phase 1: Implement the Retrieval-Augmented Generation (RAG) Pipeline
Objective: To replace the simple threat generation logic with a more intelligent RAG process that grounds LLM output in a trusted knowledge base.

Step 1.1: Set Up the pgvector Database Environment

Update Docker Configuration: Modify the postgres service in your docker-compose.yml file to use an image that includes the pgvector extension. This avoids manual compilation.

File: docker-compose.yml

Action: Change image: postgres:15 to image: pgvector/pgvector:pg15.

Add Python Dependencies: Update the backend's requirements to include libraries for pgvector and sentence embeddings.

File: apps/api/requirements.txt

Action: Add the following lines:

pgvector==0.2.0
sentence-transformers==2.7.0
Rebuild your Docker container (./docker-start.sh will handle this) or update your local virtual environment (pip install -r requirements.txt).

Create a Database Migration to Enable the Extension:

Action (Terminal in apps/api):

alembic revision -m "Enable vector extension"

Edit the new file in alembic/versions/ to add op.execute("CREATE EXTENSION IF NOT EXISTS vector;") to the upgrade() function.

alembic upgrade head to apply it to your database.

Step 1.2: Define the Knowledge Base Schema

Create a New SQLAlchemy Model: This table will store the text chunks and their corresponding vector embeddings.

Action: Create a new file apps/api/app/models/knowledge_base.py.

Content:

Python

from sqlalchemy import Column, Integer, String, Text
from pgvector.sqlalchemy import Vector
from app.database import Base

class KnowledgeBaseEntry(Base):
    __tablename__ = "knowledge_base_entries"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False, index=True) # e.g., 'MITRE_ATT&CK'
    technique_id = Column(String(50), index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384)) # Dimension for 'all-MiniLM-L6-v2' model
Generate and Apply the Migration:

Action (Terminal): alembic revision --autogenerate -m "Create knowledge_base_entries table" followed by alembic upgrade head.

Step 1.3: Implement a Data Ingestion Service and Task

Create a Standalone Ingestion Service: This service will contain the core logic for processing and embedding data, keeping it separate from the Celery task definition.

Action: Create a new file apps/api/app/services/ingestion_service.py.

Functionality:

Define a class IngestionService with an async def ingest_from_url(...) method.

This method will handle fetching data from a source (e.g., CISA KEV URL), parsing it, generating embeddings for relevant text chunks using SentenceTransformer, and saving them as KnowledgeBaseEntry objects to the database.

Create a Celery Task to Trigger Ingestion:

Action: Create a new file apps/api/app/tasks/knowledge_base_tasks.py.

Functionality:

Define a Celery task, e.g., @celery_app.task(name="tasks.ingest_knowledge_base").

This task will instantiate IngestionService and call its ingest_from_url method.

To enable periodic updates, configure this task in your Celery Beat schedule within apps/api/app/celery_app.py.

Step 1.4: Implement the RAG-Powered Threat Generation Step

Create a New Pipeline Step Handler: This isolates the logic for this specific pipeline stage.

Action: Create a new file apps/api/app/core/pipeline/steps/threat_generator.py.

Functionality:

Define a class ThreatGenerator with an async def execute(self, db_session, pipeline_step_result, component_data) method.

Inside the execute method:

Formulate Query: Generate a descriptive search query from the input component_data (e.g., "Elevation of privilege vulnerability in a Process component named 'Authentication Service'").

Embed Query: Use the SentenceTransformer model to convert this query string into a vector embedding.

Perform Vector Search: Execute an async SQLAlchemy query against the knowledge_base_entries table to find the top 3-5 most relevant entries. Use the l2_distance function provided by pgvector for similarity search.

Augment Prompt: Construct the final LLM prompt, including a new section titled "Relevant Threat Intelligence Context" populated with the content from the search results.

Invoke LLM: Call the appropriate LLM provider via the existing LLM factory.

Store Results: Parse the LLM's response and save the generated threats, linking them to the current pipeline_step_result.

Phase 2: Implement Model and Prompt Versioning
Objective: To ensure all generated results are reproducible and traceable by versioning the prompts and models used.

Step 2.1: Update the Database Schema

Create a Prompt Model: This table will store all prompt templates and their versions.

Action: Create apps/api/app/models/prompt.py.

Content: Include columns for id, name (a unique identifier like threat_generation), version (integer), template_text (Text), and is_active (Boolean). Add a unique constraint on (name, version).

Update the PipelineStepResult Model: Add foreign keys to track exactly what was used.

File: apps/api/app/models/pipeline.py.

Action: Add prompt_id = Column(Integer, ForeignKey("prompts.id")), llm_model = Column(String), and embedding_model = Column(String).

Generate and Apply Migration:

Action (Terminal): Run Alembic to generate and apply these changes.

Step 2.2: Implement a Prompt Management Service

Create the Service: This centralizes access to prompts.

Action: Create apps/api/app/services/prompt_service.py.

Functionality: Implement an async def get_active_prompt(db_session, name: str) method that queries the prompts table for the active prompt with the given name.

Step 2.3: Integrate Versioning into the Pipeline Step

Update the ThreatGenerator: Modify the step handler from Phase 1.

File: apps/api/app/core/pipeline/steps/threat_generator.py.

Action:

Instead of using a hardcoded prompt, call the new PromptService to fetch the active prompt template from the database at the beginning of the execute method.

When saving the final PipelineStepResult, populate the new fields: prompt_id (from the prompt you just fetched), llm_model, and embedding_model (these model names can be retrieved from your application's settings file, config.py).

Phase 3: Establish the Human Feedback Loop Foundation
Objective: To build the backend infrastructure needed to capture user validation of generated threats, creating a dataset for future fine-tuning.

Step 3.1: Create the Feedback Database Model

Define the Model: This table will log every user interaction with a generated threat.

Action: Create apps/api/app/models/threat_feedback.py.

Content:

Define a Python Enum for ValidationAction ('ACCEPTED', 'EDITED', 'DELETED').

Create a ThreatFeedback model with columns for id, threat_id (ForeignKey to your threats table), action (using the Enum), edited_content (Text, nullable), and a user_id (nullable for now, to be linked when authentication is added).

Generate and Apply Migration:

Action (Terminal): Run Alembic to add this table.

Step 3.2: Implement the Feedback API Endpoint

Create a New Endpoint: This allows the frontend to submit feedback data.

File: A new file is appropriate here, apps/api/app/api/endpoints/threats.py.

Functionality:

Define a POST /api/threats/{threat_id}/feedback endpoint.

Create a Pydantic BaseModel to define the request body, expecting an action and optional edited_content.

The endpoint handler will receive this data, create a ThreatFeedback record, and save it to the database using an async session.

Inform Frontend Team: Communicate the availability and specification of this new endpoint so they can integrate it into the Threat Refinement UI.