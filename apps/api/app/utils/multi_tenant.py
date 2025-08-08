"""
Multi-tenancy utilities for client data segregation

Provides helper functions for filtering data based on client_id
to ensure strict data isolation between clients.
"""

from typing import Optional, List, Any
from sqlalchemy.orm import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models import User, Pipeline


class MultiTenantMixin:
    """Mixin to add multi-tenant filtering capabilities to database models"""
    
    def filter_by_client_access(self, query: Query, user: User, client_id_column: Any) -> Query:
        """
        Filter query based on user's client access permissions
        
        Args:
            query: SQLAlchemy query to filter
            user: User requesting the data
            client_id_column: Column containing client_id in the model
            
        Returns:
            Filtered query that respects client data access rules
        """
        if user.is_administrator():
            # Administrators can see all data
            return query
            
        if user.is_client_user():
            # External clients can only see their own data
            return query.where(client_id_column == user.client_id)
        
        # Internal users can see all data by default (but not client-specific data)
        # In Phase 5, this could be restricted further based on business requirements
        return query


class ClientDataFilter:
    """Utility class for filtering data based on client access rules"""
    
    def __init__(self, user: User):
        self.user = user
        
    def can_access_pipeline(self, pipeline: Pipeline) -> bool:
        """Check if user can access a specific pipeline"""
        if self.user.is_administrator():
            return True
            
        if self.user.is_client_user():
            # Client users can only access pipelines assigned to their client
            return pipeline.client_id == self.user.client_id
        
        # Internal users can access all pipelines
        return True
    
    def filter_pipeline_query(self, query: Query) -> Query:
        """Filter pipeline query based on user's access permissions"""
        if self.user.is_administrator():
            return query
            
        if self.user.is_client_user():
            return query.where(Pipeline.client_id == self.user.client_id)
        
        return query
    
    async def get_accessible_pipelines(
        self,
        session: AsyncSession,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Pipeline]:
        """Get pipelines that the user can access"""
        query = select(Pipeline).offset(offset)
        
        if limit:
            query = query.limit(limit)
            
        query = self.filter_pipeline_query(query)
        
        result = await session.execute(query)
        return list(result.scalars().all())


def create_client_aware_query(
    base_query: Query,
    user: User,
    client_id_column: Any
) -> Query:
    """
    Create a query that automatically filters data based on client access
    
    Args:
        base_query: Base SQLAlchemy query
        user: User making the request
        client_id_column: Column containing client_id in the queried model
        
    Returns:
        Query filtered for appropriate client access
    """
    if user.is_administrator():
        return base_query
        
    if user.is_client_user():
        return base_query.where(client_id_column == user.client_id)
    
    return base_query


def ensure_client_data_access(user: User, target_client_id: Optional[str]) -> bool:
    """
    Validate that user has access to data for the specified client_id
    
    Args:
        user: User requesting access
        target_client_id: Client ID of the data being accessed
        
    Returns:
        True if access is allowed
        
    Raises:
        PermissionError: If access is denied
    """
    if user.is_administrator():
        return True
        
    if user.is_client_user():
        if user.client_id != target_client_id:
            raise PermissionError(f"Access denied to client data: {target_client_id}")
        return True
    
    # Internal users can access non-client data
    if target_client_id is None:
        return True
        
    return True  # Internal users can access client data by default


async def assign_client_id_to_pipeline(
    session: AsyncSession,
    pipeline: Pipeline,
    user: User
) -> None:
    """
    Assign appropriate client_id to a pipeline based on the creating user
    
    Args:
        session: Database session
        pipeline: Pipeline to assign client_id to
        user: User creating the pipeline
    """
    if user.is_client_user():
        # Client users' pipelines are automatically assigned to their client
        pipeline.client_id = user.client_id
    else:
        # Internal users create non-client pipelines by default
        # In Phase 5, this could be modified to allow assignment to specific clients
        pipeline.client_id = None
    
    await session.flush()  # Ensure the assignment is persisted


class ClientAwareService:
    """Base class for services that need client-aware data filtering"""
    
    def __init__(self, session: AsyncSession, user: User):
        self.session = session
        self.user = user
        self.data_filter = ClientDataFilter(user)
    
    def ensure_access(self, target_client_id: Optional[str]) -> None:
        """Ensure user has access to the specified client data"""
        ensure_client_data_access(self.user, target_client_id)
    
    def filter_query(self, query: Query, client_id_column: Any) -> Query:
        """Apply client filtering to a query"""
        return create_client_aware_query(query, self.user, client_id_column)