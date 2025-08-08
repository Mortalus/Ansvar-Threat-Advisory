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