"""
Project and Session Management Service
Handles project creation, session management, branching, and loading.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import selectinload, joinedload

from app.models.project import Project, ProjectSession, SessionSnapshot
from app.models.pipeline import Pipeline, PipelineStatus
from app.services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing threat modeling projects and sessions."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.pipeline_service = PipelineService(session)
    
    async def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Project:
        """
        Create a new threat modeling project.
        
        Args:
            name: Project name
            description: Optional project description
            created_by: User who created the project
            tags: Optional tags for categorization
            
        Returns:
            Created project
        """
        logger.info(f"🆕 Creating new project: '{name}'")
        
        project = Project(
            name=name,
            description=description,
            created_by=created_by,
            tags=tags or []
        )
        
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        
        logger.info(f"✅ Project created successfully: {project.id}")
        return project
    
    async def get_projects(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Project]:
        """
        Get all projects with optional search and pagination.
        
        Args:
            limit: Maximum number of projects to return
            offset: Number of projects to skip
            search: Optional search term for project names
            
        Returns:
            List of projects with session counts
        """
        logger.info(f"📋 Fetching projects (limit: {limit}, offset: {offset}, search: '{search}')")
        
        query = select(Project).options(
            selectinload(Project.sessions)
        ).order_by(desc(Project.updated_at))
        
        if search:
            query = query.where(Project.name.ilike(f"%{search}%"))
        
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        projects = result.scalars().all()
        
        logger.info(f"✅ Retrieved {len(projects)} projects")
        return projects
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID with all sessions."""
        logger.info(f"🔍 Fetching project: {project_id}")
        
        query = select(Project).options(
            selectinload(Project.sessions).selectinload(ProjectSession.child_sessions),
            selectinload(Project.sessions).selectinload(ProjectSession.parent_session)
        ).where(Project.id == project_id)
        
        result = await self.session.execute(query)
        project = result.scalar_one_or_none()
        
        if project:
            logger.info(f"✅ Project found: '{project.name}' with {len(project.sessions)} sessions")
        else:
            logger.warning(f"❌ Project not found: {project_id}")
        
        return project
    
    async def create_session(
        self,
        project_id: str,
        name: str,
        description: Optional[str] = None,
        parent_session_id: Optional[str] = None,
        branch_point: Optional[str] = None
    ) -> ProjectSession:
        """
        Create a new session within a project.
        
        Args:
            project_id: Parent project ID
            name: Session name
            description: Optional session description
            parent_session_id: Optional parent session for branching
            branch_point: Pipeline step where branching occurred
            
        Returns:
            Created session
        """
        logger.info(f"🚀 Creating new session: '{name}' in project {project_id}")
        
        # Verify project exists
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Verify parent session if provided
        parent_session = None
        if parent_session_id:
            parent_session = await self.get_session(parent_session_id)
            if not parent_session:
                raise ValueError(f"Parent session {parent_session_id} not found")
            logger.info(f"🌿 Creating branch from session '{parent_session.name}' at step '{branch_point}'")
        
        # Determine if this is main branch
        is_main_branch = parent_session_id is None
        if not is_main_branch and parent_session:
            # Check if parent was main branch and this is first child
            children_count = len(parent_session.child_sessions)
            is_main_branch = parent_session.is_main_branch and children_count == 0
        
        session = ProjectSession(
            project_id=project_id,
            name=name,
            description=description,
            parent_session_id=parent_session_id,
            branch_point=branch_point,
            is_main_branch=is_main_branch
        )
        
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        
        logger.info(f"✅ Session created successfully: {session.id} (main_branch: {is_main_branch})")
        return session
    
    async def get_session(self, session_id: str) -> Optional[ProjectSession]:
        """Get a session by ID with related data."""
        logger.info(f"🔍 Fetching session: {session_id}")
        
        query = select(ProjectSession).options(
            joinedload(ProjectSession.project),
            joinedload(ProjectSession.pipeline),
            joinedload(ProjectSession.parent_session),
            selectinload(ProjectSession.child_sessions)
        ).where(ProjectSession.id == session_id)
        
        result = await self.session.execute(query)
        session = result.scalar_one_or_none()
        
        if session:
            logger.info(f"✅ Session found: '{session.name}' in project '{session.project.name}'")
        else:
            logger.warning(f"❌ Session not found: {session_id}")
        
        return session
    
    async def get_project_sessions(
        self,
        project_id: str,
        include_archived: bool = False
    ) -> List[ProjectSession]:
        """Get all sessions for a project in chronological order."""
        logger.info(f"📂 Fetching sessions for project: {project_id}")
        
        query = select(ProjectSession).options(
            joinedload(ProjectSession.parent_session),
            selectinload(ProjectSession.child_sessions)
        ).where(ProjectSession.project_id == project_id)
        
        if not include_archived:
            query = query.where(ProjectSession.status != 'archived')
        
        query = query.order_by(ProjectSession.created_at)
        
        result = await self.session.execute(query)
        sessions = result.scalars().all()
        
        logger.info(f"✅ Retrieved {len(sessions)} sessions")
        return sessions
    
    async def link_session_to_pipeline(
        self,
        session_id: str,
        pipeline_id: str
    ) -> ProjectSession:
        """Link a session to a pipeline."""
        logger.info(f"🔗 Linking session {session_id} to pipeline {pipeline_id}")
        
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.pipeline_id = pipeline_id
        session.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        logger.info(f"✅ Session linked to pipeline successfully")
        return session
    
    async def update_session_progress(
        self,
        session_id: str,
        completion_percentage: Optional[int] = None,
        status: Optional[str] = None,
        document_name: Optional[str] = None,
        document_size: Optional[int] = None,
        total_threats: Optional[int] = None,
        risk_summary: Optional[Dict[str, int]] = None
    ) -> ProjectSession:
        """Update session progress and metadata."""
        logger.info(f"📊 Updating session progress: {session_id}")
        
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Update provided fields
        if completion_percentage is not None:
            session.completion_percentage = completion_percentage
            logger.info(f"📈 Progress updated: {completion_percentage}%")
        
        if status is not None:
            session.status = status
            if status == "completed":
                session.completed_at = datetime.utcnow()
            logger.info(f"📋 Status updated: {status}")
        
        if document_name is not None:
            session.document_name = document_name
            
        if document_size is not None:
            session.document_size = document_size
            
        if total_threats is not None:
            session.total_threats_found = total_threats
            logger.info(f"🎯 Threats updated: {total_threats}")
            
        if risk_summary is not None:
            session.risk_level_summary = risk_summary
            logger.info(f"⚠️ Risk summary updated: {risk_summary}")
        
        session.updated_at = datetime.utcnow()
        await self.session.commit()
        
        logger.info(f"✅ Session progress updated successfully")
        return session
    
    async def create_session_snapshot(
        self,
        session_id: str,
        step_name: str,
        pipeline_state: Dict[str, Any],
        step_results: Optional[Dict[str, Any]] = None,
        snapshot_name: Optional[str] = None,
        created_by_action: str = "auto_save"
    ) -> SessionSnapshot:
        """Create a snapshot of session state at a specific step."""
        logger.info(f"📸 Creating snapshot for session {session_id} at step '{step_name}'")
        
        snapshot = SessionSnapshot(
            session_id=session_id,
            step_name=step_name,
            snapshot_name=snapshot_name,
            pipeline_state=pipeline_state,
            step_results=step_results,
            created_by_action=created_by_action
        )
        
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        
        logger.info(f"✅ Snapshot created: {snapshot.id}")
        return snapshot
    
    async def get_session_snapshots(
        self,
        session_id: str,
        step_name: Optional[str] = None
    ) -> List[SessionSnapshot]:
        """Get snapshots for a session, optionally filtered by step."""
        logger.info(f"📸 Fetching snapshots for session: {session_id}")
        
        query = select(SessionSnapshot).where(SessionSnapshot.session_id == session_id)
        
        if step_name:
            query = query.where(SessionSnapshot.step_name == step_name)
        
        query = query.order_by(desc(SessionSnapshot.created_at))
        
        result = await self.session.execute(query)
        snapshots = result.scalars().all()
        
        logger.info(f"✅ Retrieved {len(snapshots)} snapshots")
        return snapshots
    
    async def branch_session_from_snapshot(
        self,
        parent_session_id: str,
        branch_name: str,
        snapshot_id: str,
        description: Optional[str] = None
    ) -> ProjectSession:
        """Create a new session branched from a specific snapshot."""
        logger.info(f"🌿 Creating branch '{branch_name}' from snapshot {snapshot_id}")
        
        # Get parent session and snapshot
        parent_session = await self.get_session(parent_session_id)
        if not parent_session:
            raise ValueError(f"Parent session {parent_session_id} not found")
        
        snapshot_query = select(SessionSnapshot).where(SessionSnapshot.id == snapshot_id)
        snapshot_result = await self.session.execute(snapshot_query)
        snapshot = snapshot_result.scalar_one_or_none()
        
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        # Create new session
        new_session = await self.create_session(
            project_id=parent_session.project_id,
            name=branch_name,
            description=description,
            parent_session_id=parent_session_id,
            branch_point=snapshot.step_name
        )
        
        # Create new pipeline from snapshot state
        pipeline_state = snapshot.pipeline_state
        new_pipeline = await self.pipeline_service.create_pipeline_from_state(
            document_text=pipeline_state.get('document_text', ''),
            initial_state=pipeline_state
        )
        
        # Link session to new pipeline
        await self.link_session_to_pipeline(new_session.id, new_pipeline.id)
        
        logger.info(f"✅ Branch created successfully: {new_session.id}")
        return new_session
    
    async def get_session_tree(self, project_id: str) -> Dict[str, Any]:
        """Get a hierarchical tree of all sessions in a project."""
        logger.info(f"🌳 Building session tree for project: {project_id}")
        
        sessions = await self.get_project_sessions(project_id)
        
        # Build tree structure
        tree = {"sessions": [], "roots": []}
        session_map = {}
        
        # First pass: create session nodes
        for session in sessions:
            node = {
                "id": str(session.id),
                "name": session.name,
                "description": session.description,
                "status": session.status,
                "completion_percentage": session.completion_percentage,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                "is_main_branch": session.is_main_branch,
                "branch_point": session.branch_point,
                "document_name": session.document_name,
                "total_threats": session.total_threats_found,
                "risk_summary": session.risk_level_summary,
                "children": []
            }
            session_map[str(session.id)] = node
            tree["sessions"].append(node)
        
        # Second pass: build parent-child relationships
        for session in sessions:
            if session.parent_session_id:
                parent_id = str(session.parent_session_id)
                if parent_id in session_map:
                    session_map[parent_id]["children"].append(session_map[str(session.id)])
            else:
                tree["roots"].append(session_map[str(session.id)])
        
        logger.info(f"✅ Session tree built: {len(tree['roots'])} root sessions")
        return tree
