### Updated Project Instructions (Actionable)

Purpose: Convert the current platform plan into developer-executable steps that are modular, defensively programmed, and future-proof for enterprise clients.

Scope covered here:
- P0 security actions
- Sprint 1 (platform unification + performance + RBAC)
- Sprint 2 (admin UX, agents, KB)
- Phase 3 (enterprise hardening)
- Guardrails, testing, and acceptance criteria

---

### P0 Security (Do first)

- Rotate exposed secrets
  - Revoke and replace Scaleway API key (referenced in docs). Update `apps/api/.env` and Docker secrets if used.
  - Run a full repo scan for secrets:
    - Add/Run: `gitleaks detect --no-git -v` (or TruffleHog) in CI and pre-commit.
  - Ensure logs redact secrets. Search code for logging of provider configs and redact.

- Runtime config validation (fail fast)
  - In `apps/api/app/core/llm/__init__.py`, ensure provider selection errors clearly explain missing envs.
  - Add startup validation in `apps/api/app/startup.py`: verify required envs per enabled provider and raise on invalid config.

- Request correlation + structured logs
  - Add a request ID middleware in `apps/api/app/main.py` and include the ID in:
    - API logs, Celery task metadata, and WebSocket messages.
  - Standardize JSON logs; propagate correlation ID through worker logs.

Acceptance:
- CI secrets scan passes, secrets rotated, logs show redaction, startup fails fast on invalid provider setup, correlation IDs visible in API/WS/task logs.

---

### Sprint 1: Unify Frontend With Stateful Pipeline + Performance + RBAC

#### A. Frontend API Refactor (Pipeline-first)

- Store pipeline_id centrally
  - File: `apps/web/lib/store.ts`
  - Add state: `pipelineId`, mutators `setPipelineId`, and selectors for step status.

- Create pipeline on flow start
  - File: `apps/web/lib/api.ts`
  - Add `createPipeline(): Promise<{ pipeline_id: string }>` calling `POST /api/pipeline/create`.
  - On upload/start button, call `createPipeline` and persist `pipelineId` in store.

- Execute steps via background tasks
  - File: `apps/web/lib/api.ts`
  - Add `executeStepBackground(pipelineId: string, step: string, data: any)` → `POST /api/tasks/execute-step`.
  - Replace direct document-step calls with `executeStepBackground` in pipeline components:
    - `apps/web/components/pipeline/steps/dfd-review.tsx`
    - `apps/web/components/pipeline/steps/dfd-visualization.tsx`
    - `apps/web/components/pipeline/steps/threat-generation-step.tsx`
    - `apps/web/components/pipeline/steps/enhanced-dfd-review.tsx`

- Real-time progress via WebSocket
  - Verify existing `api.connectWebSocket(pipelineId)` usage.
  - Ensure event handling for: `task_queued`, `step_started`, `task_progress`, `step_completed`, `task_failed` updates store.

- Add cancel/retry controls
  - File: `apps/web/components/agents/task-monitor.tsx`
  - Add actions using `POST /api/pipeline/{id}/cancel` and re-queue via `executeStepBackground`.

Acceptance:
- A user can complete: upload → DFD extraction/review → agent-based threats → refinement with live progress.
- UI persists and resumes state by `pipelineId`.

#### B. Backend: Fast Agent Catalog (sub-1s)

- Cache agent registry summaries
  - File: `apps/api/app/core/agents/registry.py`
    - Add method `get_cached_catalog()` reading from Redis/DB snapshot with TTL (e.g., 30s).
    - Add background refresh task that performs full discovery and writes the snapshot.
  - Endpoint: `apps/api/app/api/endpoints/agents_simple.py`
    - Serve from cached snapshot; include `last_refreshed` and `refresh_in_progress` flags.
  - Startup: `apps/api/app/startup.py`
    - Run `initialize_agent_registry()` and schedule periodic refresh.

- Split heavy detail endpoint
  - File: `apps/api/app/api/endpoints/agent_management.py`
    - Add `/agents/{name}/summary` (cached) and `/agents/{name}/details` (may be deferred/queued).

Acceptance:
- `GET /api/agents/list` returns < 1s consistently.
- Registry refresh occurs asynchronously without blocking requests.

#### C. RBAC + Multi-Tenancy Enforcement

- Enforce permission checks (decorator/dependency)
  - File: `apps/api/app/api/v1/auth.py`
    - Ensure `require_permission()` is reusable; export for endpoints.
  - Apply to sensitive endpoints:
    - Pipeline execute/cancel/list/delete → `PIPELINE_EXECUTE`, `PIPELINE_VIEW`.
    - Agent configure/enable/disable → `AGENT_MANAGE`.
    - KB ingest/update/delete → `KB_MANAGE`.
    - Settings/prompts CRUD → `SETTINGS_MANAGE`.

- Client scoping
  - Use `utils/multi_tenant.py` helpers to filter queries by `client_id` for list/read; validate write access on mutations.
  - Verify models include `client_id` where applicable (`Pipeline`, user-linked records).

- Sessions
  - Ensure session validation on all routes that mutate state.

Acceptance:
- Role matrix tests pass for Admin/Analyst/Viewer/Client across endpoints.
- Cross-tenant access attempts are denied.

---

### Sprint 2: Admin UX + New Agents + KB Expansion

#### A. Admin Hub (UI)

- Agents page
  - Files:
    - `apps/web/components/admin/agent-manager.tsx`
    - `apps/web/app/admin/agents/page.tsx`
  - Implement list/filter, health status, enable/disable, config view/edit (reads/writes to agent endpoints).

- Prompts/Settings
  - File: `apps/web/components/admin/prompt-editor.tsx`
  - CRUD against `/api/settings/prompts` and activation endpoint.

- Tasks/Workers overview
  - File: `apps/web/components/admin/system-monitor.tsx`
  - Read `/api/tasks/list`, `/api/tasks/stats`; surface retries/failures.

- Audit/History
  - File: `apps/web/components/admin/history-viewer.tsx`
  - Read `AgentExecutionLog`, threat feedback and show human-readable audit trail.

Acceptance:
- Admin can enable/disable agents, edit prompts, view tasks, and see audit history from the UI.

#### B. Finish Agent Management Backend

- Implement configuration lifecycle
  - File: `apps/api/app/api/endpoints/agent_management.py`
    - Implement `POST /agents/{name}/configure` (validate with `AgentValidator`, audit write).
    - Implement `POST /agents/{name}/enable` and `/disable` with RBAC and audit logging.
  - File: `apps/api/app/models/agent_config.py`
    - Ensure versioning of configs; write execution logs on test runs.

Acceptance:
- Config/enable/disable endpoints functional with full validation and audits.

#### C. Add 3–5 Modular Agents (plugin-first)

Implement under `apps/api/app/core/agents/impl/` with `BaseAgent`:
- CloudConfigurationAgent (cloud posture/IaC risks)
- IdentityAccessAgent (IAM/SSO/OAuth/priv-esc)
- DataProtectionAgent (PII/PHI, encryption/retention)
- ApplicationSecurityAgent (OWASP/CWE mapping)
- ThreatIntelEnrichmentAgent (link KB entries to threats)

For each agent:
- Define `AgentMetadata` (category, version, requirements).
- Add input/output validation via `AgentValidator`.
- Expose health probe; integrate with `AgentHealthMonitor`.
- Unit tests using Mock LLM and DFD fixtures.

Acceptance:
- Agents discoverable via registry, configurable from Admin, runnable in pipeline, tests pass.

#### D. KB Expansion + UI

- Ingestion providers
  - File: `apps/api/app/services/ingestion_service.py`
  - Add NIST 800-53 and CIS Controls processors (distinct `source` names).
  - Support per-tenant namespaces (e.g., `source_tenant` or `namespace` field).

- KB Admin UI
  - Files: `apps/web/components/admin/report-exporter.tsx` (or new `kb-manager.tsx`)
  - Show source stats, last updated, error states; trigger updates via `/api/knowledge-base/update-all`.

Acceptance:
- New sources ingested with stats visible; per-tenant queries isolated; UI can refresh and monitor KB.

---

### Phase 3: Enterprise Hardening (observability, governance, scale)

- Observability
  - Add Prometheus metrics and Grafana dashboards; export Celery, DB, HTTP, and agent metrics.
  - OpenTelemetry tracing across API/Celery/DB; include correlation IDs; surface in logs and WS messages.

- Data governance
  - Add retention policies per tenant; redaction for PII in logs; export/delete-by-tenant tools.

- LLM strategy
  - Per-tenant provider selection with health gating; canary/feature flags for agents and prompts.

- Packaging and plugins
  - Define entry-point discovery for agent and KB providers; semantic versioning and migration contracts.

- HA/Scaling
  - Celery priority queues per tenant/role; worker autoscaling; DB pool tuning; backpressure signaling to UI.

Acceptance:
- Dashboards live and actionable; traces propagate; tenancy governance tools present; load tests meet SLAs.

---

### Guardrails (apply to all work)

- Defensive programming
  - Strict Pydantic schemas (`extra="forbid"`), explicit timeouts and retries, circuit breakers, graceful degradation.
  - Idempotent pipeline writes; clear, typed WebSocket messages; consistent error envelopes.

- RBAC testing
  - Unit/integration tests for Admin/Analyst/Viewer/Client role matrices.

- Rate limiting and quotas
  - Enforce via NGINX and app-level limits (document size, concurrent steps per tenant, queue priorities).

- Code quality
  - Strong typing, descriptive names, early returns, clear error paths, and module boundaries.

---

### Testing & Acceptance Checklist

- Backend
  - Unit tests: agent registry (cached), validator, health monitor, RBAC permissions, KB ingestion/search.
  - Integration tests: full pipeline via tasks + WS; admin endpoints; multi-tenant filtering.

- Frontend
  - Pipeline E2E: create → execute steps → live updates → cancel/retry → resume.
  - Admin flows: list/enable/disable/configure agents; prompts CRUD; KB stats/actions; tasks view.

- Performance
  - `GET /api/agents/list` < 1s; background refresh not blocking.
  - Pipeline steps emit WS messages within 1s of task queueing.

---

### Quick Reference (files to touch)

- Backend
  - Agents: `app/core/agents/{registry.py,validator.py,health_monitor.py,impl/*,orchestrator_v2.py}`
  - Pipeline: `app/core/pipeline/manager.py`, `app/api/endpoints/{pipeline.py,tasks.py,documents.py}`
  - Agents API: `app/api/endpoints/{agents_simple.py,agent_management.py,agent_health.py}`
  - KB: `app/services/ingestion_service.py`, `app/api/endpoints/knowledge_base.py`
  - RBAC: `app/api/v1/auth.py`, `app/services/rbac_service.py`, `app/utils/multi_tenant.py`
  - Startup: `app/startup.py`, `app/main.py` (middleware/logging)

- Frontend
  - API & Store: `apps/web/lib/{api.ts,store.ts}`
  - Pipeline Steps: `apps/web/components/pipeline/steps/*`
  - Admin: `apps/web/components/admin/*`, `apps/web/app/admin/*`

---

Notes
- This document converts the direction in `CLAUDE2.md` and `AgentUIPlan.md` into concrete, developer-ready tasks with acceptance criteria.
- Keep changes modular and feature-flagged where appropriate. Target small, mergeable PRs with tests.



