"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
import os
from .config import Settings

settings = Settings()

# Database URL configuration
if settings.environment == "development":
    # For development, use SQLite if no PostgreSQL URL provided
    if not settings.database_url:
        DATABASE_URL = "sqlite:///./threat_modeling.db"
        ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./threat_modeling.db"
    else:
        DATABASE_URL = settings.database_url
        ASYNC_DATABASE_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
else:
    # Production requires PostgreSQL
    if not settings.database_url:
        raise ValueError("DATABASE_URL must be set in production")
    DATABASE_URL = settings.database_url
    ASYNC_DATABASE_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

# Create engines
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},
        poolclass=NullPool
    )
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool
    )
else:
    # PostgreSQL configuration
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    async_engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

# Create session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Create declarative base
Base = declarative_base()

# Dependency to get database session
async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_session():
    """Synchronous session for non-async operations"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()