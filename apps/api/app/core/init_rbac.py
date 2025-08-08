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