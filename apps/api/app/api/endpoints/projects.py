"""
Project and Session Management API Endpoints
Handles project creation, session management, loading, and branching.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.project_service import ProjectService
from app.dependencies import get_async_session
from app.models.project import Project, ProjectSession
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])

# === Pydantic Models ===

class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    tags: Optional[List[str]] = Field(None, description="Project tags for categorization")
    created_by: Optional[str] = Field(None, description="User who created the project")

class CreateSessionRequest(BaseModel):
    project_id: str = Field(..., description="Parent project ID")
    name: str = Field(..., min_length=1, max_length=255, description="Session name")
    description: Optional[str] = Field(None, max_length=1000, description="Session description")

class BranchSessionRequest(BaseModel):
    parent_session_id: str = Field(..., description="Parent session ID")
    branch_name: str = Field(..., min_length=1, max_length=255, description="New branch name")
    branch_point: str = Field(..., description="Pipeline step to branch from")
    description: Optional[str] = Field(None, description="Branch description")

class LoadSessionRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to load")
    create_branch: bool = Field(False, description="Create a new branch instead of loading directly")
    branch_name: Optional[str] = Field(None, description="Name for new branch if create_branch is True")

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    tags: Optional[List[str]]
    session_count: int
    latest_session: Optional[Dict[str, Any]]

class SessionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    project_id: str
    project_name: str
    parent_session_id: Optional[str]
    parent_session_name: Optional[str]
    branch_point: Optional[str]
    is_main_branch: bool
    status: str
    completion_percentage: int
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    document_name: Optional[str]
    total_threats_found: int
    risk_level_summary: Optional[Dict[str, int]]
    pipeline_id: Optional[str]
    session_path: str
    children_count: int

# === Dependency Injection ===

async def get_project_service(session: AsyncSession = Depends(get_async_session)) -> ProjectService:
    return ProjectService(session)

# === API Endpoints ===

@router.post("/", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    service: ProjectService = Depends(get_project_service)
):
    """
    🆕 Create a new threat modeling project.
    
    This is the starting point for any threat modeling analysis.
    Each project can contain multiple sessions for different analyses or iterations.
    """
    logger.info(f"🚀 === CREATE PROJECT API ===")
    logger.info(f"📝 Project name: '{request.name}'")
    logger.info(f"📄 Description: {len(request.description) if request.description else 0} chars")
    logger.info(f"🏷️ Tags: {request.tags}")
    
    try:
        project = await service.create_project(
            name=request.name,
            description=request.description,
            created_by=request.created_by,
            tags=request.tags
        )
        
        response = ProjectResponse(
            id=str(project.id),
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            created_by=project.created_by,
            tags=project.tags,
            session_count=0,
            latest_session=None
        )
        
        logger.info(f"✅ Project created successfully: {project.id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of projects to return"),
    offset: int = Query(0, ge=0, description="Number of projects to skip"),
    search: Optional[str] = Query(None, description="Search term for project names"),
    service: ProjectService = Depends(get_project_service)
):
    """
    📋 List all threat modeling projects with session summaries.
    
    Supports pagination and search functionality.
    Returns projects ordered by most recently updated.
    """
    logger.info(f"📋 === LIST PROJECTS API ===")
    logger.info(f"🔍 Search: '{search}', Limit: {limit}, Offset: {offset}")
    
    try:
        projects = await service.get_projects(limit=limit, offset=offset, search=search)
        
        responses = []
        for project in projects:
            # Get latest session info
            latest_session = None
            if project.sessions:
                latest = max(project.sessions, key=lambda s: s.updated_at or s.created_at)
                latest_session = {
                    "id": str(latest.id),
                    "name": latest.name,
                    "status": latest.status,
                    "completion_percentage": latest.completion_percentage,
                    "updated_at": latest.updated_at.isoformat() if latest.updated_at else latest.created_at.isoformat()
                }
            
            responses.append(ProjectResponse(
                id=str(project.id),
                name=project.name,
                description=project.description,
                created_at=project.created_at,
                updated_at=project.updated_at,
                created_by=project.created_by,
                tags=project.tags,
                session_count=len(project.sessions),
                latest_session=latest_session
            ))
        
        logger.info(f"✅ Retrieved {len(responses)} projects")
        return responses
        
    except Exception as e:
        logger.error(f"❌ Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")

@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project_details(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
):
    """
    🔍 Get detailed project information including session tree.
    
    Returns the project with a hierarchical view of all sessions,
    showing branching relationships and current status.
    """
    logger.info(f"🔍 === GET PROJECT DETAILS API ===")
    logger.info(f"📋 Project ID: {project_id}")
    
    try:
        project = await service.get_project(project_id)
        if not project:
            logger.warning(f"❌ Project not found: {project_id}")
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get session tree
        session_tree = await service.get_session_tree(project_id)
        
        response = {
            "project": {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "created_by": project.created_by,
                "tags": project.tags,
                "session_count": len(project.sessions)
            },
            "session_tree": session_tree
        }
        
        logger.info(f"✅ Project details retrieved: {len(project.sessions)} sessions")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get project details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project details: {str(e)}")

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    service: ProjectService = Depends(get_project_service)
):
    """
    🚀 Create a new threat modeling session within a project.
    
    This creates a new analysis session that will have its own pipeline.
    Can be used for different iterations or variations of the threat model.
    """
    logger.info(f"🚀 === CREATE SESSION API ===")
    logger.info(f"📋 Project ID: {request.project_id}")
    logger.info(f"📝 Session name: '{request.name}'")
    
    try:
        session = await service.create_session(
            project_id=request.project_id,
            name=request.name,
            description=request.description
        )
        
        response = SessionResponse(
            id=str(session.id),
            name=session.name,
            description=session.description,
            project_id=str(session.project_id),
            project_name=session.project.name if session.project else "Unknown",
            parent_session_id=None,
            parent_session_name=None,
            branch_point=None,
            is_main_branch=session.is_main_branch,
            status=session.status,
            completion_percentage=session.completion_percentage,
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at,
            document_name=session.document_name,
            total_threats_found=session.total_threats_found,
            risk_level_summary=session.risk_level_summary,
            pipeline_id=str(session.pipeline_id) if session.pipeline_id else None,
            session_path=session.session_path,
            children_count=0
        )
        
        logger.info(f"✅ Session created successfully: {session.id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.post("/sessions/branch", response_model=SessionResponse)
async def branch_session(
    request: BranchSessionRequest,
    service: ProjectService = Depends(get_project_service)
):
    """
    🌿 Create a new session branched from an existing session.
    
    This allows you to take an existing analysis and create variations
    from a specific point in the pipeline (e.g., after DFD extraction).
    """
    logger.info(f"🌿 === BRANCH SESSION API ===")
    logger.info(f"🔗 Parent session: {request.parent_session_id}")
    logger.info(f"📝 Branch name: '{request.branch_name}'")
    logger.info(f"📍 Branch point: {request.branch_point}")
    
    try:
        # Get parent session info
        parent_session = await service.get_session(request.parent_session_id)
        if not parent_session:
            raise HTTPException(status_code=404, detail="Parent session not found")
        
        # Create branch
        session = await service.create_session(
            project_id=str(parent_session.project_id),
            name=request.branch_name,
            description=request.description,
            parent_session_id=request.parent_session_id,
            branch_point=request.branch_point
        )
        
        response = SessionResponse(
            id=str(session.id),
            name=session.name,
            description=session.description,
            project_id=str(session.project_id),
            project_name=session.project.name if session.project else parent_session.project.name,
            parent_session_id=str(session.parent_session_id),
            parent_session_name=parent_session.name,
            branch_point=session.branch_point,
            is_main_branch=session.is_main_branch,
            status=session.status,
            completion_percentage=session.completion_percentage,
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at,
            document_name=session.document_name,
            total_threats_found=session.total_threats_found,
            risk_level_summary=session.risk_level_summary,
            pipeline_id=str(session.pipeline_id) if session.pipeline_id else None,
            session_path=session.session_path,
            children_count=0
        )
        
        logger.info(f"✅ Branch created successfully: {session.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to branch session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to branch session: {str(e)}")

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_details(
    session_id: str,
    service: ProjectService = Depends(get_project_service)
):
    """
    🔍 Get detailed information about a specific session.
    
    Returns complete session information including pipeline status,
    parent/child relationships, and progress metrics.
    """
    logger.info(f"🔍 === GET SESSION DETAILS API ===")
    logger.info(f"📋 Session ID: {session_id}")
    
    try:
        session = await service.get_session(session_id)
        if not session:
            logger.warning(f"❌ Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        response = SessionResponse(
            id=str(session.id),
            name=session.name,
            description=session.description,
            project_id=str(session.project_id),
            project_name=session.project.name if session.project else "Unknown",
            parent_session_id=str(session.parent_session_id) if session.parent_session_id else None,
            parent_session_name=session.parent_session.name if session.parent_session else None,
            branch_point=session.branch_point,
            is_main_branch=session.is_main_branch,
            status=session.status,
            completion_percentage=session.completion_percentage,
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at,
            document_name=session.document_name,
            total_threats_found=session.total_threats_found,
            risk_level_summary=session.risk_level_summary,
            pipeline_id=str(session.pipeline_id) if session.pipeline_id else None,
            session_path=session.session_path,
            children_count=len(session.child_sessions)
        )
        
        logger.info(f"✅ Session details retrieved: '{session.name}'")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get session details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session details: {str(e)}")

@router.post("/sessions/load")
async def load_session(
    request: LoadSessionRequest,
    service: ProjectService = Depends(get_project_service)
):
    """
    📂 Load an existing session for continued work.
    
    This retrieves the session's pipeline state and prepares it for
    continued analysis. Optionally creates a new branch.
    """
    logger.info(f"📂 === LOAD SESSION API ===")
    logger.info(f"📋 Session ID: {request.session_id}")
    logger.info(f"🌿 Create branch: {request.create_branch}")
    
    try:
        session = await service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # If creating a branch, create new session
        if request.create_branch:
            if not request.branch_name:
                raise HTTPException(status_code=400, detail="Branch name required when create_branch is True")
            
            # Create branch from the session's current state
            new_session = await service.create_session(
                project_id=str(session.project_id),
                name=request.branch_name,
                description=f"Branch from {session.name}",
                parent_session_id=str(session.id),
                branch_point="current_state"
            )
            
            # Copy pipeline if it exists
            if session.pipeline_id:
                # Get pipeline data and create new pipeline
                # This would need implementation in pipeline_service
                pass
            
            session_to_return = new_session
            logger.info(f"🌿 Created branch '{request.branch_name}' from session '{session.name}'")
        else:
            session_to_return = session
            logger.info(f"📂 Loading existing session '{session.name}'")
        
        # Return session data for frontend
        response = {
            "session": {
                "id": str(session_to_return.id),
                "name": session_to_return.name,
                "project_id": str(session_to_return.project_id),
                "project_name": session_to_return.project.name if session_to_return.project else "Unknown",
                "pipeline_id": str(session_to_return.pipeline_id) if session_to_return.pipeline_id else None,
                "is_branch": request.create_branch,
                "parent_session_name": session.name if request.create_branch else None
            },
            "pipeline_data": None  # Would be populated with actual pipeline data
        }
        
        logger.info(f"✅ Session loaded successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to load session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load session: {str(e)}")
