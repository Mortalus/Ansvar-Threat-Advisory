from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Phase 2: Structured logging configuration
from app.core.logging_config import setup_logging, LoggingMiddleware, get_logger

# Import configuration
from app.config import settings, get_cors_origins

# Import routers
from app.api.endpoints import documents, pipeline, websocket, llm, tasks, threats, knowledge_base, debug, settings, projects, projects_simple, agents_simple, agent_management, simple_workflows, workflows, workflow_phase1
from app.api.v1 import auth

# Import startup tasks
# Startup tasks imported within lifespan context to avoid circular imports

# Phase 2: Configure structured logging
setup_logging(
    level="INFO",
    enable_structured=True,
    log_file=None  # Could add file logging in production
)
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle with graceful database shutdown
    Phase 2.1: Enhanced connection cleanup
    """
    logger.info("🚀 Starting Threat Modeling API...")
    
    # Startup actions
    logger.info("🔄 Initializing database connections...")
    from app.core.db_connection_manager import get_connection_manager
    manager = await get_connection_manager()
    
    logger.info("🔄 Initializing default data...")
    from app.startup import initialize_default_data_robust
    await initialize_default_data_robust()
    logger.info("✅ Application startup completed")
    
    yield
    
    # Phase 2.1: Graceful shutdown with connection cleanup
    logger.info("🔄 Shutting down Threat Modeling API...")
    try:
        from app.core.db_connection_manager import cleanup_connections
        await cleanup_connections()
        logger.info("✅ Graceful shutdown completed")
    except Exception as e:
        logger.warning(f"⚠️ Shutdown warning (non-critical): {e}")

# Create FastAPI app
app = FastAPI(
    title="Threat Modeling Pipeline API",
    description="AI-powered threat modeling and security analysis platform",
    version="1.0.0",
    lifespan=lifespan
)

# Phase 2: Add structured logging middleware (must be first)
app.add_middleware(
    LoggingMiddleware,
    skip_paths=['/health/live', '/gateway/status']
)

# Configure CORS
cors_origins = get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False if "*" in cors_origins else True,  # Can't use credentials with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(llm.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(threats.router)
app.include_router(knowledge_base.router)
app.include_router(websocket.router)
app.include_router(debug.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(projects_simple.router, prefix="/api")
app.include_router(agents_simple.router)
app.include_router(agent_management.router)
app.include_router(simple_workflows.router, prefix="/api/simple-workflows", tags=["Simple Workflows"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(workflow_phase1.router, prefix="/api/phase1", tags=["Phase 1 Demo"])

# Enhanced health check endpoint with database verification
@app.get("/health")
async def health_check():
    """
    Comprehensive health check with database connectivity verification
    Phase 2: Includes circuit breaker status for resilience monitoring
    Returns detailed system status for debugging distributed system issues
    """
    from app.database import verify_db_health, get_connection_pool_stats
    from app.core.resilience import get_circuit_breaker_status
    
    health_response = {
        "status": "unknown",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "threat-modeling-api",
        "version": "1.0.0",
        "database": {},
        "connection_pools": {},
        "circuit_breakers": {},
        "checks": {}
    }
    
    # Test database connectivity
    db_health = await verify_db_health()
    health_response["database"] = db_health
    
    # Get circuit breaker status (Phase 2)
    health_response["circuit_breakers"] = get_circuit_breaker_status()
    
    # Get connection pool statistics (Phase 2.1)
    health_response["connection_pools"] = get_connection_pool_stats()
    
    # Overall system status
    circuit_issues = any(
        cb["state"] != "closed" 
        for cb in health_response["circuit_breakers"].values()
    )
    
    if db_health["status"] == "healthy" and not circuit_issues:
        health_response["status"] = "healthy"
        health_response["checks"]["database"] = "✅ Connected"
        health_response["checks"]["circuit_breakers"] = "✅ All circuits closed"
    else:
        health_response["status"] = "degraded"  
        health_response["checks"]["database"] = f"❌ {db_health.get('error', 'Unknown error')}" if db_health["status"] != "healthy" else "✅ Connected"
        health_response["checks"]["circuit_breakers"] = "⚠️ Some circuits open" if circuit_issues else "✅ All circuits closed"
    
    # Add service-specific checks
    health_response["checks"]["api"] = "✅ Running"
    health_response["checks"]["environment"] = f"✅ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    
    return health_response

# Simple health endpoint for load balancers
@app.get("/health/live") 
async def liveness_check():
    """Lightweight liveness check for container orchestration"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

# Database-specific health check
@app.get("/health/db")
async def database_health():
    """Detailed database health information for debugging"""
    from app.database import verify_db_health
    return await verify_db_health()

# CRITICAL: Emergency connection pool reset
@app.post("/health/reset-pool") 
async def reset_connection_pool():
    """
    EMERGENCY ENDPOINT: Reset database connection pool
    Use when document upload or other operations fail due to connection issues
    """
    from app.database import reset_connection_pool
    
    logger.warning("🚨 EMERGENCY: Connection pool reset requested")
    
    success = await reset_connection_pool()
    
    if success:
        return {
            "status": "success",
            "message": "Connection pool reset successfully", 
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        return {
            "status": "failed",
            "message": "Connection pool reset failed",
            "timestamp": datetime.utcnow().isoformat()
        }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Threat Modeling Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )