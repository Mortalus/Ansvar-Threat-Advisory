"""
WebSocket endpoints for real-time workflow updates in Phase 3.
Provides live status updates for workflow executions.
"""

import json
import uuid
from typing import Dict, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models import User
from app.models.workflow import WorkflowRun, WorkflowStatus
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Connection manager for WebSocket connections
class WorkflowConnectionManager:
    def __init__(self):
        # Store connections by connection ID
        self.connections: Dict[str, WebSocket] = {}
        # Store which runs each connection is subscribed to
        self.subscriptions: Dict[str, Set[str]] = {}  # connection_id -> set of run_ids
        # Store which connections are subscribed to each run
        self.run_subscribers: Dict[str, Set[str]] = {}  # run_id -> set of connection_ids

    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.connections[connection_id] = websocket
        self.subscriptions[connection_id] = set()
        logger.info(f"WebSocket connected: {connection_id}")

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.connections:
            del self.connections[connection_id]
        
        # Remove from all subscriptions
        if connection_id in self.subscriptions:
            for run_id in self.subscriptions[connection_id]:
                if run_id in self.run_subscribers:
                    self.run_subscribers[run_id].discard(connection_id)
            del self.subscriptions[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")

    def subscribe_to_run(self, connection_id: str, run_id: str):
        """Subscribe a connection to a specific workflow run."""
        if connection_id in self.subscriptions:
            self.subscriptions[connection_id].add(run_id)
            
            if run_id not in self.run_subscribers:
                self.run_subscribers[run_id] = set()
            self.run_subscribers[run_id].add(connection_id)
            
            logger.info(f"Connection {connection_id} subscribed to run {run_id}")

    async def send_to_run_subscribers(self, run_id: str, message: dict):
        """Send a message to all connections subscribed to a specific run."""
        if run_id not in self.run_subscribers:
            return
        
        disconnected_connections = []
        for connection_id in self.run_subscribers[run_id]:
            if connection_id in self.connections:
                try:
                    await self.connections[connection_id].send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send message to {connection_id}: {e}")
                    disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)

    async def send_to_all(self, message: dict):
        """Send a message to all connected clients."""
        disconnected_connections = []
        for connection_id, websocket in self.connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message to {connection_id}: {e}")
                disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)

# Global connection manager
workflow_manager = WorkflowConnectionManager()


async def get_current_user_ws(websocket: WebSocket, db: AsyncSession) -> User:
    """Get current user from WebSocket (simplified for Phase 3)."""
    # In Phase 3, we'll use a simplified approach
    # In production, you'd want proper WebSocket authentication
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.username == "admin"))
    user = result.scalar_one_or_none()
    if not user:
        raise Exception("User not found")
    return user


@router.websocket("/ws/workflow")
async def workflow_websocket_all(websocket: WebSocket):
    """WebSocket endpoint for general workflow updates."""
    connection_id = str(uuid.uuid4())
    
    try:
        await workflow_manager.connect(websocket, connection_id)
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connected",
            "connection_id": connection_id,
            "message": "Connected to workflow updates"
        }))
        
        while True:
            try:
                # Receive messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "subscribe" and "run_id" in message:
                    workflow_manager.subscribe_to_run(connection_id, message["run_id"])
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "run_id": message["run_id"]
                    }))
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        workflow_manager.disconnect(connection_id)


@router.websocket("/ws/workflow/{run_id}")
async def workflow_websocket_run(websocket: WebSocket, run_id: str):
    """WebSocket endpoint for specific workflow run updates."""
    connection_id = str(uuid.uuid4())
    
    try:
        await workflow_manager.connect(websocket, connection_id)
        workflow_manager.subscribe_to_run(connection_id, run_id)
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connected",
            "connection_id": connection_id,
            "run_id": run_id,
            "message": f"Connected to workflow run {run_id}"
        }))
        
        while True:
            try:
                # Keep connection alive and handle messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        workflow_manager.disconnect(connection_id)


# Utility functions to send updates (called from workflow execution)
async def notify_run_status_change(run_id: str, status: WorkflowStatus, progress: float):
    """Notify subscribers about workflow run status changes."""
    message = {
        "type": "run_status",
        "run_id": run_id,
        "data": {
            "status": status.value,
            "progress": progress
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await workflow_manager.send_to_run_subscribers(run_id, message)
    await workflow_manager.send_to_all(message)


async def notify_step_completion(run_id: str, step_id: str, status: str, execution_time_ms: int):
    """Notify subscribers about step completion."""
    message = {
        "type": "step_status",
        "run_id": run_id,
        "data": {
            "step_id": step_id,
            "status": status,
            "execution_time_ms": execution_time_ms
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await workflow_manager.send_to_run_subscribers(run_id, message)


async def notify_artifact_created(run_id: str, step_id: str, artifact_id: str, artifact_name: str):
    """Notify subscribers about new artifact creation."""
    message = {
        "type": "artifact_created",
        "run_id": run_id,
        "data": {
            "step_id": step_id,
            "artifact_id": artifact_id,
            "artifact_name": artifact_name
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await workflow_manager.send_to_run_subscribers(run_id, message)


async def notify_error(run_id: str, error_message: str, step_id: str = None):
    """Notify subscribers about workflow errors."""
    message = {
        "type": "error",
        "run_id": run_id,
        "data": {
            "error_message": error_message,
            "step_id": step_id
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await workflow_manager.send_to_run_subscribers(run_id, message)


# Export the manager for use in other modules
__all__ = [
    'router', 
    'workflow_manager',
    'notify_run_status_change',
    'notify_step_completion', 
    'notify_artifact_created',
    'notify_error'
]