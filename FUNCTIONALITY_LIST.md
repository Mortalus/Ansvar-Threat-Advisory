## Comprehensive Functionality List

### Authentication & RBAC
- User login (username/email + password) with session token issuance and audit logging
- User logout (session invalidation)
- Get current authenticated user profile with roles and permissions
- Create user (admin) with optional roles and client metadata (client_id, organization, external flag)
- List users (admin)
- Get user by ID (admin)
- Update user roles (admin)
- Create client user (admin)
- List client users by client_id (admin)
- Change current user password (verifies existing password)
- List roles (system admin) with permissions
- List permissions (system admin)
- Require-auth and require-permission dependency helpers; session validation

### Projects & Sessions
- Create project with name, description, tags, created_by
- List projects with pagination/search and latest-session summary
- Get project details including hierarchical session tree
- Create session within a project (new analysis run)
- Branch session from a parent session at a specified pipeline step
- Get session details (status, progress, hierarchy, threat stats)
- Load session (optionally create a new branch from current state)
- Defensive simple projects listing API with fallbacks: direct DB → pipeline inference → mock data
- Simple endpoints: create test project, health check for projects API

### Pipeline Orchestration & Tasks
- Create pipeline (metadata: name, description, owner)
- Execute pipeline step (synchronous or background) for steps: document_upload, data_extraction, data_extraction_review, dfd_extraction, dfd_review, threat_generation, threat_refinement, attack_path_analysis
- Get pipeline status (current step, step results, timestamps)
- Cancel pipeline
- List pipelines (optional status filter, limit)
- Get step result for a specific pipeline step
- Delete pipeline
- Background tasks API: enqueue single step, enqueue full pipeline run, query task status, cancel task, list active/scheduled/reserved tasks, get worker stats, worker health check
- Real-time notifications: WebSocket updates for step started/progress/completed/failed from background workers

### Documents & DFD Processing
- Upload documents (PDF/TXT) with text extraction, 10MB limit, token/cost estimates, and document_upload step execution
- Extract STRIDE-focused security data (sync or background) with optional quality validation
- Review and update extracted security data (persisted to pipeline)
- Extract DFD (enhanced default or basic) with STRIDE expert review, confidence scoring, security validation, and quality report
- Review and update DFD components with validation
- Generate threats for reviewed DFD (invokes pipeline threat_generation)
- Refine threats (invokes pipeline threat_refinement)
- Analyze attack paths (invokes pipeline attack_path_analysis) with configurable limits
- Retrieve sample DFD (for testing/demo)

### Knowledge Base & RAG
- Queue ingestion of an external knowledge source (e.g., CISA KEV) as a background task
- Search knowledge base using semantic/hybrid retrieval (pgvector in Postgres; cosine fallback in SQLite)
- Retrieve knowledge base stats (total entries, per-source counts, last updated)
- Initialize default sources (queues ingestion tasks for defaults)
- Delete knowledge entries by source name
- Scheduled updates: periodic task that queues source ingestions (incl. CWE)
- Ingest CWE database (XML/ZIP), parse, embed, and store entries with vector embeddings
- Models support dual storage for embeddings (pgvector or JSON) across DB backends

### Threat Generation & Refinement
- Threat feedback API: submit feedback (approve/reject/edit with confidence), list feedback by threat, list feedback by pipeline, aggregate feedback stats
- Threat Generator V3: multi-agent (architectural, business, compliance) analysis with CWE context, resilient LLM calls, residual risk computation, consolidated threats, priority scoring, executive summary and metrics
- Optimized threat refinement: semantic deduplication, batched risk assessment, business risk statements, prioritization/ranking, statistics, and robust fallbacks

### Real-Time & Observability
- WebSocket notifications for pipeline step/task events (start, progress, completion, failure) initiated from background workers
- Structured logging throughout pipeline and task execution for traceability and diagnostics


### Frontend UI (Next.js)
- Authenticated UI for 7-step pipeline flow with progress tracking
- Document upload and extraction screens with status toasts
- Interactive DFD visualization and review (Mermaid) with edit support
- Threat review/refinement views and feedback submission controls
- Project dashboard with session tree and branching actions
- Admin area: agent manager, prompt editor, workflow builder, workflow executions, system monitor, user manager, report exporter
- Login page and client-friendly views

### API Backend (FastAPI)
- REST endpoints for pipeline, documents, tasks, projects/sessions, knowledge base, threats/feedback, agents, settings
- WebSocket endpoint `/ws/{pipeline_id}` for real-time pipeline updates
- Dependency-injected services and RBAC-protected routes with fine-grained permissions

### Modular Agent System
- Pluggable agent registry with validator and health monitor
- Specialized agents: architectural, business, compliance
- Orchestrated multi-agent execution with resilient retries and fallbacks

### LLM Provider Abstraction
- Providers: Scaleway, Ollama, Azure, Mock
- Per-step/provider configuration, model selection, and token accounting
- Timeouts, retries, and graceful degradation for unstable providers

### Background Tasks & Scheduling
- Celery workers for pipeline steps and full pipeline execution
- Celery tasks for knowledge base ingestion (URL and CWE XML) and periodic updates
- Cleanup tasks and health/status endpoints for workers

### Database & Migrations
- SQLAlchemy models for users/RBAC, projects/sessions/snapshots, pipelines/steps/results, prompts, knowledge base (entries/CWE), feedback, workflow templates, settings
- Alembic migrations including pgvector enablement; supports PostgreSQL and SQLite
- Resilient async session creation with health checks and auto-recovery

### Prompt & Model Versioning
- Versioned prompt templates stored in DB and referenced by pipeline step results
- Recorded provider/model metadata and token usage per step for reproducibility/auditability

### Admin Workflow Templates
- Define reusable workflow templates and execute them with approval gates
- Services and endpoints to manage and run modular workflows

### Multi-Tenancy & Client Access
- Tenant scoping via `client_id` on users and pipelines; client roles with restricted permissions
- Utilities for access checks and segregation; recommended client access patterns (token/SSO)

### Settings & Configuration
- Centralized settings for application and agents with safe defaults/fallbacks
- API endpoints to view/update configuration (protected by RBAC)

### DFD Visualization & Review (UI)
- Mermaid-based interactive DFD graph with edit/validation
- Enhanced DFD quality indicators (confidence, security gaps, expert additions)

### Reporting & Export
- UI to export reports, diagrams, and summaries for stakeholders
- Aggregated feedback statistics for reporting quality improvements

### Resilience & Fault Tolerance
- Defensive DB access patterns and fallbacks (projects-simple API)
- Circuit breaker/fallback strategies for LLM calls and parsing with safe defaults
- Robust error handling across pipeline steps with stateful recovery

### Deployment & DevOps
- Docker and Compose for local/prod; startup scripts and auto-migrations
- Separate containers for API, frontend, workers, beat, and database; Nginx config
- Health endpoints and verification scripts for deployment checks

