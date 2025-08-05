from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.endpoints import pipeline, documents, websocket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Threat Modeling Pipeline API",
    version="1.0.0"
)

# CORS middleware - more permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.get("/")
async def root():
    return {"message": "Threat Modeling Pipeline API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Set Redis to None for now if not needed
app.state.redis = None
