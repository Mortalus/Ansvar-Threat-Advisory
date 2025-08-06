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