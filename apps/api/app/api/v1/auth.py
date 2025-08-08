"""
Authentication and authorization endpoints for RBAC
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db_connection_manager import get_robust_session

async def get_db():
    """Get database session with robust error handling"""
    async with get_robust_session() as session:
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