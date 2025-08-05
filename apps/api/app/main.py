from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as redis
from app.config import get_settings
from app.api.endpoints import pipeline, documents, websocket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = await redis.from_url(settings.redis_url)
    logger.info("Connected to Redis")
    yield
    # Shutdown
    await app.state.redis.close()
    logger.info("Disconnected from Redis")

app = FastAPI(
    title="Threat Modeling Pipeline API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}