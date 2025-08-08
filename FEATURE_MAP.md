## High-Level Feature Map

- **Frontend UI (Next.js)**: User-facing application in `apps/web` that guides the 7-step pipeline, provides interactive DFD review/visualization, admin tools, and real-time status.
- **API Backend (FastAPI)**: Service in `apps/api` exposing REST and WebSocket endpoints for pipeline execution, agents, knowledge base, projects/sessions, settings, and authentication.
- **Pipeline Orchestration**: Core managers in `apps/api/app/core/pipeline` that coordinate document upload, DFD extraction/review, multi-agent threat generation (V3), refinement, and optional attack path analysis with step tracking.
- **Modular Agent System**: Pluggable agents in `apps/api/app/core/agents` with a registry, validator, and health monitor enabling specialized analyses (architectural, business, compliance) and resilient execution.
- **LLM Provider Abstraction**: Provider layer in `apps/api/app/core/llm` supporting Scaleway, Ollama, Azure, and mock backends with per-step model/config selection.
- **Knowledge Base & RAG**: Vector-backed knowledge store (`knowledge_base_entries`, pgvector) with ingestion/search services grounding generation with CWE/MITRE/CISA context.
- **Background Tasks & Scheduling**: Celery workers and Beat with Redis broker handling long-running steps, queued execution, and scheduled KB updates and maintenance tasks.
- **Database & Migrations**: SQLAlchemy models and Alembic migrations managing pipelines, steps, prompts, feedback, workflow templates, projects/sessions, and vector indices on PostgreSQL/SQLite.
- **Authentication & RBAC**: Auth endpoints and role-based permissions controlling access to pipeline execution, agent management, knowledge base operations, and admin features.
- **Project & Session Management**: Entities and APIs that organize analyses into projects and sessions with branching, persistence, and resumption of pipeline state.
- **Real-Time Updates (WebSocket)**: Live pipeline notifications via `/ws/{pipeline_id}` for step start, progress, completion, and failure events to keep the UI in sync.
- **Prompt & Model Versioning**: Versioned prompt templates and recorded model metadata to ensure reproducibility, auditability, and controlled prompt evolution.
- **Threat Feedback & Learning**: Feedback capture and statistics enabling few-shot learning and continuous quality improvement of generated/refined threats.
- **Logging & Observability**: Structured, verbose logging with health endpoints and task monitoring to trace flows, diagnose issues, and measure performance.
- **Admin Workflow Templates**: Configurable workflow template definitions and execution services enabling reusable, automated step sequences with approval gates.
- **Multi-Tenancy & Client Access**: Tenant-scoping utilities and recommended client access patterns (token-based/SSO) for secure external collaboration.
- **Settings & Configuration**: Centralized application/agent settings and safe fallbacks for provider parameters, prompts, and automation controls.
- **DFD Visualization & Review**: Interactive Mermaid-based components for visualizing and editing extracted DFDs with validation and export options.
- **Reporting & Export**: UI components and APIs to export results, diagrams, and summaries for stakeholder deliverables.
- **Deployment & DevOps**: Docker/Docker Compose, startup scripts, and auto-migrations for local development and production deployment.


