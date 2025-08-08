# UX/UI Current State Summary

Version: 2025-08-08

## Executive Snapshot
- **Primary users**: Analysts/Security Engineers running a 7-step pipeline; Admins configuring agents and settings.
- **Core journey**: Upload docs → DFD extraction → DFD review → Threat Generation (V3 multi-agent) → Threat Refinement → (optional) Attack Path Analysis → Export/report.
- **System behavior**: Long-running steps run in background with real-time WebSocket updates; strong defensive UX around loading, errors, and retries.

## Information Architecture (Frontend)
- `apps/web/app/`
  - `page.tsx`: Main pipeline entry with stepwise flow.
  - `projects/`: Project/session views (list, layout, simple, test).
  - `admin/`: Hubs for agents, workflow builder/executions, prompts, system monitor, users.
  - `login/`: Auth screen.
- `apps/web/components/`
  - `pipeline/steps/`: DFD review, interactive Mermaid, threat generation, agent configuration (enhanced), etc.
  - `admin/`: Agent Manager, Prompt Editor, Workflow Builder, System Monitor, User Manager, Report Exporter.
  - `ui/`: Buttons, Cards, Progress, Toaster, ErrorBoundary.

## Key Screens & Current UX
- **Home/Pipeline**
  - Guided, linear steps with prerequisites and clear disabled states.
  - Background execution with toasts + progress; reconnect-safe WebSocket status.
  - DFD Review features: visual Mermaid, JSON, and editable lists with validation.
  - Threat Generation (V3): multi-agent summary, progress by agent, clear completion/continue affordances.
  - Threat Refinement: risk ranking, business context, consolidation explained in UI.

- **Projects & Sessions**
  - Projects and branched sessions model exist; UI provides session tree and resumption.
  - Known: intermittent pooling issues on some `/projects/*` calls; core pipeline remains unaffected.

- **Admin Area (present but partial)**
  - Pages for agent management, prompts, workflow builder/executions, system monitor, users, reports.
  - Portions are stubs/in-progress; backend coverage is broader than current UI wiring.

## Interactions & Feedback
- **Progress & Status**: 
  - WebSocket messages: `step_started`, `task_progress`, `step_completed`, `task_failed`.
  - Visual progress bars and per-step/agent indicators.
- **Error Handling**:
  - Defensive timeouts, retries, circuit breakers reflected with clear messages.
  - Safe fallbacks and empty states; users can re-run steps without losing state.
- **Cost Transparency**:
  - Token estimates surfaced early (document upload) to set expectations.

## Roles & Permissions (Current)
- Auth present; RBAC partially enforced at API boundaries (pipeline, agents, KB).
- Admin tools exist in UI; permissions model is evolving (e.g., dedicated `KB_MANAGE` planned).

## Known UX Gaps
- Frontend still contains legacy stateless flows in places; must standardize on stateful pipeline/task APIs.
- Admin management UIs (agents, workflows, audit history) are not fully wired to backend capabilities.
- Report generation/export UI not yet completed.

## Current End-User Flow (Mockup)
```mermaid
flowchart LR
  U[Upload Documents] --> DFD[Extract DFD]
  DFD --> RV[Review & Edit DFD]
  RV --> TG[Generate Threats (V3 Multi‑Agent)]
  TG --> TR[Refine Threats]
  TR --> APA{Attack Path Analysis?}
  APA -- Yes --> AP[Analyze Attack Paths]
  APA -- No --> EX[Export/Report]
  AP --> EX

  classDef step fill:#0ea5e9,stroke:#0284c7,color:#fff
  class U,DFD,RV,TG,TR,AP,EX step
```

## Component Inventory (select)
- `pipeline/steps/agent-configuration-enhanced.tsx`: agent selection with health/metrics and animations.
- `pipeline/steps/enhanced-dfd-review.tsx`: editable DFD with validation and Mermaid.
- `pipeline/steps/threat-generation-step.tsx`: background execution and live progress.
- `components/ui/*`: consistent, accessible primitives.

## Accessibility & Responsiveness
- Responsive layout with modern affordances; keyboard focus visible; ARIA largely present in primitives.
- Further AA hardening planned (contrast audits, role labeling across admin tools).


