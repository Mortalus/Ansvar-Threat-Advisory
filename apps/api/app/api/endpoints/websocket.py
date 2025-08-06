"""WebSocket endpoints for real-time updates"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
from typing import Dict, Set
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}

class ConnectionManager:
    """Manage WebSocket connections for pipeline updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, pipeline_id: str):
        """Accept and register a new connection"""
        await websocket.accept()
        
        if pipeline_id not in self.active_connections:
            self.active_connections[pipeline_id] = set()
        
        self.active_connections[pipeline_id].add(websocket)
        logger.info(f"WebSocket connected for pipeline {pipeline_id}")
    
    def disconnect(self, websocket: WebSocket, pipeline_id: str):
        """Remove a connection"""
        if pipeline_id in self.active_connections:
            self.active_connections[pipeline_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[pipeline_id]:
                del self.active_connections[pipeline_id]
        
        logger.info(f"WebSocket disconnected for pipeline {pipeline_id}")
    
    async def send_update(self, pipeline_id: str, data: dict):
        """Send update to all connections for a pipeline"""
        if pipeline_id in self.active_connections:
            # Create list to avoid set changing during iteration
            connections = list(self.active_connections[pipeline_id])
            
            for connection in connections:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.error(f"Failed to send update: {e}")
                    # Remove failed connection
                    self.disconnect(connection, pipeline_id)
    
    async def broadcast(self, data: dict):
        """Broadcast to all connected clients"""
        for pipeline_id, connections in self.active_connections.items():
            await self.send_update(pipeline_id, data)

# Create global connection manager
manager = ConnectionManager()

@router.websocket("/ws/{pipeline_id}")
async def websocket_endpoint(websocket: WebSocket, pipeline_id: str):
    """WebSocket endpoint for pipeline updates"""
    await manager.connect(websocket, pipeline_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "pipeline_id": pipeline_id,
            "message": "Connected to pipeline updates"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for any message from client (ping/pong)
            data = await websocket.receive_text()
            
            # Echo back as confirmation (or handle specific commands)
            if data == "ping":
                await websocket.send_text("pong")
            else:
                # Could handle other client messages here
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, pipeline_id)
        logger.info(f"Client disconnected from pipeline {pipeline_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, pipeline_id)

# Helper function to send updates (can be called from other parts of the app)
async def send_pipeline_update(pipeline_id: str, update_data: dict):
    """Send an update to all clients watching a pipeline"""
    await manager.send_update(pipeline_id, update_data)

# Export for use in other modules
__all__ = ["router", "send_pipeline_update", "manager"]