User: Excellent. Now let's analyze the Authentication & RBAC module.

Here is the relevant code from the following files: apps/api/app/api/v1/auth.py, apps/api/app/models/user.py, apps/api/app/models/rbac.py, apps/api/app/services/rbac_service.py, apps/api/app/services/user_service.py, apps/api/app/core/init_rbac.py, apps/api/app/dependencies.py

Python

// --- Start of apps/api/app/api/v1/auth.py ---
"""
Authentication and authorization endpoints for RBAC
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_async_session

async def get_db():
    async for session in get_async_session():
        yield session
from ...services.rbac_service import RBACService, PermissionDenied, AuthenticationRequired
from ...models import User, Role, Permission, RoleType, PermissionType

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Request/Response Models

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: Optional[str]
    roles: List[str]
    permissions: List[str]
    session_token: str
    expires_in_hours: int = 24

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    account_locked: bool
    organization: Optional[str]
    department: Optional[str]
    client_id: Optional[str]
    client_organization: Optional[str]
    is_external_client: bool
    roles: List[str]
    permissions: List[str]
    last_login: Optional[datetime]
    created_at: datetime

class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    client_id: Optional[str] = None
    client_organization: Optional[str] = None
    is_external_client: Optional[bool] = False

class CreateClientUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    client_id: str
    client_organization: str
    full_name: Optional[str] = None

class UpdateUserRolesRequest(BaseModel):
    roles: List[str]

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    is_system_role: bool
    is_active: bool
    permissions: List[str]

class PermissionResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    resource: str
    action: str

# Dependencies

async def get_rbac_service(db: AsyncSession = Depends(get_db)) -> RBACService:
    return RBACService(db)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Optional[User]:
    if not credentials:
        return None
    return await rbac_service.validate_session(credentials.credentials)

async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await rbac_service.validate_session(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def require_permission(permission: str):
    """Decorator to require specific permission"""
    async def permission_dependency(
        current_user: User = Depends(require_auth),
        rbac_service: RBACService = Depends(get_rbac_service)
    ) -> User:
        try:
            await rbac_service.require_permission(current_user, permission)
            return current_user
        except PermissionDenied:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission {permission} required"
            )
    return permission_dependency

# Authentication Endpoints

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Authenticate user and create session"""
    ip_address = http_request.client.host
    user_agent = http_request.headers.get("user-agent")
    
    user, session_token = await rbac_service.authenticate_user(
        request.username,
        request.password,
        ip_address,
        user_agent
    )
    
    if not user or not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Get permissions safely without lazy loading
    permissions = []
    for role in user.roles:
        for permission in role.permissions:
            permissions.append(permission.name)
    
    return LoginResponse(
        user_id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        roles=[role.name for role in user.roles],
        permissions=permissions,
        session_token=session_token
    )

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Logout user and invalidate session"""
    if credentials:
        await rbac_service.logout_user(credentials.credentials)
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_auth)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        account_locked=current_user.account_locked,
        organization=current_user.organization,
        department=current_user.department,
        client_id=current_user.client_id,
        client_organization=current_user.client_organization,
        is_external_client=current_user.is_external_client,
        roles=[role.name for role in current_user.roles],
        permissions=current_user.get_permissions(),
        last_login=current_user.last_login,
        created_at=current_user.created_at
    )

# User Management Endpoints (Admin only)

@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_permission(PermissionType.USER_CREATE)),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Create a new user (Admin only)"""
    try:
        user = await rbac_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            roles=request.roles,
            client_id=request.client_id,
            client_organization=request.client_organization,
            is_external_client=request.is_external_client or False
        )
        
        # Update additional fields if provided
        if request.organization:
            user.organization = request.organization
        if request.department:
            user.department = request.department
        
        await rbac_service.session.commit()
        await rbac_service.session.refresh(user)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            account_locked=user.account_locked,
            organization=user.organization,
            department=user.department,
            client_id=user.client_id,
            client_organization=user.client_organization,
            is_external_client=user.is_external_client,
            roles=[role.name for role in user.roles],
            permissions=user.get_permissions(),
            last_login=user.last_login,
            created_at=user.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_permission(PermissionType.USER_VIEW)),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """List all users (Admin only)"""
    users = await rbac_service.list_users()
    
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            account_locked=user.account_locked,
            organization=user.organization,
            department=user.department,
            client_id=user.client_id,
            client_organization=user.client_organization,
            is_external_client=user.is_external_client,
            roles=[role.name for role in user.roles],
            permissions=user.get_permissions(),
            last_login=user.last_login,
            created_at=user.created_at
        )
        for user in users
    ]

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_permission(PermissionType.USER_VIEW)),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get user by ID (Admin only)"""
    user = await rbac_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        account_locked=user.account_locked,
        organization=user.organization,
        department=user.department,
        client_id=user.client_id,
        client_organization=user.client_organization,
        is_external_client=user.is_external_client,
        roles=[role.name for role in user.roles],
        permissions=user.get_permissions(),
        last_login=user.last_login,
        created_at=user.created_at
    )

@router.put("/users/{user_id}/roles")
async def update_user_roles(
    user_id: int,
    request: UpdateUserRolesRequest,
    current_user: User = Depends(require_permission(PermissionType.USER_ASSIGN_ROLES)),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Update user roles (Admin only)"""
    success = await rbac_service.update_user_roles(user_id, request.roles)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User roles updated successfully"}

@router.post("/clients/users", response_model=UserResponse)
async def create_client_user(
    request: CreateClientUserRequest,
    current_user: User = Depends(require_permission(PermissionType.USER_CREATE)),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Create a new client user (Admin only)"""
    try:
        user = await rbac_service.create_client_user(
            username=request.username,
            email=request.email,
            password=request.password,
            client_id=request.client_id,
            client_organization=request.client_organization,
            full_name=request.full_name
        )
        
        await rbac_service.session.refresh(user)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            account_locked=user.account_locked,
            organization=user.organization,
            department=user.department,
            client_id=user.client_id,
            client_organization=user.client_organization,
            is_external_client=user.is_external_client,
            roles=[role.name for role in user.roles],
            permissions=user.get_permissions(),
            last_login=user.last_login,
            created_at=user.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create client user: {str(e)}"
        )

@router.get("/clients/{client_id}/users", response_model=List[UserResponse])
async def list_client_users(
    client_id: str,
    current_user: User = Depends(require_permission(PermissionType.USER_VIEW)),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """List users for a specific client (Admin only)"""
    users = await rbac_service.get_users_by_client_id(client_id)
    
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            account_locked=user.account_locked,
            organization=user.organization,
            department=user.department,
            client_id=user.client_id,
            client_organization=user.client_organization,
            is_external_client=user.is_external_client,
            roles=[role.name for role in user.roles],
            permissions=user.get_permissions(),
            last_login=user.last_login,
            created_at=user.created_at
        )
        for user in users
    ]

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(require_auth),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Change current user's password"""
    # Verify current password
    import bcrypt
    if not bcrypt.checkpw(request.current_password.encode('utf-8'), 
                         current_user.hashed_password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    success = await rbac_service.change_password(current_user.id, request.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password"
        )
    
    return {"message": "Password changed successfully"}

# Role and Permission Endpoints

@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(require_permission(PermissionType.SYSTEM_ADMIN)),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """List all roles (Admin only)"""
    roles = await rbac_service.list_roles()
    
    return [
        RoleResponse(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            is_system_role=role.is_system_role,
            is_active=role.is_active,
            permissions=[perm.name for perm in role.permissions]
        )
        for role in roles
    ]

@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    current_user: User = Depends(require_permission(PermissionType.SYSTEM_ADMIN)),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """List all permissions (Admin only)"""
    permissions = await rbac_service.list_permissions()
    
    return [
        PermissionResponse(
            id=perm.id,
            name=perm.name,
            display_name=perm.display_name,
            description=perm.description,
            resource=perm.resource,
            action=perm.action
        )
        for perm in permissions
    ]
// --- End of apps/api/app/api/v1/auth.py ---

// --- Start of apps/api/app/models/user.py ---
"""User model for authentication and ownership"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.orm import relationship
from typing import List
from .base import BaseModel

class User(BaseModel):
    """User model with RBAC support"""
    __tablename__ = "users"
    
    # Basic user fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Authentication fields
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Account status
    account_locked = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Profile information
    organization = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Multi-tenancy support for client portal
    client_id = Column(String(100), nullable=True, index=True)  # Identifies external client organization
    client_organization = Column(String(255), nullable=True)  # Client company name for display
    is_external_client = Column(Boolean, default=False, nullable=False)  # Flag for client portal users
    
    # Timestamps
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    pipelines = relationship("Pipeline", back_populates="owner", cascade="all, delete-orphan")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    sessions = relationship("UserSession", foreign_keys="UserSession.user_id", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission through their roles"""
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False
    
    def get_permissions(self) -> List[str]:
        """Get all permissions for this user"""
        permissions = set()
        for role in self.roles:
            for permission in role.permissions:
                permissions.add(permission.name)
        return list(permissions)
    
    def is_administrator(self) -> bool:
        """Check if user is an administrator"""
        return self.is_superuser or self.has_role("administrator")
    
    def is_client_user(self) -> bool:
        """Check if user is an external client"""
        return self.is_external_client and self.client_id is not None
    
    def can_access_client_data(self, target_client_id: str) -> bool:
        """Check if user can access data for a specific client"""
        if self.is_administrator():
            return True  # Admins can access all client data
        
        if self.is_client_user():
            return self.client_id == target_client_id  # Clients can only access their own data
        
        return True  # Internal users can access all data by default
// --- End of apps/api/app/models/user.py ---

// --- Start of apps/api/app/models/rbac.py ---
"""
Role-Based Access Control (RBAC) models for the Threat Modeling Platform

Provides role and permission management for enterprise security controls.
"""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Table, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import BaseModel


# Association tables for many-to-many relationships
user_roles = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table(
    'role_permissions',
    BaseModel.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class RoleType(str, enum.Enum):
    """Predefined system roles"""
    ADMINISTRATOR = "administrator"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_USER = "api_user"  # For service accounts
    CLIENT = "client"  # For external client portal access


class PermissionType(str, enum.Enum):
    """System permissions for granular access control"""
    # Pipeline Operations
    PIPELINE_CREATE = "pipeline:create"
    PIPELINE_VIEW = "pipeline:view"
    PIPELINE_EDIT = "pipeline:edit"
    PIPELINE_DELETE = "pipeline:delete"
    PIPELINE_EXECUTE = "pipeline:execute"
    
    # Agent Management
    AGENT_VIEW = "agent:view"
    AGENT_CONFIGURE = "agent:configure"
    AGENT_EXECUTE = "agent:execute"
    AGENT_MANAGE = "agent:manage"
    
    # System Administration
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_AUDIT = "system:audit"
    
    # User Management
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_EDIT = "user:edit"
    USER_DELETE = "user:delete"
    USER_ASSIGN_ROLES = "user:assign_roles"
    
    # Reports & Export
    REPORT_VIEW = "report:view"
    REPORT_EXPORT = "report:export"
    REPORT_ADMIN = "report:admin"
    
    # Configuration
    CONFIG_VIEW = "config:view"
    CONFIG_EDIT = "config:edit"
    
    # Client Portal Permissions (for external clients)
    CLIENT_DASHBOARD_VIEW = "client:dashboard_view"
    CLIENT_PROJECT_VIEW = "client:project_view"
    CLIENT_REPORT_VIEW = "client:report_view"
    CLIENT_REPORT_DOWNLOAD = "client:report_download"


class Role(BaseModel):
    """
    Role definitions for RBAC system
    Defines what groups of permissions users can have
    """
    __tablename__ = "roles"
    
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Role metadata
    is_system_role = Column(Boolean, default=False, nullable=False)  # Cannot be deleted
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(name='{self.name}', display_name='{self.display_name}')>"
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if this role has a specific permission"""
        return any(perm.name == permission_name for perm in self.permissions)


class Permission(BaseModel):
    """
    Permission definitions for fine-grained access control
    """
    __tablename__ = "permissions"
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    resource = Column(String(50), nullable=False)  # e.g., 'pipeline', 'agent', 'system'
    action = Column(String(50), nullable=False)    # e.g., 'create', 'read', 'update', 'delete'
    
    # Permission metadata
    is_system_permission = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(name='{self.name}', resource='{self.resource}', action='{self.action}')>"


class UserSession(BaseModel):
    """
    User session management for authentication tracking
    """
    __tablename__ = "user_sessions"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Session metadata
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Session context
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(Text)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    revoked_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="sessions")
    revoked_by_user = relationship("User", foreign_keys=[revoked_by])
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, active={self.is_active})>"
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None) if self.expires_at else True


class AuditLog(BaseModel):
    """
    Audit log for RBAC operations and security events
    """
    __tablename__ = "audit_logs"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(Integer, ForeignKey("user_sessions.id"), nullable=True)
    
    # Audit event details
    event_type = Column(String(100), nullable=False, index=True)  # login, role_change, permission_denied, etc.
    resource_type = Column(String(50))  # pipeline, agent, user, etc.
    resource_id = Column(String(100))   # ID of the affected resource
    action = Column(String(50), nullable=False)  # create, read, update, delete, execute
    
    # Event context
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Event outcome
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    
    # Additional context
    details = Column(Text)  # JSON string with additional event details
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    session = relationship("UserSession", foreign_keys=[session_id])
    
    def __repr__(self):
        return f"<AuditLog(event_type='{self.event_type}', user_id={self.user_id}, success={self.success})>"


def create_default_roles_and_permissions(session):
    """
    Bootstrap function to create default roles and permissions
    Should be called during database initialization
    """
    # Create default permissions
    permissions = [
        # Pipeline permissions
        Permission(name=PermissionType.PIPELINE_CREATE, display_name="Create Pipelines", 
                  description="Create new threat modeling pipelines", resource="pipeline", action="create"),
        Permission(name=PermissionType.PIPELINE_VIEW, display_name="View Pipelines", 
                  description="View pipeline details and results", resource="pipeline", action="read"),
        Permission(name=PermissionType.PIPELINE_EDIT, display_name="Edit Pipelines", 
                  description="Modify pipeline configuration", resource="pipeline", action="update"),
        Permission(name=PermissionType.PIPELINE_DELETE, display_name="Delete Pipelines", 
                  description="Delete pipelines and their data", resource="pipeline", action="delete"),
        Permission(name=PermissionType.PIPELINE_EXECUTE, display_name="Execute Pipelines", 
                  description="Run pipeline steps and agents", resource="pipeline", action="execute"),
        
        # Agent permissions
        Permission(name=PermissionType.AGENT_VIEW, display_name="View Agents", 
                  description="View agent configurations and status", resource="agent", action="read"),
        Permission(name=PermissionType.AGENT_CONFIGURE, display_name="Configure Agents", 
                  description="Modify agent settings and prompts", resource="agent", action="update"),
        Permission(name=PermissionType.AGENT_EXECUTE, display_name="Execute Agents", 
                  description="Run individual agents", resource="agent", action="execute"),
        Permission(name=PermissionType.AGENT_MANAGE, display_name="Manage Agents", 
                  description="Enable/disable agents and manage registry", resource="agent", action="manage"),
        
        # System permissions
        Permission(name=PermissionType.SYSTEM_ADMIN, display_name="System Administration", 
                  description="Full system administration access", resource="system", action="admin"),
        Permission(name=PermissionType.SYSTEM_MONITOR, display_name="System Monitoring", 
                  description="View system metrics and health", resource="system", action="monitor"),
        Permission(name=PermissionType.SYSTEM_AUDIT, display_name="System Audit", 
                  description="View audit logs and security events", resource="system", action="audit"),
        
        # User permissions
        Permission(name=PermissionType.USER_VIEW, display_name="View Users", 
                  description="View user accounts and profiles", resource="user", action="read"),
        Permission(name=PermissionType.USER_CREATE, display_name="Create Users", 
                  description="Create new user accounts", resource="user", action="create"),
        Permission(name=PermissionType.USER_EDIT, display_name="Edit Users", 
                  description="Modify user accounts", resource="user", action="update"),
        Permission(name=PermissionType.USER_DELETE, display_name="Delete Users", 
                  description="Delete user accounts", resource="user", action="delete"),
        Permission(name=PermissionType.USER_ASSIGN_ROLES, display_name="Assign User Roles", 
                  description="Assign and modify user roles", resource="user", action="assign_roles"),
        
        # Report permissions
        Permission(name=PermissionType.REPORT_VIEW, display_name="View Reports", 
                  description="View generated reports", resource="report", action="read"),
        Permission(name=PermissionType.REPORT_EXPORT, display_name="Export Reports", 
                  description="Export reports in various formats", resource="report", action="export"),
        Permission(name=PermissionType.REPORT_ADMIN, display_name="Report Administration", 
                  description="Manage report templates and settings", resource="report", action="admin"),
        
        # Configuration permissions
        Permission(name=PermissionType.CONFIG_VIEW, display_name="View Configuration", 
                  description="View system configuration", resource="config", action="read"),
        Permission(name=PermissionType.CONFIG_EDIT, display_name="Edit Configuration", 
                  description="Modify system configuration", resource="config", action="update"),
        
        # Client portal permissions
        Permission(name=PermissionType.CLIENT_DASHBOARD_VIEW, display_name="View Client Dashboard", 
                  description="Access client portal dashboard", resource="client", action="dashboard_view"),
        Permission(name=PermissionType.CLIENT_PROJECT_VIEW, display_name="View Client Projects", 
                  description="View assigned project results", resource="client", action="project_view"),
        Permission(name=PermissionType.CLIENT_REPORT_VIEW, display_name="View Client Reports", 
                  description="View project reports in client portal", resource="client", action="report_view"),
        Permission(name=PermissionType.CLIENT_REPORT_DOWNLOAD, display_name="Download Client Reports", 
                  description="Download project reports", resource="client", action="report_download"),
    ]
    
    # Add permissions to session
    for perm in permissions:
        existing = session.query(Permission).filter_by(name=perm.name).first()
        if not existing:
            session.add(perm)
    
    session.flush()  # Ensure permissions are available for role creation
    
    # Create default roles with appropriate permissions
    roles = [
        {
            "name": RoleType.ADMINISTRATOR,
            "display_name": "Administrator",
            "description": "Full system access with all permissions",
            "permissions": [perm.name for perm in permissions]  # All permissions
        },
        {
            "name": RoleType.ANALYST,
            "display_name": "Security Analyst",
            "description": "Can create and manage threat models, configure agents",
            "permissions": [
                PermissionType.PIPELINE_CREATE, PermissionType.PIPELINE_VIEW, 
                PermissionType.PIPELINE_EDIT, PermissionType.PIPELINE_EXECUTE,
                PermissionType.AGENT_VIEW, PermissionType.AGENT_CONFIGURE, PermissionType.AGENT_EXECUTE,
                PermissionType.REPORT_VIEW, PermissionType.REPORT_EXPORT,
                PermissionType.CONFIG_VIEW
            ]
        },
        {
            "name": RoleType.VIEWER,
            "display_name": "Viewer",
            "description": "Read-only access to view threat models and reports",
            "permissions": [
                PermissionType.PIPELINE_VIEW,
                PermissionType.AGENT_VIEW,
                PermissionType.REPORT_VIEW,
                PermissionType.CONFIG_VIEW
            ]
        },
        {
            "name": RoleType.API_USER,
            "display_name": "API User",
            "description": "Service account for API access",
            "permissions": [
                PermissionType.PIPELINE_CREATE, PermissionType.PIPELINE_VIEW, 
                PermissionType.PIPELINE_EXECUTE,
                PermissionType.AGENT_VIEW, PermissionType.AGENT_EXECUTE,
                PermissionType.REPORT_VIEW, PermissionType.REPORT_EXPORT
            ]
        },
        {
            "name": RoleType.CLIENT,
            "display_name": "Client",
            "description": "External client with limited portal access to their own projects",
            "permissions": [
                PermissionType.CLIENT_DASHBOARD_VIEW,
                PermissionType.CLIENT_PROJECT_VIEW,
                PermissionType.CLIENT_REPORT_VIEW,
                PermissionType.CLIENT_REPORT_DOWNLOAD
            ]
        }
    ]
    
    for role_data in roles:
        existing_role = session.query(Role).filter_by(name=role_data["name"]).first()
        if not existing_role:
            role = Role(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_system_role=True
            )
            
            # Add permissions to role
            for perm_name in role_data["permissions"]:
                permission = session.query(Permission).filter_by(name=perm_name).first()
                if permission:
                    role.permissions.append(permission)
            
            session.add(role)
    
    session.commit()
// --- End of apps/api/app/models/rbac.py ---

// --- Start of apps/api/app/services/rbac_service.py ---
"""
RBAC (Role-Based Access Control) service for authentication and authorization

Provides comprehensive user management, session handling, and permission checking
for the Threat Modeling Platform.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
import bcrypt

from ..models import (
    User, Role, Permission, UserSession, AuditLog,
    RoleType, PermissionType, user_roles
)


class RBACService:
    """Service for RBAC operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.session_duration_hours = 24  # Default session duration
    
    # Authentication Methods
    
    async def authenticate_user(
        self, 
        username: str, 
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate user and create session
        Returns (User, session_token) or (None, None) if authentication fails
        """
        # Find user by username or email with eager loading
        stmt = select(User).options(
            selectinload(User.roles).selectinload(Role.permissions)
        ).where(
            or_(User.username == username, User.email == username)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active or user.account_locked:
            await self._log_auth_event("login_failed", user.id if user else None, 
                                     ip_address, user_agent, success=False, 
                                     details="User not found, inactive, or locked")
            return None, None
        
        # Check password
        if not user.hashed_password:
            await self._log_auth_event("login_failed", user.id, ip_address, user_agent, 
                                     success=False, details="No password set")
            return None, None
        
        # Robust password checking with proper encoding
        try:
            password_bytes = password.encode('utf-8')
            hash_bytes = user.hashed_password.encode('utf-8')
            password_valid = bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            await self._log_auth_event("login_failed", user.id, ip_address, user_agent,
                                     success=False, details=f"Password check error: {str(e)}")
            return None, None
        
        if not password_valid:
            # Increment failed login attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.account_locked = True
                await self._log_auth_event("account_locked", user.id, ip_address, user_agent,
                                         success=False, details="Too many failed attempts")
            
            await self.session.commit()
            await self._log_auth_event("login_failed", user.id, ip_address, user_agent,
                                     success=False, details="Invalid password")
            return None, None
        
        # Reset failed login attempts on successful auth
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        
        # Create session
        session_token = await self._create_user_session(user, ip_address, user_agent)
        
        await self.session.commit()
        await self._log_auth_event("login_success", user.id, ip_address, user_agent, 
                                 success=True, details="User authenticated")
        
        return user, session_token
    
    async def validate_session(self, session_token: str) -> Optional[User]:
        """
        Validate session token and return user if valid
        Updates last_accessed timestamp
        """
        stmt = select(UserSession).options(
            selectinload(UserSession.user).selectinload(User.roles).selectinload(Role.permissions)
        ).where(
            and_(
                UserSession.session_token == session_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        # Update last accessed
        session.last_accessed = datetime.utcnow()
        await self.session.commit()
        
        return session.user
    
    async def logout_user(self, session_token: str) -> bool:
        """Logout user by invalidating session"""
        stmt = select(UserSession).where(UserSession.session_token == session_token)
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            return False
        
        session.is_active = False
        session.revoked_at = datetime.utcnow()
        
        await self.session.commit()
        await self._log_auth_event("logout", session.user_id, None, None, 
                                 success=True, details="User logged out")
        
        return True
    
    # User Management Methods
    
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        client_id: Optional[str] = None,
        client_organization: Optional[str] = None,
        is_external_client: bool = False
    ) -> User:
        """Create a new user with optional roles"""
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            is_active=True,
            password_changed_at=datetime.utcnow(),
            client_id=client_id,
            client_organization=client_organization,
            is_external_client=is_external_client
        )
        
        # Assign roles if provided
        if roles:
            role_objects = await self._get_roles_by_names(roles)
            user.roles = role_objects
        else:
            # Assign default viewer role
            viewer_role = await self._get_role_by_name(RoleType.VIEWER)
            if viewer_role:
                user.roles = [viewer_role]
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        await self._log_auth_event("user_created", user.id, None, None,
                                 success=True, details=f"User created with roles: {roles or ['viewer']}")
        
        return user
    
    async def update_user_roles(self, user_id: int, role_names: List[str]) -> bool:
        """Update user's roles"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        old_roles = [role.name for role in user.roles]
        new_roles = await self._get_roles_by_names(role_names)
        user.roles = new_roles
        
        await self.session.commit()
        await self._log_auth_event("roles_updated", user_id, None, None,
                                 success=True, 
                                 details=f"Roles changed from {old_roles} to {role_names}")
        
        return True
    
    async def change_password(self, user_id: int, new_password: str) -> bool:
        """Change user password"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.hashed_password = hashed_password
        user.password_changed_at = datetime.utcnow()
        user.failed_login_attempts = 0
        user.account_locked = False
        
        await self.session.commit()
        await self._log_auth_event("password_changed", user_id, None, None,
                                 success=True, details="Password updated")
        
        return True
    
    async def create_client_user(
        self,
        username: str,
        email: str,
        password: str,
        client_id: str,
        client_organization: str,
        full_name: Optional[str] = None
    ) -> User:
        """Create a new external client user with restricted access"""
        return await self.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            roles=[RoleType.CLIENT],
            client_id=client_id,
            client_organization=client_organization,
            is_external_client=True
        )
    
    async def get_users_by_client_id(self, client_id: str) -> List[User]:
        """Get all users for a specific client organization"""
        stmt = select(User).options(selectinload(User.roles)).where(User.client_id == client_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    # Permission Checking Methods
    
    async def check_permission(self, user: User, permission: str) -> bool:
        """Check if user has a specific permission"""
        if user.is_superuser:
            return True
        
        return user.has_permission(permission)
    
    async def check_client_data_access(
        self,
        user: User,
        target_client_id: Optional[str] = None
    ) -> bool:
        """
        Check if user can access data for a specific client
        Returns True if access is allowed, False otherwise
        """
        if user.is_administrator():
            return True  # Admins can access all data
        
        if not target_client_id:
            return not user.is_client_user()  # Internal users can access non-client data
        
        return user.can_access_client_data(target_client_id)
    
    async def require_client_data_access(
        self,
        user: User,
        target_client_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> bool:
        """
        Require client data access and log audit event if denied
        Raises PermissionDenied exception if user lacks access
        """
        has_access = await self.check_client_data_access(user, target_client_id)
        
        if not has_access:
            await self._log_auth_event(
                "client_data_access_denied",
                user.id,
                None,
                None,
                success=False,
                details=f"Client data access denied for client_id {target_client_id}, resource {resource_type}:{resource_id}"
            )
            raise PermissionDenied(f"Access denied to client data: {target_client_id}")
        
        return True
    
    async def require_permission(
        self, 
        user: User, 
        permission: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> bool:
        """
        Check permission and log audit event if denied
        Raises PermissionDenied exception if user lacks permission
        """
        has_permission = await self.check_permission(user, permission)
        
        if not has_permission:
            await self._log_auth_event(
                "permission_denied", 
                user.id, 
                None, 
                None,
                success=False,
                details=f"Permission {permission} denied for resource {resource_type}:{resource_id}"
            )
            raise PermissionDenied(f"Permission {permission} required")
        
        return True
    
    # Role Management Methods
    
    async def create_role(
        self, 
        name: str, 
        display_name: str, 
        description: str,
        permissions: List[str]
    ) -> Role:
        """Create a new role with permissions"""
        role = Role(
            name=name,
            display_name=display_name,
            description=description,
            is_system_role=False
        )
        
        # Add permissions
        permission_objects = await self._get_permissions_by_names(permissions)
        role.permissions = permission_objects
        
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        
        return role
    
    # Query Methods
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with roles and permissions loaded"""
        stmt = select(User).options(
            selectinload(User.roles).selectinload(Role.permissions)
        ).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username with roles and permissions loaded"""
        stmt = select(User).options(
            selectinload(User.roles).selectinload(Role.permissions)
        ).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_users(self) -> List[User]:
        """List all users with their roles and permissions"""
        stmt = select(User).options(
            selectinload(User.roles).selectinload(Role.permissions)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def list_roles(self) -> List[Role]:
        """List all roles with their permissions"""
        stmt = select(Role).options(selectinload(Role.permissions))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def list_permissions(self) -> List[Permission]:
        """List all permissions"""
        stmt = select(Permission)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    # Private Helper Methods
    
    async def _create_user_session(
        self, 
        user: User, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Create a new user session and return token"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=self.session_duration_hours)
        
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True
        )
        
        self.session.add(session)
        return session_token
    
    async def _get_role_by_name(self, role_name: str) -> Optional[Role]:
        """Get role by name"""
        stmt = select(Role).where(Role.name == role_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_roles_by_names(self, role_names: List[str]) -> List[Role]:
        """Get roles by list of names"""
        stmt = select(Role).where(Role.name.in_(role_names))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def _get_permissions_by_names(self, permission_names: List[str]) -> List[Permission]:
        """Get permissions by list of names"""
        stmt = select(Permission).where(Permission.name.in_(permission_names))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def _log_auth_event(
        self,
        event_type: str,
        user_id: Optional[int],
        ip_address: Optional[str],
        user_agent: Optional[str],
        success: bool,
        details: Optional[str] = None
    ):
        """Log authentication/authorization events"""
        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            resource_type="auth",
            action="authenticate",
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details
        )
        self.session.add(audit_log)


class PermissionDenied(Exception):
    """Exception raised when user lacks required permission"""
    pass


class AuthenticationMiddleware:
    """Middleware for handling authentication in FastAPI"""
    
    def __init__(self, rbac_service: RBACService):
        self.rbac_service = rbac_service
    
    async def get_current_user(self, session_token: str) -> Optional[User]:
        """Get current authenticated user from session token"""
        if not session_token:
            return None
        
        return await self.rbac_service.validate_session(session_token)
    
    async def require_authentication(self, session_token: str) -> User:
        """Require valid authentication, raise exception if not authenticated"""
        user = await self.get_current_user(session_token)
        if not user:
            raise AuthenticationRequired("Valid session required")
        return user
    
    async def require_permission(
        self, 
        session_token: str, 
        permission: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> User:
        """Require authentication and specific permission"""
        user = await self.require_authentication(session_token)
        await self.rbac_service.require_permission(user, permission, resource_type, resource_id)
        return user


class AuthenticationRequired(Exception):
    """Exception raised when authentication is required but not provided"""
    pass
// --- End of apps/api/app/services/rbac_service.py ---

// --- Start of apps/api/app/services/user_service.py ---
"""User database service layer (for future authentication)"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from ..models import User


class UserService:
    """Service for user database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user(
        self,
        email: str,
        username: str,
        full_name: Optional[str] = None
    ) -> User:
        """Create a new user"""
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            is_active=True
        )
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        user = await self.get_user_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            await self.session.commit()
            return True
        return False
    
    async def list_users(self, limit: int = 100) -> List[User]:
        """List all users"""
        stmt = select(User).order_by(User.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
// --- End of apps/api/app/services/user_service.py ---

// --- Start of apps/api/app/core/init_rbac.py ---
"""
RBAC Database Initialization Script

Creates default roles, permissions, and an admin user for the system.
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_async_session
from ..models import User, Role, Permission, RoleType, PermissionType
from ..models.rbac import create_default_roles_and_permissions
from ..services.rbac_service import RBACService


async def init_rbac_system():
    """Initialize RBAC system with default roles and admin user"""
    session_gen = get_async_session()
    session = await session_gen.__anext__()
    
    try:
        # Create default roles and permissions
        print("Creating default roles and permissions...")
        await create_default_roles_and_permissions_async(session)
        
        # Create default admin user if it doesn't exist
        rbac_service = RBACService(session)
        
        admin_user = await rbac_service.get_user_by_username("admin")
        if not admin_user:
            print("Creating default admin user...")
            
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123!")
            admin_email = os.getenv("ADMIN_EMAIL", "admin@threatmodeling.local")
            
            admin_user = await rbac_service.create_user(
                username="admin",
                email=admin_email,
                password=admin_password,
                full_name="System Administrator",
                roles=[RoleType.ADMINISTRATOR]
            )
            
            print(f"Admin user created:")
            print(f"  Username: admin")
            print(f"  Email: {admin_email}")
            print(f"  Password: {admin_password}")
            print("  Please change the password after first login!")
        else:
            print("Admin user already exists")
        
        print("RBAC system initialization completed successfully")
    
    finally:
        await session.close()


async def create_default_roles_and_permissions_async(session: AsyncSession):
    """Async version of the bootstrap function"""
    # Create default permissions
    permissions_data = [
        # Pipeline permissions
        {
            "name": PermissionType.PIPELINE_CREATE,
            "display_name": "Create Pipelines",
            "description": "Create new threat modeling pipelines",
            "resource": "pipeline",
            "action": "create"
        },
        {
            "name": PermissionType.PIPELINE_VIEW,
            "display_name": "View Pipelines",
            "description": "View pipeline details and results",
            "resource": "pipeline",
            "action": "read"
        },
        {
            "name": PermissionType.PIPELINE_EDIT,
            "display_name": "Edit Pipelines",
            "description": "Modify pipeline configuration",
            "resource": "pipeline",
            "action": "update"
        },
        {
            "name": PermissionType.PIPELINE_DELETE,
            "display_name": "Delete Pipelines",
            "description": "Delete pipelines and their data",
            "resource": "pipeline",
            "action": "delete"
        },
        {
            "name": PermissionType.PIPELINE_EXECUTE,
            "display_name": "Execute Pipelines",
            "description": "Run pipeline steps and agents",
            "resource": "pipeline",
            "action": "execute"
        },
        
        # Agent permissions
        {
            "name": PermissionType.AGENT_VIEW,
            "display_name": "View Agents",
            "description": "View agent configurations and status",
            "resource": "agent",
            "action": "read"
        },
        {
            "name": PermissionType.AGENT_CONFIGURE,
            "display_name": "Configure Agents",
            "description": "Modify agent settings and prompts",
            "resource": "agent",
            "action": "update"
        },
        {
            "name": PermissionType.AGENT_EXECUTE,
            "display_name": "Execute Agents",
            "description": "Run individual agents",
            "resource": "agent",
            "action": "execute"
        },
        {
            "name": PermissionType.AGENT_MANAGE,
            "display_name": "Manage Agents",
            "description": "Enable/disable agents and manage registry",
            "resource": "agent",
            "action": "manage"
        },
        
        # System permissions
        {
            "name": PermissionType.SYSTEM_ADMIN,
            "display_name": "System Administration",
            "description": "Full system administration access",
            "resource": "system",
            "action": "admin"
        },
        {
            "name": PermissionType.SYSTEM_MONITOR,
            "display_name": "System Monitoring",
            "description": "View system metrics and health",
            "resource": "system",
            "action": "monitor"
        },
        {
            "name": PermissionType.SYSTEM_AUDIT,
            "display_name": "System Audit",
            "description": "View audit logs and security events",
            "resource": "system",
            "action": "audit"
        },
        
        # User permissions
        {
            "name": PermissionType.USER_VIEW,
            "display_name": "View Users",
            "description": "View user accounts and profiles",
            "resource": "user",
            "action": "read"
        },
        {
            "name": PermissionType.USER_CREATE,
            "display_name": "Create Users",
            "description": "Create new user accounts",
            "resource": "user",
            "action": "create"
        },
        {
            "name": PermissionType.USER_EDIT,
            "display_name": "Edit Users",
            "description": "Modify user accounts",
            "resource": "user",
            "action": "update"
        },
        {
            "name": PermissionType.USER_DELETE,
            "display_name": "Delete Users",
            "description": "Delete user accounts",
            "resource": "user",
            "action": "delete"
        },
        {
            "name": PermissionType.USER_ASSIGN_ROLES,
            "display_name": "Assign User Roles",
            "description": "Assign and modify user roles",
            "resource": "user",
            "action": "assign_roles"
        },
        
        # Report permissions
        {
            "name": PermissionType.REPORT_VIEW,
            "display_name": "View Reports",
            "description": "View generated reports",
            "resource": "report",
            "action": "read"
        },
        {
            "name": PermissionType.REPORT_EXPORT,
            "display_name": "Export Reports",
            "description": "Export reports in various formats",
            "resource": "report",
            "action": "export"
        },
        {
            "name": PermissionType.REPORT_ADMIN,
            "display_name": "Report Administration",
            "description": "Manage report templates and settings",
            "resource": "report",
            "action": "admin"
        },
        
        # Configuration permissions
        {
            "name": PermissionType.CONFIG_VIEW,
            "display_name": "View Configuration",
            "description": "View system configuration",
            "resource": "config",
            "action": "read"
        },
        {
            "name": PermissionType.CONFIG_EDIT,
            "display_name": "Edit Configuration",
            "description": "Modify system configuration",
            "resource": "config",
            "action": "update"
        },
        
        # Client portal permissions
        {
            "name": PermissionType.CLIENT_DASHBOARD_VIEW,
            "display_name": "View Client Dashboard",
            "description": "Access client portal dashboard",
            "resource": "client",
            "action": "dashboard_view"
        },
        {
            "name": PermissionType.CLIENT_PROJECT_VIEW,
            "display_name": "View Client Projects",
            "description": "View assigned project results",
            "resource": "client",
            "action": "project_view"
        },
        {
            "name": PermissionType.CLIENT_REPORT_VIEW,
            "display_name": "View Client Reports",
            "description": "View project reports in client portal",
            "resource": "client",
            "action": "report_view"
        },
        {
            "name": PermissionType.CLIENT_REPORT_DOWNLOAD,
            "display_name": "Download Client Reports",
            "description": "Download project reports",
            "resource": "client",
            "action": "report_download"
        },
    ]
    
    # Create permissions
    permissions = []
    for perm_data in permissions_data:
        stmt = select(Permission).where(Permission.name == perm_data["name"])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            permission = Permission(**perm_data, is_system_permission=True)
            session.add(permission)
            permissions.append(permission)
        else:
            permissions.append(existing)
    
    await session.flush()  # Ensure permissions are available for role creation
    
    # Create default roles with appropriate permissions
    roles_data = [
        {
            "name": RoleType.ADMINISTRATOR,
            "display_name": "Administrator",
            "description": "Full system access with all permissions",
            "permissions": [perm.name for perm in permissions]  # All permissions
        },
        {
            "name": RoleType.ANALYST,
            "display_name": "Security Analyst",
            "description": "Can create and manage threat models, configure agents",
            "permissions": [
                PermissionType.PIPELINE_CREATE, PermissionType.PIPELINE_VIEW,
                PermissionType.PIPELINE_EDIT, PermissionType.PIPELINE_EXECUTE,
                PermissionType.AGENT_VIEW, PermissionType.AGENT_CONFIGURE, PermissionType.AGENT_EXECUTE,
                PermissionType.REPORT_VIEW, PermissionType.REPORT_EXPORT,
                PermissionType.CONFIG_VIEW
            ]
        },
        {
            "name": RoleType.VIEWER,
            "display_name": "Viewer",
            "description": "Read-only access to view threat models and reports",
            "permissions": [
                PermissionType.PIPELINE_VIEW,
                PermissionType.AGENT_VIEW,
                PermissionType.REPORT_VIEW,
                PermissionType.CONFIG_VIEW
            ]
        },
        {
            "name": RoleType.API_USER,
            "display_name": "API User",
            "description": "Service account for API access",
            "permissions": [
                PermissionType.PIPELINE_CREATE, PermissionType.PIPELINE_VIEW,
                PermissionType.PIPELINE_EXECUTE,
                PermissionType.AGENT_VIEW, PermissionType.AGENT_EXECUTE,
                PermissionType.REPORT_VIEW, PermissionType.REPORT_EXPORT
            ]
        },
        {
            "name": RoleType.CLIENT,
            "display_name": "Client",
            "description": "External client with limited portal access to their own projects",
            "permissions": [
                PermissionType.CLIENT_DASHBOARD_VIEW,
                PermissionType.CLIENT_PROJECT_VIEW,
                PermissionType.CLIENT_REPORT_VIEW,
                PermissionType.CLIENT_REPORT_DOWNLOAD
            ]
        }
    ]
    
    for role_data in roles_data:
        stmt = select(Role).where(Role.name == role_data["name"])
        result = await session.execute(stmt)
        existing_role = result.scalar_one_or_none()
        
        if not existing_role:
            role = Role(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_system_role=True
            )
            
            # Add permissions to role
            for perm_name in role_data["permissions"]:
                stmt = select(Permission).where(Permission.name == perm_name)
                result = await session.execute(stmt)
                permission = result.scalar_one_or_none()
                if permission:
                    role.permissions.append(permission)
            
            session.add(role)
    
    await session.commit()


if __name__ == "__main__":
    asyncio.run(init_rbac_system())
// --- End of apps/api/app/core/init_rbac.py ---

// --- Start of apps/api/app/dependencies.py ---
"""
Application dependencies and shared instances
"""
from app.core.pipeline.manager import PipelineManager
from app.database import get_async_session, check_connection_health
import logging

logger = logging.getLogger(__name__)

# Create a singleton instance of PipelineManager with bulletproof session management
pipeline_manager_instance = PipelineManager()

async def get_pipeline_manager() -> PipelineManager:
    """
    BULLETPROOF dependency to get the pipeline manager instance.
    Includes proactive connection health monitoring and auto-recovery.
    """
    # Proactive health check before returning manager
    try:
        is_healthy, recovery_attempted = await check_connection_health()
        if not is_healthy:
            logger.warning("⚠️ Database connection unhealthy - PipelineManager may have reduced functionality")
        elif recovery_attempted:
            logger.info("✅ Database connection recovered - PipelineManager ready")
    except Exception as health_error:
        logger.error(f"❌ Pipeline manager health check failed: {health_error}")
        # Continue anyway - the resilient session creation will handle issues
    
    return pipeline_manager_instance

# Re-export database session dependency for convenience
get_db = get_async_session  # Alias for consistency with agent_management.py

__all__ = ['get_pipeline_manager', 'get_async_session', 'get_db']
// --- End of apps/api/app/dependencies.py ---


Your Task: Analyze this code and list the specific user-facing or API-level functionalities it provides. Be precise. For example, instead of "handles users", list "User login with session token generation", "User logout (session invalidation)", "List and manage roles and permissions (admin)", "Change password for current user", "Client user creation and listing", etc.


