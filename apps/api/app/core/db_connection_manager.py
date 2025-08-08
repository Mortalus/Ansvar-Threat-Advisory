"""
Robust Database Connection Manager

Handles connection pooling issues, event loop problems, and provides fallback mechanisms
for asyncpg connection stability.
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
import asyncpg

logger = logging.getLogger(__name__)


class RobustConnectionManager:
    """
    Manages database connections with multiple fallback strategies
    to handle asyncpg event loop and connection pool issues.
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        self._engine = None
        self._sessionmaker = None
        self._direct_pool = None
        self._initialization_lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize the connection manager with proper event loop handling"""
        async with self._initialization_lock:
            if self._engine is not None:
                return
                
            try:
                # Create engine with NullPool to avoid connection pool issues
                self._engine = create_async_engine(
                    self.async_url,
                    poolclass=NullPool,  # No connection pooling
                    connect_args={
                        "server_settings": {
                            "application_name": "threat_modeling_robust",
                            "jit": "off",
                        },
                        "command_timeout": 60,
                        "max_cached_statement_lifetime": 0,
                        "max_cacheable_statement_size": 0,
                    },
                    echo=False,
                )
                
                # Create session maker
                self._sessionmaker = async_sessionmaker(
                    bind=self._engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=False,
                    autocommit=False,
                )
                
                # Initialize direct connection pool for fallback
                self._direct_pool = await asyncpg.create_pool(
                    host="postgres",
                    port=5432,
                    user="threat_user",
                    password="secure_password_123",
                    database="threat_modeling",
                    min_size=1,
                    max_size=5,
                    max_queries=50000,
                    max_inactive_connection_lifetime=300,
                    command_timeout=60,
                )
                
                logger.info("✅ Robust connection manager initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize connection manager: {e}")
                raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session with multiple fallback strategies.
        
        Strategy order:
        1. Try normal SQLAlchemy session
        2. Reinitialize engine if needed
        3. Use direct asyncpg connection as last resort
        """
        
        # Ensure initialization
        if self._engine is None:
            await self.initialize()
        
        session = None
        connection_method = "sqlalchemy"
        
        try:
            # Strategy 1: Normal SQLAlchemy session
            try:
                session = self._sessionmaker()
                # Test the session
                await session.execute(text("SELECT 1"))
                logger.debug("✅ Using normal SQLAlchemy session")
                
            except Exception as e:
                logger.warning(f"⚠️ Normal session failed: {e}")
                
                # Strategy 2: Reinitialize engine
                try:
                    logger.info("🔄 Reinitializing database engine...")
                    await self._cleanup()
                    await self.initialize()
                    session = self._sessionmaker()
                    await session.execute(text("SELECT 1"))
                    logger.info("✅ Using reinitialized session")
                    
                except Exception as reinit_error:
                    logger.error(f"❌ Reinitialization failed: {reinit_error}")
                    
                    # Strategy 3: Direct asyncpg connection wrapper
                    logger.warning("⚠️ Falling back to direct asyncpg connection")
                    session = await self._create_direct_session()
                    connection_method = "direct"
            
            # Yield the session
            yield session
            
            # Commit if using SQLAlchemy session
            if connection_method == "sqlalchemy":
                try:
                    await session.commit()
                except Exception as commit_error:
                    logger.error(f"❌ Commit failed: {commit_error}")
                    await session.rollback()
                    raise
                    
        except Exception as e:
            logger.error(f"❌ Session error: {e}")
            if session and connection_method == "sqlalchemy":
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    logger.warning(f"⚠️ Rollback failed: {rollback_error}")
            raise
            
        finally:
            if session:
                try:
                    await session.close()
                except Exception as close_error:
                    logger.warning(f"⚠️ Session close warning: {close_error}")
    
    async def _create_direct_session(self) -> AsyncSession:
        """Create a session-like wrapper around a direct asyncpg connection"""
        
        if self._direct_pool is None:
            await self.initialize()
        
        conn = await self._direct_pool.acquire()
        
        # Create a minimal session wrapper
        class DirectSession:
            def __init__(self, connection, pool):
                self._conn = connection
                self._pool = pool
                self._transaction = None
                
            async def execute(self, query, *args, **kwargs):
                """Execute a query"""
                query_str = str(query)
                if hasattr(query, 'compile'):
                    # SQLAlchemy query object
                    compiled = query.compile()
                    query_str = str(compiled)
                    
                result = await self._conn.fetch(query_str)
                
                # Wrap in a result-like object
                class Result:
                    def __init__(self, records):
                        self._records = records
                        
                    def scalar(self):
                        if self._records and len(self._records) > 0:
                            return self._records[0][0]
                        return None
                        
                    def scalar_one_or_none(self):
                        return self.scalar()
                        
                    def all(self):
                        return self._records
                        
                    def first(self):
                        return self._records[0] if self._records else None
                
                return Result(result)
                
            async def commit(self):
                """Commit transaction if exists"""
                if self._transaction:
                    await self._transaction.commit()
                    self._transaction = None
                    
            async def rollback(self):
                """Rollback transaction if exists"""
                if self._transaction:
                    await self._transaction.rollback()
                    self._transaction = None
                    
            async def close(self):
                """Release connection back to pool"""
                if self._transaction:
                    await self.rollback()
                await self._pool.release(self._conn)
                
            async def begin(self):
                """Begin a transaction"""
                self._transaction = self._conn.transaction()
                await self._transaction.start()
                
            def add(self, obj):
                """Compatibility method - does nothing for direct connections"""
                logger.warning("⚠️ add() called on direct connection - operation skipped")
                
            def delete(self, obj):
                """Compatibility method - does nothing for direct connections"""
                logger.warning("⚠️ delete() called on direct connection - operation skipped")
                
            async def flush(self):
                """Compatibility method - does nothing for direct connections"""
                pass
        
        return DirectSession(conn, self._direct_pool)
    
    async def _cleanup(self):
        """Clean up existing connections and engine"""
        
        if self._engine:
            try:
                await self._engine.dispose()
            except Exception as e:
                logger.warning(f"⚠️ Engine disposal warning: {e}")
            self._engine = None
            
        if self._direct_pool:
            try:
                await self._direct_pool.close()
            except Exception as e:
                logger.warning(f"⚠️ Direct pool close warning: {e}")
            self._direct_pool = None
            
        self._sessionmaker = None
        logger.info("✅ Connection manager cleaned up")
    
    async def close(self):
        """Close all connections"""
        await self._cleanup()


# Global connection manager instance
_connection_manager: Optional[RobustConnectionManager] = None


async def get_connection_manager() -> RobustConnectionManager:
    """Get or create the global connection manager"""
    global _connection_manager
    
    if _connection_manager is None:
        from ..config import Settings
        settings = Settings()
        
        if not settings.database_url:
            raise ValueError("DATABASE_URL not configured")
            
        _connection_manager = RobustConnectionManager(settings.database_url)
        await _connection_manager.initialize()
    
    return _connection_manager


@asynccontextmanager
async def get_robust_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a robust database session that handles connection issues gracefully.
    
    This is the main entry point for getting database sessions throughout
    the application.
    """
    manager = await get_connection_manager()
    async with manager.get_session() as session:
        yield session


async def cleanup_connections():
    """Clean up all database connections (for shutdown)"""
    global _connection_manager
    
    if _connection_manager:
        await _connection_manager.close()
        _connection_manager = None
        logger.info("✅ All database connections closed")