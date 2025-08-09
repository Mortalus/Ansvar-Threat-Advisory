## Migration Plan: Decouple UI From Current Backend and Enable Pluggable Backends

### Goals
- Decouple the frontend(s) from the current API surface so the UI can switch between the existing backend and a new backend with minimal code changes.
- Establish a thin, type-safe client layer (SDK) and adapter(s) that normalize data contracts and error models.
- Preserve current functionality while enabling incremental migration and safe rollback.

### Scope
- In scope: API client abstraction, types, adapters for Current Backend (CB) and New Backend (NB), WebSocket abstraction, authentication abstraction, configuration/feature flags, mocks and contract tests, rollout plan.
- Out of scope: Changing backend implementations (beyond documenting required mappings), large UX redesigns, deep state management refactors.

### Current State Summary (as of repo)
- UI implementations:
  - Next.js app under `apps/web/` already calls the existing API directly via `apps/web/lib/api.ts` and uses `/api/ws/...` WebSockets.
  - New Vite app under `New_design/` uses mock data only; no API integration yet.
- Backend (CB) provides Phase 2/3 workflow endpoints, agent endpoints, settings/prompts, and WS endpoints. Some execution nuances exist (e.g., execute-async gating and single-step executor), so the UI must not hardcode assumptions about terminal transitions.

### Decoupling Architecture
1. Canonical UI Domain Models
   - Define canonical TS interfaces for core entities used by UI:
     - WorkflowTemplate, WorkflowRun, WorkflowStep, WorkflowArtifact, AgentInfo, AgentConfig, PromptTemplate, AuthSession.
   - Put these in a shared location per app:
     - Next app: `apps/web/lib/types.ts` (or `lib/types/`)
     - New_design app: `New_design/src/lib/types.ts`

2. API Client (SDK) Interface
   - Define an interface describing all UI needs (CRUD + actions):
     - Templates: list/get/create
     - Runs: start, status, list, artifacts, cancel, executeNext, executeAsync
     - Agents: list, get/update config, test, history, performance
     - Prompts/settings: list/get/update
     - Auth: login/logout/refresh, current user
   - Example (conceptual):
     - `IBackendClient { workflows: { listTemplates(): Promise<WorkflowTemplate[]>; startRun(...); getRunStatus(...); ... }, agents: {...}, auth: {...} }`

3. Adapters (per backend)
   - Implement `CurrentBackendAdapter` mapping the SDK interface to existing endpoints:
     - Base URL: `/api/phase2/...`, `/api/agents/...`, `/api/settings/...`
     - WS URLs: `/api/ws/workflow`, `/api/ws/workflow/{runId}`
     - Normalize enums/strings (e.g., status values: `created/running/completed/failed/...`).
   - Implement `NewBackendAdapter` translating SDK methods to NB endpoints (when NB is ready). If NB differs materially, adapt and coerce to the canonical models.

4. Transport Layer & Config
   - Provide a small HTTP layer (fetch or axios) with:
     - Base URL from env (e.g., `VITE_API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL`).
     - Auth token injection (Bearer) and 401 handling.
     - Consistent error object shape: `{ code, message, details }`.
   - WebSocket utility that accepts a path provider from the adapter and exposes a uniform event API: `onRunStatus`, `onStepStatus`, `onArtifact`, `onError`.

5. Feature Flags & Selection
   - Runtime or build-time flag to choose adapter:
     - Env: `BACKEND_TARGET=current` | `new`
     - Optional query param override for testing: `?backend=new`.
   - Progressive enablement: start with CB, switch specific features to NB as they land (via per-feature flags).

6. Authentication Abstraction
   - `AuthProvider` interface: `login`, `logout`, `getToken`, `onTokenChanged`.
   - Current impl: uses CB’s auth endpoints (already present in Next app). NB adapter can provide its own auth flow if needed.

7. Error Model & Resilience
   - Normalize transport errors and backend business errors to one shape.
   - Retries/backoff for transient errors; circuit-breaker optional.
   - UI should not assume automatic completion of runs; always poll or subscribe, and surface manual actions when needed.

### Implementation Steps
1. New_design: Introduce SDK and Types
   - Create `New_design/src/lib/types.ts` (canonical UI types).
   - Create `New_design/src/lib/http.ts` for fetch client with base URL, token injection, and error normalization.
   - Create `New_design/src/lib/ws.ts` for WebSocket wrapper (connect, subscribe, parse, dispatch).
   - Create `New_design/src/lib/sdk.ts` defining `IBackendClient` interface (no implementation yet).

2. Current Backend Adapter (CB)
   - Create `New_design/src/lib/adapters/currentBackend.ts` implementing `IBackendClient` using existing endpoints:
     - Templates: `GET /api/phase2/workflow/templates`
     - Start run: `POST /api/phase2/workflow/runs/start`
     - Run status: `GET /api/phase2/workflow/runs/{runId}/status`
     - Artifacts: `GET /api/phase2/workflow/runs/{runId}/artifacts?include_content=true`
     - Execute next/async, cancel, list runs
     - Agents: `GET /api/agents/list`, config, test, etc.
     - Prompts/settings endpoints
   - Create `New_design/src/lib/wsPaths.current.ts` mapping to `/api/ws/workflow` endpoints.

3. New Backend Adapter (NB)
   - Create `New_design/src/lib/adapters/newBackend.ts` with stubs aligned to NB API design.
   - Implement mapping/coercion to canonical types as NB endpoints are finalized.

4. Adapter Selector & App Wiring
   - Add `New_design/src/lib/backendSelector.ts` reading `VITE_BACKEND_TARGET` and returning the chosen adapter instance.
   - Update `App.tsx` views to replace mock data with SDK calls.
   - For Workflows, wire:
     - List templates -> adapter.workflows.listTemplates()
     - Start run -> adapter.workflows.startRun()
     - Run detail -> poll adapter.workflows.getRunStatus() and fetch artifacts; optionally subscribe via WS wrapper.

5. Next.js App (apps/web) — Optional Alignment
   - Introduce the same SDK pattern (or reuse logic) under `apps/web/lib/sdk/` to simplify parallel migration.
   - Replace direct fetches with SDK calls over time (incremental PRs).

6. Mocks & Contract Tests
   - Add MSW (Mock Service Worker) in New_design for local dev to simulate both CB and NB.
   - Write contract tests ensuring adapters produce canonical types (Jest/Vitest):
     - Given backend response X, adapter returns canonical model Y.
     - Ensures UI stability even if backend responses vary.

7. Observability Hooks
   - Add opt-in logging/telemetry middleware in `http.ts` (request/response timing, status, payload size) with sampling.
   - Surface adapter identity (current/new) in logs for troubleshooting.

### Data Contract Mapping (Canonical -> Current Backend)
- WorkflowStatus: `created | running | paused | completed | failed | cancelled | timeout` (strings)
  - CB: already uses lowercase strings; UI must not assume auto-complete behavior.
- WorkflowRun:
  - Fields: `run_id`, `status`, `progress`, `total_steps`, `completed_steps`, `started_at`, `completed_at`, `is_terminal`, `can_retry`.
  - CB: provided by `/runs/{runId}/status` and `/runs` list; map to canonical names.
- WorkflowStep:
  - Fields: `step_id`, `agent_type`, `status`, `position`, `retry_count`, `execution_time_ms`.
  - CB: exposed in run status payload.
- WorkflowArtifact:
  - Fields: `name`, `artifact_type`, `version`, `is_latest`, `size_bytes`, optional `content_json/text` (when requested with `include_content=true`).
- AgentInfo/Config: map from `/api/agents/list` and `/agents/{name}/config` to canonical fields; convert casing where needed.
- Prompts/Settings: UI-level types independent of backend storage; adapters coerce as needed.

### Authentication Abstraction
- `AuthProvider` contract:
  - `login(credentials) -> { token, user }`
  - `logout()`
  - `getToken()`
  - `refresh()` (optional)
- CB adapter implementation leverages existing auth endpoints and stores token in `localStorage`.
- NB adapter can implement a different flow; UI uses the same AuthProvider API.

### WebSocket Abstraction
- Provide `subscribeToRun(runId, handlers)` returning a disposable subscription.
- CB path: `/api/ws/workflow/{runId}`; events: `run_status`, `step_status`, `artifact_created`, `error`.
- NB path: determined by NB; adapter translates events to canonical event objects.

### Configuration & Environments
- Env vars for New_design:
  - `VITE_API_BASE_URL` (e.g., `http://localhost:8000` or gateway origin)
  - `VITE_WS_BASE_URL` (optional; otherwise derived from window.location)
  - `VITE_BACKEND_TARGET` = `current` | `new`
- CORS/WS
  - Ensure backend allows Vite dev origin (CORS) and WS proxying via gateway; or run Vite behind the same gateway.

### Rollout Plan
1. Phase A — Introduce SDK & CB Adapter in New_design
   - Replace mock reads with adapter calls for Agents and Workflow templates first.
   - Keep mock write actions (create agent/workflow) until backend supports them.
2. Phase B — Wire Runs & Status
   - Start runs from UI, poll status, fetch artifacts; add WS when convenient.
3. Phase C — Stabilize & Tests
   - Add MSW mocks and contract tests; tighten types; add error surfaces.
4. Phase D — Add NB Adapter (feature-flagged)
   - Implement NB endpoints as they become available; validate parity via contract tests.
5. Phase E — Progressive Cutover
   - Enable NB by env/flag in selected environments (staging); monitor; roll back if needed.

### Risks & Mitigations
- Backend behavioral differences (e.g., execution lifecycle)
  - Mitigation: UI treats runs as event-driven; no strong assumptions; user can trigger next step; robust empty/error states.
- Divergent schemas between CB and NB
  - Mitigation: canonical UI types with per-adapter coercion; contract tests enforce stability.
- Auth differences
  - Mitigation: Auth abstraction; adapter-owned flows.
- WS pathing/proxy issues
  - Mitigation: central WS wrapper; configurable base URL; fallback to polling.

### Testing Strategy
- Unit tests for adapters: input-output mapping.
- Integration tests against MSW: happy paths + error paths.
- Manual E2E smoke in dev/staging with both adapters selected via env.

### Acceptance Criteria Checklist
- [ ] Canonical types defined and used in UI components
- [ ] `IBackendClient` interface implemented for CB; NB stub in place
- [ ] HTTP client with token injection and normalized errors
- [ ] WS wrapper publishing canonical events
- [ ] Feature flag/env switch between CB and NB
- [ ] Contract tests for key endpoints (templates, runs, status, artifacts, agents)
- [ ] Documentation for env/config and adapter selection

### Suggested File Layout (New_design)
- `src/lib/types.ts` — canonical UI types
- `src/lib/http.ts` — HTTP client
- `src/lib/ws.ts` — WebSocket helper
- `src/lib/sdk.ts` — `IBackendClient` interface
- `src/lib/adapters/currentBackend.ts` — CB adapter
- `src/lib/adapters/newBackend.ts` — NB adapter
- `src/lib/backendSelector.ts` — selects adapter by env/flag
- `src/features/...` — Views use SDK only (no raw fetch)

### Timeline (indicative)
- Day 1: Types + HTTP + SDK interface + CB adapter (read-only flows)
- Day 2: Workflows start/status/artifacts + Agents list/config
- Day 3: WS wrapper + error surfaces + MSW contract tests
- Day 4+: NB adapter implementation as endpoints become available; staged rollout

### Notes on Current Backend Edge Cases (UI implications)
- `execute-async` gating and single-step executor: UI should support manual "Execute Next" triggers and not assume that a single call completes a run.
- DFD extractor context: ensure `document_text` is provided via `initial_context` and that adapters pass it correctly when starting runs.

---
This plan allows the New_design UI to integrate quickly with the existing backend while creating a durable seam to switch to the new backend without reworking components.


