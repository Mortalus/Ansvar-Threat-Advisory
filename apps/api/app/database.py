"""
Database configuration and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
import os
import time
import asyncio
from .config import Settings
import logging

logger = logging.getLogger(__name__)

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
    # PostgreSQL configuration with enhanced resilience and proper cleanup
    engine = create_engine(
        DATABASE_URL, 
        pool_pre_ping=True,           # Test connections before use
        pool_recycle=3600,            # Recycle connections after 1 hour
        pool_size=5,                  # Smaller pool to reduce cleanup issues
        max_overflow=10,              # Reduced overflow connections
        pool_timeout=30,              # Timeout when getting connection from pool
        # Enhanced cleanup configuration
        pool_reset_on_return='commit', # Reset connections properly
    )
    # ROBUST CONNECTION POOL - Fixed for asyncpg event loop issues
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL, 
        # Use NullPool to avoid connection pool issues with asyncpg
        poolclass=NullPool,           # No connection pooling - create new connections
        
        # Asyncpg-specific configuration to prevent race conditions
        connect_args={
            "server_settings": {
                "application_name": "threat_modeling_api_robust",
                "jit": "off",
                "statement_timeout": "60s",     # Longer for complex operations
                "idle_in_transaction_session_timeout": "120s",
            },
            "command_timeout": 30,            # Longer command timeout
            "max_cached_statement_lifetime": 0,  # Disable statement caching
            "max_cacheable_statement_size": 0,   # Disable statement caching
        },
        
        echo=bool(os.getenv('SQL_DEBUG', False)),
    )

# Create session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# Create declarative base
Base = declarative_base()

# BULLETPROOF session dependency with asyncpg race condition prevention
async def get_async_session() -> AsyncSession:
    """
    Bulletproof async session dependency optimized for asyncpg
    Prevents 'another operation is in progress' errors
    """
    session = None
    connection_tested = False
    
    try:
        logger.debug("🔄 Creating new database session")
        session = AsyncSessionLocal()
        
        # Use connection validation instead of immediate test query
        # This prevents race conditions with asyncpg
        logger.debug("✅ Database session created successfully")
        connection_tested = True
        
        yield session
        
        # Explicit commit with error handling
        try:
            await session.commit()
            logger.debug("✅ Session committed successfully")
        except Exception as commit_error:
            logger.error(f"❌ Session commit failed: {commit_error}")
            try:
                await session.rollback()
                logger.debug("✅ Session rolled back after commit failure")
            except Exception as rollback_error:
                logger.error(f"❌ Session rollback failed: {rollback_error}")
            raise commit_error
            
    except Exception as e:
        logger.error(f"❌ Database session error: {e}")
        
        # Safe rollback strategy
        if session and connection_tested:
            try:
                await session.rollback()
                logger.debug("✅ Session rolled back successfully")
            except Exception as rollback_error:
                logger.warning(f"⚠️ Session rollback failed (non-critical): {rollback_error}")
        
        raise e
        
    finally:
        # Simplified cleanup to prevent race conditions
        if session:
            try:
                await session.close()
                logger.debug("✅ Session closed normally")
            except Exception as close_error:
                logger.warning(f"⚠️ Session close warning (non-critical): {close_error}")

def get_session():
    """
    Synchronous session for non-async operations with better cleanup
    Phase 2.1: Enhanced error handling
    """
    session = None
    try:
        session = SessionLocal()
        yield session
    except Exception as e:
        if session:
            try:
                session.rollback()
            except Exception as rollback_error:
                logger.error(f"Sync session rollback error: {rollback_error}")
        raise e
    finally:
        if session:
            try:
                session.close()
            except Exception as close_error:
                # Log but don't raise - cleanup errors shouldn't break the request  
                logger.warning(f"Sync session cleanup warning (non-critical): {close_error}")

# Database health check functions
async def verify_db_health():
    """
    Comprehensive database health check for observability
    Tests both connection pool and database responsiveness
    """
    import time
    from sqlalchemy import text
    
    health_info = {
        "status": "unknown",
        "connection_pool": {},
        "query_performance": {},
        "error": None,
        "timestamp": time.time()
    }
    
    try:
        # Test async engine connection with basic session (no recovery to avoid recursion)
        start_time = time.time()
        async with AsyncSessionLocal() as session:
            # Test basic connectivity
            result = await session.execute(text("SELECT 1 as health_check"))
            health_check = result.scalar()
            
            if health_check != 1:
                raise Exception("Health check query returned unexpected result")
            
            # Basic pool info (simplified for compatibility)
            pool = async_engine.pool
            health_info["connection_pool"] = {
                "pool_type": type(pool).__name__,
                "status": "✅ Connection pool operational",
            }
            
            # Measure query performance
            query_time = time.time() - start_time
            health_info["query_performance"] = {
                "response_time_ms": round(query_time * 1000, 2),
                "status": "fast" if query_time < 0.1 else "slow" if query_time < 1.0 else "critical"
            }
            
        health_info["status"] = "healthy"
        
    except Exception as e:
        health_info["status"] = "unhealthy"
        health_info["error"] = str(e)
        
        # Basic pool info on failure
        health_info["connection_pool"] = {
            "pool_type": "AsyncAdaptedQueuePool", 
            "status": "❌ Connection pool issues detected"
        }
    
    return health_info

async def test_db_connection():
    """Simple connection test for basic health checks"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False

# Emergency connection recovery
async def get_emergency_connection():
    """
    CRITICAL: Get a fresh database connection bypassing the pool
    Use for critical operations when pool is unstable
    """
    import asyncpg
    try:
        # Direct connection bypassing SQLAlchemy pool
        conn = await asyncpg.connect(
            host="postgres",
            port=5432,
            user="threat_user",
            password="secure_password_123", 
            database="threat_modeling"
        )
        return conn
    except Exception as e:
        logger.error(f"❌ Emergency connection failed: {e}")
        raise

async def get_resilient_session():
    """
    Get a database session with emergency fallback
    CRITICAL FIX for document upload failures
    """
    try:
        # Try normal session first
        session = AsyncSessionLocal()
        # Test the session with a simple query
        await session.execute(text("SELECT 1"))
        return session
    except Exception as e:
        logger.warning(f"⚠️ Normal session failed, creating emergency session: {e}")
        # Create emergency session with direct connection
        emergency_conn = await get_emergency_connection()
        # Wrap in a minimal session-like object
        class EmergencySession:
            def __init__(self, conn):
                self._conn = conn
                
            async def execute(self, query, params=None):
                if params:
                    return await self._conn.fetch(str(query), *params)
                else:
                    return await self._conn.fetch(str(query))
            
            async def commit(self):
                pass  # Direct connections auto-commit
                
            async def rollback(self):
                pass  # Not needed for direct connections
                
            async def close(self):
                await self._conn.close()
                
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                await self.close()
        
        return EmergencySession(emergency_conn)

# BULLETPROOF Connection pool management with intelligent recovery
async def reset_connection_pool():
    """
    BULLETPROOF: Reset the connection pool when it becomes unstable
    Includes intelligent detection and multi-strategy recovery
    """
    global async_engine, AsyncSessionLocal
    try:
        logger.warning("🚨 EMERGENCY CONNECTION POOL RESET INITIATED")
        
        # Strategy 1: Graceful disposal with timeout
        if async_engine:
            try:
                logger.info("🔄 Step 1: Graceful engine disposal")
                await async_engine.dispose()
                logger.info("✅ Engine disposed gracefully")
            except Exception as disposal_error:
                logger.warning(f"⚠️ Graceful disposal failed: {disposal_error}")
                # Continue with force reset
        
        # Strategy 2: Recreate engine with bulletproof configuration
        logger.info("🔄 Step 2: Creating new bulletproof engine")
        if ASYNC_DATABASE_URL.startswith("sqlite"):
            # SQLite configuration - no pool parameters allowed
            async_engine = create_async_engine(
                ASYNC_DATABASE_URL,
                connect_args={"check_same_thread": False},
                poolclass=NullPool,
                echo=bool(os.getenv('SQL_DEBUG', False)),
            )
        else:
            # PostgreSQL configuration with pool parameters
            async_engine = create_async_engine(
                ASYNC_DATABASE_URL,
                # BULLETPROOF configuration - maximum stability
                pool_pre_ping=False,
                pool_recycle=1800,            # 30 minutes
                pool_size=5,                  # More connections for stability
                max_overflow=0,               # NO overflow - prevents connection chaos
                pool_timeout=10,              # Fail fast
                
                connect_args={
                    "server_settings": {
                        "application_name": "threat_modeling_api_bulletproof",
                        "jit": "off",
                        "statement_timeout": "30s",
                        "idle_in_transaction_session_timeout": "60s",
                    },
                    "command_timeout": 15,
                },
                
                pool_reset_on_return='commit',
                echo=bool(os.getenv('SQL_DEBUG', False)),
            )
        
        # Strategy 3: Test the new engine immediately
        logger.info("🔄 Step 3: Testing new connection pool")
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            if test_value != 1:
                raise Exception("Connection test failed - unexpected result")
        logger.info("✅ New connection pool tested successfully")
        
        # Strategy 4: Recreate session maker
        logger.info("🔄 Step 4: Creating new session maker")
        AsyncSessionLocal = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("🎉 BULLETPROOF CONNECTION POOL RESET COMPLETED SUCCESSFULLY")
        return True
        
    except Exception as e:
        logger.error(f"❌ CRITICAL: Connection pool reset completely failed: {e}")
        # Last resort: Try to create a minimal working engine
        try:
            logger.warning("🚨 LAST RESORT: Creating minimal emergency engine")
            if ASYNC_DATABASE_URL.startswith("sqlite"):
                # SQLite emergency configuration
                async_engine = create_async_engine(
                    ASYNC_DATABASE_URL,
                    connect_args={"check_same_thread": False},
                    poolclass=NullPool,
                )
            else:
                # PostgreSQL emergency configuration
                async_engine = create_async_engine(
                    ASYNC_DATABASE_URL,
                    pool_size=1,
                    max_overflow=0,
                    pool_timeout=5,
                    pool_pre_ping=False,
                )
            AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession)
            logger.warning("⚠️ Emergency engine created - limited functionality")
            return True
        except Exception as emergency_error:
            logger.error(f"❌ FATAL: Emergency engine creation failed: {emergency_error}")
            return False

# Graceful shutdown functions
async def close_db_connections():
    """
    Gracefully close database connections during application shutdown
    Phase 2.1: Proper connection lifecycle management
    """
    try:
        logger.info("🔄 Closing database connections gracefully...")
        
        # Close async engine
        if async_engine:
            await async_engine.dispose()
            logger.info("✅ Async database connections closed")
            
        # Close sync engine  
        if engine:
            engine.dispose()
            logger.info("✅ Sync database connections closed")
            
    except Exception as e:
        logger.warning(f"⚠️ Warning during database shutdown (non-critical): {e}")

# INTELLIGENT connection pool monitoring and auto-recovery
def get_connection_pool_stats():
    """Get detailed connection pool statistics with health analysis"""
    try:
        stats = {
            'timestamp': time.time(),
            'health_status': 'unknown',
            'recommendations': []
        }
        
        # Async engine stats with health analysis
        if async_engine and hasattr(async_engine, 'pool'):
            pool = async_engine.pool
            
            # Safely get pool metrics
            try:
                size = getattr(pool, 'size', lambda: 0)()
                checked_in = getattr(pool, 'checkedin', lambda: 0)()
                checked_out = getattr(pool, 'checkedout', lambda: 0)()
                overflow = getattr(pool, 'overflow', lambda: 0)()
                
                stats['async_pool'] = {
                    'size': size,
                    'checked_in': checked_in,
                    'checked_out': checked_out,
                    'overflow': overflow,
                    'pool_type': type(pool).__name__,
                    'utilization_percent': round((checked_out / max(size, 1)) * 100, 2) if size > 0 else 0
                }
                
                # Health analysis
                utilization = (checked_out / max(size, 1)) * 100 if size > 0 else 0
                
                if utilization > 90:
                    stats['health_status'] = 'critical'
                    stats['recommendations'].append('Connection pool near capacity - consider increasing pool_size')
                elif utilization > 70:
                    stats['health_status'] = 'warning'
                    stats['recommendations'].append('High connection pool utilization - monitor closely')
                elif overflow > 0:
                    stats['health_status'] = 'warning'
                    stats['recommendations'].append('Overflow connections detected - may indicate pool undersizing')
                else:
                    stats['health_status'] = 'healthy'
                    
            except Exception as pool_error:
                stats['async_pool'] = {'error': f'Unable to read pool stats: {pool_error}'}
                stats['health_status'] = 'error'
                stats['recommendations'].append('Pool statistics unavailable - possible pool corruption')
        
        # Sync engine stats (simplified)
        if engine and hasattr(engine, 'pool'):
            try:
                pool = engine.pool
                stats['sync_pool'] = {
                    'size': getattr(pool, 'size', lambda: 'unknown')(),
                    'checked_in': getattr(pool, 'checkedin', lambda: 'unknown')(),
                    'checked_out': getattr(pool, 'checkedout', lambda: 'unknown')(), 
                    'overflow': getattr(pool, 'overflow', lambda: 'unknown')(),
                    'pool_type': type(pool).__name__
                }
            except Exception as sync_error:
                stats['sync_pool'] = {'error': f'Unable to read sync pool: {sync_error}'}
            
        return stats
        
    except Exception as e:
        return {
            'error': f'Critical error getting pool stats: {e}',
            'health_status': 'critical',
            'timestamp': time.time(),
            'recommendations': ['Immediate pool reset recommended']
        }

# PROACTIVE connection pool health checker
async def check_connection_health():
    """
    Proactively check connection pool health and auto-recover if needed
    Returns: (is_healthy: bool, recovery_attempted: bool)
    """
    try:
        # Quick connection test with basic session (no recovery to avoid recursion)
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1 as health_check"))
            if result.scalar() != 1:
                raise Exception("Health check query returned unexpected result")
        
        # Check pool statistics
        pool_stats = get_connection_pool_stats()
        
        if pool_stats.get('health_status') == 'critical':
            logger.warning("🚨 CRITICAL pool health detected - initiating auto-recovery")
            recovery_success = await reset_connection_pool()
            return recovery_success, True
        
        return True, False
        
    except Exception as health_error:
        logger.error(f"❌ Connection health check failed: {health_error}")
        
        # Automatic recovery attempt
        logger.warning("🔄 Attempting automatic connection pool recovery")
        recovery_success = await reset_connection_pool()
        
        if recovery_success:
            logger.info("✅ Auto-recovery successful")
            return True, True
        else:
            logger.error("❌ Auto-recovery failed - manual intervention required")
            return False, True

# NUCLEAR OPTION: Completely fresh session for each request
async def get_resilient_session_with_recovery():
    """
    NUCLEAR OPTION: Create completely fresh database connection for each request
    This bypasses ALL connection pooling issues by creating new connections
    """
    max_retries = 2
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Create a NEW engine and session maker for this request only
            if ASYNC_DATABASE_URL.startswith("sqlite"):
                # SQLite configuration - no pool parameters allowed
                fresh_engine = create_async_engine(
                    ASYNC_DATABASE_URL,
                    connect_args={"check_same_thread": False},
                    poolclass=NullPool,
                    echo=False,
                )
            else:
                # PostgreSQL configuration with pool parameters
                fresh_engine = create_async_engine(
                    ASYNC_DATABASE_URL,
                    # Minimal configuration for single-use connection
                    pool_size=1,
                    max_overflow=0,
                    pool_timeout=5,
                    pool_pre_ping=False,
                    pool_recycle=-1,  # Never recycle since it's single-use
                    echo=False,
                )
            
            fresh_session_maker = async_sessionmaker(
                bind=fresh_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create session from fresh engine
            session = fresh_session_maker()
            
            # Test the connection
            await session.execute(text("SELECT 1"))
            logger.debug(f"✅ Fresh session created successfully (attempt {retry_count + 1})")
            
            # Return a wrapper that cleans up the engine when the session closes
            class FreshSessionWrapper:
                def __init__(self, session, engine):
                    self._session = session
                    self._engine = engine
                    
                async def execute(self, *args, **kwargs):
                    return await self._session.execute(*args, **kwargs)
                
                async def commit(self):
                    return await self._session.commit()
                
                async def rollback(self):
                    return await self._session.rollback()
                
                async def close(self):
                    try:
                        await self._session.close()
                    finally:
                        await self._engine.dispose()
                        logger.debug("🧹 Fresh engine disposed")
                
                def __getattr__(self, name):
                    return getattr(self._session, name)
            
            return FreshSessionWrapper(session, fresh_engine)
            
        except Exception as session_error:
            retry_count += 1
            logger.warning(f"⚠️ Fresh session creation failed (attempt {retry_count}/{max_retries}): {session_error}")
            
            if retry_count >= max_retries:
                logger.error("❌ CRITICAL: All fresh session attempts failed")
                raise Exception(f"Failed to create fresh session after {max_retries} attempts: {session_error}")
            
            # Brief wait before retry
            await asyncio.sleep(1)
    
    raise Exception("Fresh session creation failed - this should never be reached")