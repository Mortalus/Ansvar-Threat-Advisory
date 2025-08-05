# apps/api/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import pipeline, documents, websocket
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Threat Modeling Pipeline API",
    description="API for AI-powered threat modeling pipeline",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pipeline.router, prefix="/api", tags=["pipeline"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.get("/")
async def root():
    return {
        "message": "Threat Modeling Pipeline API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}