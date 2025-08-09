"""
Phase 2: Core Workflow Engine API Endpoints
Provides REST API for workflow template management and execution.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel, Field

from app.dependencies import get_db
from app.models import User
from app.models.workflow import WorkflowTemplate, WorkflowRun, WorkflowStatus, WorkflowArtifact
from app.services.workflow_service import WorkflowService, WorkflowExecutionError
from app.tasks.workflow_tasks import execute_workflow_run, execute_workflow_step
from app.api.v1.auth import get_current_user
from app.models.rbac import PermissionType
from app.core.agents.registry import agent_registry
from app.core.agents.base import AgentExecutionContext

async def check_permission(db: AsyncSession, user: Optional[User], permission: PermissionType) -> bool:
    """Phase 2 permission check with relaxed rules for demo UX.

    - Superusers/admins have all permissions
    - Read-only permissions are allowed for everyone (unauth included)
    - Run creation/control is allowed for any authenticated user
    - Template creation/edit/delete remains admin-only
    """
    # Superusers/admins have all permissions
    if user and (getattr(user, "is_admin", False) or getattr(user, "is_superuser", False)):
        return True

    # Read permissions (allow for everyone in Phase 2 demo)
    read_permissions = [
        PermissionType.WORKFLOW_TEMPLATE_VIEW,
        PermissionType.WORKFLOW_RUN_VIEW,
        PermissionType.WORKFLOW_ARTIFACT_VIEW,
    ]
    if permission in read_permissions:
        return True

    # Allow authenticated users to start/control their runs in Phase 2
    user_write_permissions_relaxed = [
        PermissionType.WORKFLOW_RUN_CREATE,
        PermissionType.WORKFLOW_RUN_CONTROL,
    ]
    if permission in user_write_permissions_relaxed and user is not None:
        return True

    return False

router = APIRouter(prefix="/phase2/workflow", tags=["workflow-phase2"])

# Pydantic models for requests/responses
class WorkflowTemplateCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    definition: Dict[str, Any] = Field(..., description="DAG definition with steps")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Simple Sequential Workflow",
                "description": "A basic workflow demonstrating sequential execution",
                "category": "demo",
                "definition": {
                    "steps": {
                        "analyze": {
                            "agent_type": "document_analysis",
                            "config": {"depth": "basic"},
                            "depends_on": []
                        },
                        "assess_risk": {
                            "agent_type": "risk_assessment",
                            "config": {"threshold": 0.7},
                            "depends_on": ["analyze"]
                        },
                        "generate_report": {
                            "agent_type": "report_generator",
                            "config": {"format": "pdf"},
                            "depends_on": ["assess_risk"]
                        }
                    }
                }
            }
        }


class WorkflowRunStart(BaseModel):
    # Template primary key is integer in DB
    template_id: int
    initial_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    auto_execute: bool = Field(False, description="Automatically start execution")


class WorkflowStepTrigger(BaseModel):
    prompt_override: Optional[str] = Field(None, description="Override prompt for agent")


class WorkflowTemplateResponse(BaseModel):
    # Template primary key is integer in DB
    id: int
    name: str
    description: str
    category: Optional[str]
    version: str
    is_active: bool
    created_at: str
    steps_count: int


class WorkflowRunResponse(BaseModel):
    # Run primary key is integer; run_id is UUID string field
    id: int
    run_id: str
    template_id: int
    status: str
    progress: float
    total_steps: int
    completed_steps: int
    started_at: Optional[str]
    completed_at: Optional[str]
    can_retry: bool
    is_terminal: bool


# Initialize service
workflow_service = WorkflowService()


@router.post("/templates", response_model=WorkflowTemplateResponse)
async def create_workflow_template(
    template: WorkflowTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new workflow template (Admin only).
    Validates DAG structure and agent availability.
    """
    # Check permission
    if not await check_permission(db, current_user, PermissionType.WORKFLOW_TEMPLATE_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create workflow templates"
        )
    
    try:
        template_obj = await workflow_service.create_template(
            db=db,
            name=template.name,
            description=template.description,
            definition=template.definition,
            user=current_user,
            category=template.category
        )
        
        return WorkflowTemplateResponse(
            id=template_obj.id,
            name=template_obj.name,
            description=template_obj.description,
            category=template_obj.category,
            version=template_obj.version,
            is_active=template_obj.is_active,
            created_at=template_obj.created_at.isoformat(),
            steps_count=len(template_obj.definition.get('steps', {}))
        )
        
    except WorkflowExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/templates", response_model=List[WorkflowTemplateResponse])
async def list_workflow_templates(
    category: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    List available workflow templates.
    """
    # Check permission
    if not await check_permission(db, current_user, PermissionType.WORKFLOW_TEMPLATE_VIEW):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view workflow templates"
        )
    
    query = select(WorkflowTemplate)
    
    conditions = []
    if active_only:
        conditions.append(WorkflowTemplate.is_active == True)
    if category:
        conditions.append(WorkflowTemplate.category == category)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [
        WorkflowTemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            category=t.category,
            version=t.version,
            is_active=t.is_active,
            created_at=t.created_at.isoformat(),
            steps_count=len(t.definition.get('steps', {}))
        )
        for t in templates
    ]


@router.get("/templates/{template_id}")
async def get_workflow_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get detailed workflow template including DAG definition.
    """
    # Check permission
    if not await check_permission(db, current_user, PermissionType.WORKFLOW_TEMPLATE_VIEW):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view workflow templates"
        )
    
    result = await db.execute(
        select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Get execution order
    execution_order = workflow_service.dag_validator.get_execution_order(template.definition)
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "version": template.version,
        "is_active": template.is_active,
        "created_at": template.created_at.isoformat(),
        "definition": template.definition,
        "execution_order": execution_order,
        "steps_count": len(template.definition.get('steps', {}))
    }


@router.post("/templates/seed-demo")
async def seed_demo_template(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Create a demo workflow template with a simple 3-step DAG.
    Phase 2 demo convenience endpoint: allowed without authentication.
    """
    try:
        # Ensure agents are discovered so validation passes
        try:
            agent_registry.discover_agents()
        except Exception:
            pass
        definition: Dict[str, Any] = {
            "steps": {
                "dfd_extraction": {
                    "agent_type": "dfd_extractor",
                    "config": {},
                    "depends_on": []
                }
            }
        }
        # Determine creator (fallback to first user if no auth user provided)
        creator: Optional[User] = current_user
        if creator is None:
            from sqlalchemy import select as _select
            res_user = await db.execute(_select(User).limit(1))
            creator = res_user.scalar_one_or_none()
            if creator is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No user found to assign as template creator. Create an admin user first."
                )

        template_obj = await workflow_service.create_template(
            db=db,
            name="DFD Extractor (Single-step)",
            description="Single-step workflow using the DFD Extractor agent",
            definition=definition,
            user=creator,
            category="demo"
        )

        return WorkflowTemplateResponse(
            id=template_obj.id,
            name=template_obj.name,
            description=template_obj.description,
            category=template_obj.category,
            version=template_obj.version,
            is_active=template_obj.is_active,
            created_at=template_obj.created_at.isoformat(),
            steps_count=len(template_obj.definition.get("steps", {}))
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed demo template: {str(e)}"
        )


@router.post("/runs/start", response_model=WorkflowRunResponse)
async def start_workflow_run(
    request: WorkflowRunStart,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a new workflow run from a template.
    """
    # Check permission
    if not await check_permission(db, current_user, PermissionType.WORKFLOW_RUN_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create workflow runs"
        )
    
    try:
        run = await workflow_service.start_run(
            db=db,
            template_id=request.template_id,
            user=current_user,
            initial_context=request.initial_context
        )
        
        # Optionally trigger automatic execution
        if request.auto_execute:
            background_tasks.add_task(
                execute_workflow_run.apply_async,
                args=[str(run.id)]
            )
        
        return WorkflowRunResponse(
            id=run.id,
            run_id=str(run.run_id),
            template_id=run.template_id,
            status=run.status.value if hasattr(run.status, "value") else run.status,
            progress=run.get_progress_percentage(),
            total_steps=run.total_steps,
            completed_steps=run.completed_steps,
            started_at=run.started_at.isoformat() if run.started_at else None,
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
            can_retry=run.can_retry(),
            is_terminal=run.is_terminal()
        )
        
    except WorkflowExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/runs/{run_id}/status")
async def get_workflow_run_status(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed status of a workflow run including all steps.
    """
    # Check permission
    if not await check_permission(db, current_user, PermissionType.WORKFLOW_RUN_VIEW):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view workflow runs"
        )
    
    try:
        status_info = await workflow_service.get_run_status(db, run_id)
        return status_info
    except WorkflowExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/runs/{run_id}/artifacts")
async def list_run_artifacts(
    run_id: UUID,
    include_content: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    List artifacts for a workflow run. Optionally include content for small JSON/text artifacts.
    """
    # View permission (allow for all in Phase 2 demo)
    if not await check_permission(db, current_user, PermissionType.WORKFLOW_ARTIFACT_VIEW):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to view artifacts")

    result = await db.execute(select(WorkflowRun).where(WorkflowRun.run_id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    artifacts_result = await db.execute(select(WorkflowArtifact).where(WorkflowArtifact.run_id == run.id))
    rows = list(artifacts_result.scalars().all())

    items = []
    for a in rows:
        item = {
            "name": a.name,
            "artifact_type": a.artifact_type,
            "version": a.version,
            "is_latest": a.is_latest,
            "size_bytes": a.size_bytes,
        }
        if include_content:
            content = a.get_content()
            # Only include content if JSON/text small (< 128KB)
            try:
                import json as _json
                if isinstance(content, (dict, list)):
                    payload = _json.dumps(content)
                    if len(payload.encode("utf-8")) <= 131072:
                        item["content_json"] = content
                elif isinstance(content, str) and len(content.encode("utf-8")) <= 131072:
                    item["content_text"] = content
            except Exception:
                pass
        items.append(item)

    return {"artifacts": items}


@router.get("/runs/{run_id}/artifacts/{artifact_name}")
async def get_run_artifact(
    run_id: UUID,
    artifact_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get a specific artifact by name (latest version).
    """
    if not await check_permission(db, current_user, PermissionType.WORKFLOW_ARTIFACT_VIEW):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to view artifacts")

    result = await db.execute(select(WorkflowRun).where(WorkflowRun.run_id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    art_query = select(WorkflowArtifact).where(
        and_(WorkflowArtifact.run_id == run.id, WorkflowArtifact.name == artifact_name, WorkflowArtifact.is_latest == True)
    )
    art_res = await db.execute(art_query)
    artifact = art_res.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    content = artifact.get_content()
    if isinstance(content, (dict, list)):
        return {"name": artifact.name, "artifact_type": artifact.artifact_type, "content": content}
    elif isinstance(content, str):
        return {"name": artifact.name, "artifact_type": artifact.artifact_type, "content": content}
    else:
        # For binary, return metadata only
        return {"name": artifact.name, "artifact_type": artifact.artifact_type, "size_bytes": artifact.size_bytes}

@router.post("/runs/{run_id}/execute-next")
async def execute_next_step(
    run_id: UUID,
    request: WorkflowStepTrigger = WorkflowStepTrigger(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute the next pending step in a workflow run.
    """
    # Check permission
    if not await check_permission(db, current_user, PermissionType.WORKFLOW_RUN_CONTROL):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to control workflow runs"
        )
    
    try:
        executed_step = await workflow_service.execute_next_step(
            db=db,
            run_id=run_id,
            user_prompt_override=request.prompt_override
        )
        
        if not executed_step:
            return {
                "status": "no_steps_ready",
                "message": "No steps are ready for execution"
            }
        
        return {
            "status": "success",
            "executed_step": {
                "step_id": executed_step.step_id,
                "agent_type": executed_step.agent_type,
                "status": executed_step.status.value,
                "execution_time_ms": executed_step.execution_time_ms
            }
        }
        
    except WorkflowExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/runs/{run_id}/execute-async")
async def execute_workflow_async(
    run_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start asynchronous execution of a workflow run.
    """
    # Check permission
    if not await check_permission(db, current_user, PermissionType.WORKFLOW_RUN_CONTROL):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to control workflow runs"
        )
    
    # Verify run exists and is in valid state
    result = await db.execute(
        select(WorkflowRun).where(WorkflowRun.run_id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow run not found"
        )
    
    if run.status not in [WorkflowStatus.CREATED, WorkflowStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot execute run in {run.status} state"
        )
    
    # Trigger async execution
    task = execute_workflow_run.apply_async(args=[str(run_id)])
    
    return {
        "status": "triggered",
        "run_id": str(run_id),
        "task_id": task.id,
        "message": "Workflow execution started asynchronously"
    }


@router.post("/runs/{run_id}/cancel")
async def cancel_workflow_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a running workflow.
    """
    # Check permission
    if not await check_permission(db, current_user, PermissionType.WORKFLOW_RUN_CONTROL):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to control workflow runs"
        )
    
    try:
        run = await workflow_service.cancel_run(db, run_id)
        
        return {
            "status": "cancelled",
            "run_id": str(run.run_id),
            "message": "Workflow run cancelled successfully"
        }
        
    except WorkflowExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/runs", response_model=List[WorkflowRunResponse])
async def list_workflow_runs(
    status_filter: Optional[WorkflowStatus] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    List workflow runs with optional filtering.
    """
    # Check permission
    if not await check_permission(db, current_user, PermissionType.WORKFLOW_RUN_VIEW):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view workflow runs"
        )
    
    query = select(WorkflowRun)
    
    # Add filters
    if status_filter:
        query = query.where(WorkflowRun.status == status_filter)
    
    # Add user filter for non-admins when authenticated
    if current_user and not getattr(current_user, "is_admin", False):
        query = query.where(WorkflowRun.user_id == current_user.id)
    
    # Add ordering and pagination
    query = query.order_by(WorkflowRun.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    runs = result.scalars().all()
    
    return [
        WorkflowRunResponse(
            id=run.id,
            run_id=str(run.run_id),
            template_id=run.template_id,
            status=run.status.value if hasattr(run.status, "value") else run.status,
            progress=run.get_progress_percentage(),
            total_steps=run.total_steps,
            completed_steps=run.completed_steps,
            started_at=run.started_at.isoformat() if run.started_at else None,
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
            can_retry=run.can_retry(),
            is_terminal=run.is_terminal()
        )
        for run in runs
    ]


@router.get("/phase2/status")
async def get_phase2_status():
    """
    Get Phase 2 implementation status.
    """
    return {
        "phase": "Phase 2: Core Engine",
        "status": "COMPLETE",
        "features": {
            "workflow_service": "✅ WorkflowService with DAG validation",
            "dag_validator": "✅ Cycle detection and topological sorting",
            "step_execution": "✅ Sequential execution with dependency resolution",
            "artifact_management": "✅ Input/output artifacts between steps",
            "retry_logic": "✅ Configurable retry with exponential backoff",
            "async_execution": "✅ Celery tasks for background processing",
            "state_management": "✅ Persistent state with progress tracking"
        },
        "endpoints": {
            "POST /templates": "Create workflow template",
            "GET /templates": "List templates",
            "GET /templates/{id}": "Get template details",
            "POST /runs/start": "Start workflow run",
            "GET /runs/{id}/status": "Get run status",
            "POST /runs/{id}/execute-next": "Execute next step",
            "POST /runs/{id}/execute-async": "Start async execution",
            "POST /runs/{id}/cancel": "Cancel run",
            "GET /runs": "List runs"
        },
        "capabilities": {
            "dag_validation": "Validates workflow definitions for cycles and missing dependencies",
            "dependency_resolution": "Automatically determines execution order",
            "parallel_ready": "Foundation for parallel execution in Phase 4",
            "error_recovery": "Retry logic with exponential backoff",
            "progress_tracking": "Real-time progress updates"
        },
        "next_phase": "Phase 3: Basic UI - Client Portal for workflow execution"
    }