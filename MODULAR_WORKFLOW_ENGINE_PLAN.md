# Updated Developer's Plan: The Modular Workflow Engine

Version: 2025-08-08

This plan builds upon the project's existing enterprise-grade components, such as the modular agent system, Celery, and SQLAlchemy models.

## Phase 1: Foundational Data Models & Access Control

**Goal**: Establish the database schema to support workflows, versioned artifacts, and the distinction between Admin and User roles. This is the blueprint for everything that follows.

### Introduce Role-Based Access Control (RBAC):

**Action**: Modify the User model in `apps/api/app/models/user.py` to include a role field (e.g., an Enum with 'admin' and 'user' values).

**Why**: To control who can create and edit WorkflowTemplates versus who can only execute them.

### Create Workflow & Artifact Models:

**Action**: In a new file `apps/api/app/models/workflow.py`, define the following SQLAlchemy models:

#### WorkflowTemplate:
- `name`, `description`: For identification.
- `definition`: A JSONB field holding the workflow structure as a Directed Acyclic Graph (DAG). Example: 
  ```json
  {
    "steps": {
      "step1": {
        "agent_id": "...", 
        "depends_on": []
      }, 
      "step2": {
        "agent_id": "...", 
        "depends_on": ["step1"]
      }
    }
  }
  ```
- `created_by`: ForeignKey to User.

#### WorkflowRun:
- `template_id`: ForeignKey to WorkflowTemplate (for auditing where it came from).
- `run_definition`: A JSONB field containing a copy of the template's definition at the time of creation.
- `status`: String Enum (running, paused, completed, failed).
- `user_id`: ForeignKey to User.

#### Artifact:
- `run_id`: ForeignKey to WorkflowRun.
- `producing_step_id`: The ID of the step that created this artifact (e.g., "step1").
- `name`: The name of the output (e.g., "cleaned_text").
- `version`: Integer, auto-incrementing for each new version of this artifact within the run.
- `content`: A JSONB or LargeBinary field to store the artifact's data.
- `is_latest`: Boolean flag to easily find the most recent version.

**Why**: Storing the run_definition separately allows for run-specific customizations without altering the original template. The versioned Artifact model is crucial for enabling the "rollback and retry" functionality you requested.

### Run Database Migration:

**Action**: Use Alembic to generate and apply the migration for the new models.

```bash
alembic revision --autogenerate -m "Add workflow engine and versioned artifact models"
alembic upgrade head
```

**Why**: This safely updates the production database schema.

---

## Phase 2: Core Engine - Sequential Workflow Execution

**Goal**: Build the backend logic to execute a simple, linear workflow. This proves the core concept of an agent consuming an artifact and producing a new one.

### Create WorkflowService:

**Action**: In `apps/api/app/services/`, create `workflow_service.py`. It will contain the initial business logic.

- `start_run(template_id, user)`: Copies the template definition to a new WorkflowRun and kicks off the first step(s).
- `get_run_status(run_id)`: Retrieves the current state of a run and its artifacts.
- `trigger_step(run_id, step_id, user_prompt_override=None)`: The manual trigger for a step.

**Why**: This service encapsulates all workflow-related logic, keeping the API endpoints clean.

### Create workflow_tasks.py Celery Task:

**Action**: In `apps/api/app/tasks/`, create a new task file.

Define `execute_agent_on_artifact(run_id, step_id, prompt_override)`:
- Fetches the latest versions of the required input artifacts for the step_id from the database.
- Invokes the correct agent (using the existing agent registry).
- Saves the output as a new versioned Artifact row, marking it as the `is_latest`.
- Sends a WebSocket notification about the step completion.

**Why**: Utilizes the existing scalable background processing system to handle potentially long-running agent tasks.

### Implement Basic Workflow API Endpoints:

**Action**: In `apps/api/app/api/endpoints/`, create `workflows.py`.

- `POST /api/workflows/runs`: (User) Starts a new workflow run from a template.
- `GET /api/workflows/runs/{run_id}`: (User) Gets the status and artifacts for a run.
- `POST /api/workflows/runs/{run_id}/steps/{step_id}/trigger`: (User) Manually triggers a step, allowing for a prompt override.

**Why**: Provides the necessary interface for the frontend to interact with the engine.

---

## Phase 3: Admin UI - The Workflow Builder

**Goal**: Create the "from scratch" workflow definition tool, accessible only to admins.

### Build Template Management UI:

**Action**: Create a new section in the frontend (e.g., `/admin/workflows`) that is only visible to users with the 'admin' role. This section will list, create, and edit WorkflowTemplates.

**Why**: Fulfills the requirement for an admin-specific creation tool.

### Develop the Visual DAG Editor:

**Action**: The core of the admin UI will be a canvas where admins can:
- Drag and drop agents from a library.
- Draw connections between agent nodes to define dependencies (depends_on).
- Configure each node (step), which includes the crucial input mapping. For each input an agent requires, the admin will see a dropdown of all available artifacts produced by its predecessor nodes.

**Why**: This visual tool is essential for managing the complexity of DAGs and flexible input mappings, making it intuitive for admins.

### Implement Admin API Endpoints:

**Action**: Add admin-only endpoints to `workflows.py`.

- `POST /api/workflows/templates`: Creates a template from the DAG definition.
- `PUT /api/workflows/templates/{template_id}`: Updates a template.
- `GET /api/agents/list`: This existing endpoint will be used to populate the agent library in the UI.

**Why**: To save and manage the templates created by admins.

---

## Phase 4: User UI - Workflow Execution & Dashboard

**Goal**: Create the user-facing interface for running workflows and reviewing results.

### Build the Workflow Dashboard:

**Action**: Create a main `/dashboard` page where users can:
- See a gallery of available WorkflowTemplates.
- Click "Start" on a template to create a new WorkflowRun.
- View a list of their ongoing and completed runs.

**Why**: Provides the primary entry point for users to interact with the system.

### Develop the Workflow Run View:

**Action**: Create the page for viewing a single WorkflowRun.
- It will dynamically render the workflow's DAG, showing the status of each node (pending, running, awaiting_review, completed).
- It will feature a master "Auto-run next steps" toggle.
- Clicking a completed step allows the user to view the artifact(s) it produced. If a step is in awaiting_review, the user sees a "Continue" button. If it fails, they see a "Retry" button, which could pop up a modal to modify the prompt.

**Why**: This is the core user experience, providing transparency and the manual control you specified.

---

## Phase 5: Advanced Engine - Parallel & Fan-In Execution

**Goal**: Enhance the backend engine to fully support the DAG model defined in Phase 1, including parallel execution.

### Evolve the WorkflowService:

**Action**: Update the WorkflowService to be DAG-aware.
- When a step completes, the service will now check the run_definition to find all steps that were dependent on the one that just finished.
- For each of these subsequent steps, it checks if all other dependencies have also been met.

**Why**: This logic is the brain of the DAG execution, deciding what can be run next.

### Leverage Advanced Celery Patterns:

**Action**: Update the `workflow_tasks.py` and WorkflowService to use Celery's group and chord primitives.

- **group**: When multiple steps can run in parallel (fan-out), the engine will launch them as a Celery group.
- **chord**: For a fan-in scenario (e.g., Agent 4 needs output from both Agent 2 and 3), the engine will use a Celery chord. The parallel tasks (2 and 3) are the chord's header, and the fan-in task (4) is the callback that only executes when all header tasks are complete.

**Why**: This is the technically correct and most efficient way to implement parallel and fan-in logic using your existing, powerful Celery infrastructure.

---

## Implementation Benefits

1. **Leverages Existing Infrastructure**: Uses the current modular agent system, Celery background processing, and SQLAlchemy models.

2. **Versioned Artifact System**: Enables rollback and retry functionality with full audit trail.

3. **Role-Based Access**: Clear separation between admin (workflow creators) and users (workflow executors).

4. **Scalable Architecture**: Built on proven enterprise patterns with Celery for background processing.

5. **Visual DAG Management**: Intuitive admin interface for creating complex workflows.

6. **Flexible Execution**: Supports both manual step-by-step execution and automated workflows.

---

## Current State Integration

This plan builds upon:
- ✅ Existing modular agent system
- ✅ Current Celery background processing
- ✅ SQLAlchemy database models
- ✅ WebSocket notifications
- ✅ RBAC foundation
- ✅ Robust database connection management

## Next Steps

1. **Phase 1 Implementation**: Start with database schema and RBAC enhancements
2. **Backend Core**: Implement WorkflowService and basic execution engine
3. **API Layer**: Create workflow management endpoints
4. **Frontend Development**: Build admin workflow builder UI
5. **User Experience**: Implement execution dashboard and monitoring