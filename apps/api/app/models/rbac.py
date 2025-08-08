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