"""
Phase 1 Workflow API Endpoints

Demonstrates basic CRUD operations for workflow templates and runs.
Part of the Modular Workflow Engine Phase 1 implementation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from app.dependencies import get_db
from app.models.workflow import WorkflowTemplate, WorkflowRun, WorkflowStatus
from app.models.rbac import PermissionType
from app.models import User


router = APIRouter(prefix="/workflow", tags=["workflow-phase1"])


@router.get("/status")
async def get_phase1_status():
    """
    Get Phase 1 implementation status and available features.
    Public endpoint for testing Phase 1 completion.
    """
    return {
        "phase": "Phase 1: Foundation",
        "status": "COMPLETE",
        "features": {
            "database_schema": "✅ Implemented with defensive constraints",
            "workflow_models": "✅ WorkflowTemplate, WorkflowRun, WorkflowStepExecution, WorkflowArtifact",
            "rbac_integration": "✅ 10 workflow permissions integrated",
            "versioned_artifacts": "✅ Rollback and retry capability",
            "audit_trails": "✅ Template definition snapshots",
            "defensive_programming": "✅ Comprehensive validation and constraints"
        },
        "available_endpoints": {
            "GET /workflow/status": "This status endpoint",
            "GET /workflow/templates/count": "Count workflow templates",
            "GET /workflow/runs/count": "Count workflow runs", 
            "GET /workflow/permissions": "List workflow permissions"
        },
        "models": {
            "WorkflowTemplate": "Admin-managed DAG definitions",
            "WorkflowRun": "Individual workflow executions", 
            "WorkflowStepExecution": "Granular step tracking",
            "WorkflowArtifact": "Versioned artifact storage"
        },
        "next_phase": "Phase 2: Core Engine - Sequential Workflow Execution"
    }


@router.get("/templates/count")
async def get_templates_count(db: AsyncSession = Depends(get_db)):
    """
    Get count of workflow templates.
    Demonstrates database connectivity and model access.
    """
    try:
        from sqlalchemy import select
        result = await db.execute(select(func.count(WorkflowTemplate.id)))
        count = result.scalar()
        return {
            "count": count,
            "message": f"Found {count} workflow templates in database",
            "phase1_status": "Database schema and models working correctly"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.get("/runs/count") 
async def get_runs_count(db: AsyncSession = Depends(get_db)):
    """
    Get count of workflow runs.
    Demonstrates database connectivity and model relationships.
    """
    try:
        from sqlalchemy import select
        
        # Get total count
        result = await db.execute(select(func.count(WorkflowRun.id)))
        count = result.scalar()
        
        # Get status breakdown
        status_result = await db.execute(
            select(WorkflowRun.status, func.count(WorkflowRun.id))
            .group_by(WorkflowRun.status)
        )
        status_counts = status_result.all()
        
        return {
            "total_count": count,
            "status_breakdown": {status: count for status, count in status_counts},
            "available_statuses": [s.value for s in WorkflowStatus],
            "message": f"Found {count} workflow runs in database"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.get("/permissions")
async def get_workflow_permissions():
    """
    List all workflow-related permissions.
    Demonstrates RBAC integration.
    """
    workflow_perms = []
    for attr in dir(PermissionType):
        if attr.startswith('WORKFLOW_'):
            perm_value = getattr(PermissionType, attr)
            workflow_perms.append({
                "name": attr,
                "value": perm_value,
                "description": _get_permission_description(perm_value)
            })
    
    return {
        "count": len(workflow_perms),
        "permissions": workflow_perms,
        "rbac_integration": "✅ Workflow permissions integrated with existing RBAC system"
    }


def _get_permission_description(perm_value: str) -> str:
    """Helper to get human-readable permission descriptions."""
    descriptions = {
        "workflow_template:create": "Create new workflow templates (Admin only)",
        "workflow_template:view": "View workflow template definitions",
        "workflow_template:edit": "Modify existing workflow templates (Admin only)", 
        "workflow_template:delete": "Delete workflow templates (Admin only)",
        "workflow_run:create": "Start new workflow executions",
        "workflow_run:view": "View workflow execution status and history",
        "workflow_run:control": "Start, stop, pause workflow executions",
        "workflow_run:delete": "Delete workflow execution records",
        "workflow_artifact:view": "View workflow artifacts and results",
        "workflow_artifact:download": "Download workflow artifacts"
    }
    return descriptions.get(perm_value, "Workflow permission")


@router.get("/models/info")
async def get_models_info():
    """
    Get information about Phase 1 workflow models.
    Demonstrates model introspection and defensive programming features.
    """
    return {
        "models": {
            "WorkflowTemplate": {
                "description": "Reusable DAG structures for admin-managed workflows",
                "key_features": [
                    "Immutable after creation (versioning for changes)",
                    "JSON validation for DAG structure",
                    "Category-based organization",
                    "Access control integration"
                ],
                "defensive_features": [
                    "Name length validation (minimum 3 characters)",
                    "DAG structure validation",
                    "Version constraints",
                    "Foreign key relationships"
                ]
            },
            "WorkflowRun": {
                "description": "Individual workflow execution instances",
                "key_features": [
                    "Audit trail with template snapshot",
                    "Retry mechanisms with configurable limits",
                    "Progress tracking",
                    "Error handling and diagnostics"
                ],
                "defensive_features": [
                    "Status transition validation",
                    "Timeout enforcement", 
                    "Step count validation",
                    "UUID-based run identification"
                ]
            },
            "WorkflowStepExecution": {
                "description": "Granular step-level execution tracking",
                "key_features": [
                    "Agent-specific execution details",
                    "Input/output artifact tracking",
                    "Individual step retry capability",
                    "Performance metrics"
                ]
            },
            "WorkflowArtifact": {
                "description": "Versioned artifact storage with rollback capability", 
                "key_features": [
                    "Multiple content types (JSON, text, binary)",
                    "Version management with 'latest' flags",
                    "Content integrity checking (SHA-256)",
                    "Automatic expiration support"
                ],
                "defensive_features": [
                    "Content type validation",
                    "Size tracking",
                    "Single content field enforcement",
                    "Version numbering validation"
                ]
            }
        },
        "database_constraints": {
            "check_constraints": "Status validation, positive numbers, length validation",
            "unique_constraints": "Template name/version, artifact versioning", 
            "foreign_keys": "User relationships, template references",
            "indexes": "Performance optimization for common queries"
        }
    }