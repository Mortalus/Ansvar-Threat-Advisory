# Root Markdown Files — Consolidated Summary

Version: 2025-08-08

This document summarizes every `.md` file located in the repository root.

## AGENT-FLOW-TEST-RESULTS.md
- Summary of backend/frontend status for agent-based threat generation.
- Notes real-time progress, RBAC enforcement, caching, and manual testing steps; highlights resilient UX and performance fixes.

## AgentUIPlan.md
- Consolidated project plan with current state, gaps, and a phased roadmap.
- Emphasizes pipeline-first UI, admin management UIs, RBAC, and future attack-path and KB admin features.

## AUTOMATION_SETTINGS_SPECIFICATION.md
- Detailed schema and UX for per-step automation controls.
- Includes confidence scoring, UI controls for admins/clients, analytics, learning/threshold tuning, and safeguards.

## CHANGELOG.md
- Documents August 8, 2025 updates aligning docs with pipeline-first approach and accurate ports/startup.

## CLAUDE2.md
- Pipeline-first compliance check; verifies Docker, defensive programming, and enterprise readiness.
- Notes pending Scaleway key rotation.

## CLIENT_ACCESS_RECOMMENDATIONS.md
- Hybrid token + optional SSO strategy for client access.
- DB schema, API endpoints, security measures, and deployment phases for client portal.

## CRITICAL_FIXES_APPLIED.md
- Defensive programming fixes preventing crashes (type checks) and session resumption flow.
- Projects button/API endpoint corrections; improved error recovery.

## CUSTOM_PROMPTS_GUIDE.md
- How to manage/activate prompt templates per step/agent via Settings API.
- Includes examples (architectural, business, compliance) and best practices.

## DFD_QUALITY_ENHANCEMENT_OPTIONS.md
- Options to boost DFD extraction quality (STRIDE expert, multi-pass agents, checklists, RAG, confidence scoring).
- Recommends STRIDE expert + confidence/checklist patterns.

## DOCKER.md
- Production-ready Docker stack guide (8 services), commands, config, and troubleshooting.
- Security guidance, scaling, and enterprise deployment notes.

## FEATURE_MAP.md
- High-level map of platform features across UI, API, pipeline, agents, LLM, KB/RAG, tasks, RBAC, reporting, etc.

## FIXES_SUMMARY.md
- User-reported issues resolved: data visibility, prerequisite UI state, 500 errors.
- Shows defensive code snippets and test validations.

## FLOW.md
- End-to-end application flow with session management, pipeline phases, DB architecture, WebSockets, RAG, and logging.
- Provides timings, observability, and performance characteristics.

## FUNCTIONALITY_LIST.md
- Exhaustive lists of capabilities by module: Auth/RBAC, Projects/Sessions, Pipeline & Tasks, Documents/DFD, KB/RAG, Threats, UI, etc.

## IMPLEMENTATION_COMPLETE.md
- Declares RAG + prompts versioning + feedback loop production-ready.
- Lists APIs/services/tables, benefits, quick start, and next steps.

## Implementation.md
- Stepwise implementation plan for RAG, prompt versioning, and feedback, independent of code specifics.

## LOGGING_IMPROVEMENTS.md
- Describes enhanced logging across handlers with emoji markers, phases, metrics, and standards.

## MAINTENANCE_GUIDE.md
- Defensive programming maintenance playbook (validation, timeouts, degradation), performance checks, health scripts, and schedules.

## Mermaid.md
- Mermaid architecture diagram showing frontend, FastAPI, Celery, pgvector, Redis, LLM providers, and ingestion flows.

## MERGED_CHANGES_SUMMARY.md
- Summarizes merged enhancements for a robust modular agent system, caching, RBAC rollout, async tasks, and UI alignment.

## MODULAR_WORKFLOW_IMPLEMENTATION_PLAN.md
- Plan for modular agents, workflow templates, client portal, DB/API schemas, security/auth, automation & metrics, and phased rollout.

## MODULE_ANALYSIS_Authentication_RBAC.md
- Analysis of Auth/RBAC module capabilities and endpoints, including sessions, roles/permissions, and audit logging.

## MODULE_PROMPT_Authentication_RBAC.md
- Module-specific prompt and coverage for Auth/RBAC features to ensure accurate documentation/testing.

## MODULE_PROMPT_Documents_DFD.md
- Prompts/tasks to validate document processing and DFD extraction flows and endpoints.

## MODULE_PROMPT_Knowledge_Base_RAG.md
- Prompts/tasks for KB ingestion/search, stats, and maintenance operations.

## MODULE_PROMPT_Pipeline_Orchestration_Tasks.md
- Prompts/tasks for pipeline create/execute/status and tasks queue/list/stats/health flows.

## MODULE_PROMPT_Projects_Sessions.md
- Prompts/tasks for project/session CRUD, branching, loading, and summaries.

## MODULE_PROMPT_Threats_Refinement.md
- Prompts/tasks for threat generation, refinement, and feedback APIs.

## PIPELINE_FIRST_COMPLIANCE_CHECK.md
- Confirmation of pipeline-first compliance and operational readiness; reiterates security note on key rotation.

## PROJECTS_STATUS_REPORT.md
- Status of projects interface with pooling issue; provides workarounds and confirms core pipeline stability.

## RAG_IMPLEMENTATION.md
- RAG architecture, schemas, endpoints, ingestion/search, testing, deployment, and future enhancements.

## README.md
- Project overview, features, quick start, pipeline-first API usage, configuration, and development instructions.

## ROBUST_AGENT_SYSTEM_SUMMARY.md
- Comprehensive summary of modular agent system, health monitoring, validation, UI/UX, tests, and metrics.

## SECURITY_ALERT.md
- Critical alert to rotate exposed Scaleway API key; best practices for secret management.

## THREAT_QUALITY_IMPROVEMENT.md
- Three-stage quality improvement: context-aware scoring, multi-agent, and integrated analysis with quantified gains.

## THREAT_STEPS.md
- Functional walkthrough of the pipeline steps with V3 multi-agent detail and refinement process; unlimited processing and learning.

## updated-project-instructions.md
- Actionable sprints/phases: pipeline-first frontend refactor, fast agent catalog, RBAC/tenancy, Admin Hub, KB growth, and enterprise hardening.

## WORKSHOP_GUIDE.md
- Interactive DFD workshop guide with setup, live editing/visualization flows, and presentation tips.

## UX_UI_Current.md
- Current end-user UX/UI snapshot: 7-step pipeline, background tasks with WebSockets, DFD review, threat gen/refine; known gaps.

## UX_UI_Admin_Current.md
- Current admin UX/UI snapshot: agents, workflow builder/executions, prompts, monitor, users; present gaps and IA mockup.

## UX_UI_Future_Improvements.md
- Future UX/UI plan with Admin Workflow Builder (agents + web search + RAG), RBAC workflow rights, review gates by default, auto-run toggles, and runner/designer mockups.
