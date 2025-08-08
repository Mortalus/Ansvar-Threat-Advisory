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