from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Import configuration
from app.config import settings, get_cors_origins

# Import routers
from app.api.endpoints import documents, pipeline, websocket, llm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Threat Modeling API...")
    
    # Startup actions
    # TODO: Initialize database connections, cache, etc.
    
    yield
    
    # Shutdown actions
    logger.info("Shutting down Threat Modeling API...")

# Create FastAPI app
app = FastAPI(
    title="Threat Modeling Pipeline API",
    description="AI-powered threat modeling and security analysis platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),  # Use origins from config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(llm.router, prefix="/api")
app.include_router(websocket.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "threat-modeling-api"
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
async def not_found_handler(request, exc):
    return {"error": "Not found", "path": request.url.path}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {"error": "Internal server error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )