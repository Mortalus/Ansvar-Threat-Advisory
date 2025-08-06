"""WebSocket endpoints for real-time updates"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
from typing import Dict, Set, Optional, Any
import asyncio
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)
router = APIRouter()

class UpdateType(str, Enum):
    """Types of WebSocket updates"""
    CONNECTION = "connection"
    TASK_QUEUED = "task_queued"
    TASK_PROGRESS = "task_progress" 
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    PIPELINE_STATUS = "pipeline_status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"

class ConnectionManager:
    """Enhanced WebSocket connection manager for pipeline updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, pipeline_id: str):
        """Accept and register a new connection"""
        await websocket.accept()
        
        if pipeline_id not in self.active_connections:
            self.active_connections[pipeline_id] = set()
        
        self.active_connections[pipeline_id].add(websocket)
        self.connection_metadata[websocket] = {
            "pipeline_id": pipeline_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        
        logger.info(f"WebSocket connected for pipeline {pipeline_id} (total: {len(self.active_connections[pipeline_id])})")
    
    def disconnect(self, websocket: WebSocket, pipeline_id: str):
        """Remove a connection"""
        if pipeline_id in self.active_connections:
            self.active_connections[pipeline_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[pipeline_id]:
                del self.active_connections[pipeline_id]
        
        # Clean up metadata
        self.connection_metadata.pop(websocket, None)
        
        remaining = len(self.active_connections.get(pipeline_id, []))
        logger.info(f"WebSocket disconnected for pipeline {pipeline_id} (remaining: {remaining})")
    
    async def send_update(self, pipeline_id: str, data: dict):
        """Send update to all connections for a pipeline"""
        if pipeline_id not in self.active_connections:
            logger.debug(f"No active connections for pipeline {pipeline_id}")
            return
            
        # Add timestamp to all updates
        data["timestamp"] = datetime.utcnow().isoformat()
        
        # Create list to avoid set changing during iteration
        connections = list(self.active_connections[pipeline_id])
        failed_connections = []
        
        for connection in connections:
            try:
                await connection.send_json(data)
                logger.debug(f"Sent update to pipeline {pipeline_id}: {data.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"Failed to send update to pipeline {pipeline_id}: {e}")
                failed_connections.append(connection)
        
        # Clean up failed connections
        for connection in failed_connections:
            self.disconnect(connection, pipeline_id)
    
    async def broadcast(self, data: dict):
        """Broadcast to all connected clients"""
        for pipeline_id in list(self.active_connections.keys()):
            await self.send_update(pipeline_id, data)
    
    async def send_task_update(self, pipeline_id: str, update_type: UpdateType, task_data: dict):
        """Send a formatted task update"""
        update_data = {
            "type": update_type.value,
            "pipeline_id": pipeline_id,
            **task_data
        }
        await self.send_update(pipeline_id, update_data)
    
    def get_connection_count(self, pipeline_id: Optional[str] = None) -> int:
        """Get connection count for a pipeline or all pipelines"""
        if pipeline_id:
            return len(self.active_connections.get(pipeline_id, []))
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_active_pipelines(self) -> list:
        """Get list of pipeline IDs with active connections"""
        return list(self.active_connections.keys())

# Create global connection manager
manager = ConnectionManager()

@router.websocket("/ws/{pipeline_id}")
async def websocket_endpoint(websocket: WebSocket, pipeline_id: str):
    """Enhanced WebSocket endpoint for pipeline updates"""
    await manager.connect(websocket, pipeline_id)
    
    try:
        # Send initial connection confirmation
        await manager.send_task_update(
            pipeline_id, 
            UpdateType.CONNECTION, 
            {
                "message": "Connected to pipeline updates",
                "pipeline_id": pipeline_id,
                "connection_count": manager.get_connection_count(pipeline_id)
            }
        )
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat_loop(websocket, pipeline_id))
        
        try:
            # Keep connection alive and handle incoming messages
            while True:
                # Wait for any message from client (ping/pong)
                data = await websocket.receive_text()
                
                try:
                    # Try to parse as JSON for commands
                    message = json.loads(data)
                    await handle_client_message(websocket, pipeline_id, message)
                except json.JSONDecodeError:
                    # Handle simple text messages
                    if data == "ping":
                        await websocket.send_text("pong")
                        # Update last ping time
                        if websocket in manager.connection_metadata:
                            manager.connection_metadata[websocket]["last_ping"] = datetime.utcnow()
                    else:
                        logger.debug(f"Received text message from {pipeline_id}: {data}")
                        
        finally:
            # Cancel heartbeat task
            heartbeat_task.cancel()
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, pipeline_id)
        logger.info(f"Client disconnected from pipeline {pipeline_id}")
    except Exception as e:
        logger.error(f"WebSocket error for pipeline {pipeline_id}: {e}")
        manager.disconnect(websocket, pipeline_id)


async def heartbeat_loop(websocket: WebSocket, pipeline_id: str):
    """Send periodic heartbeat messages to keep connection alive"""
    try:
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            await websocket.send_json({
                "type": UpdateType.HEARTBEAT.value,
                "pipeline_id": pipeline_id,
                "timestamp": datetime.utcnow().isoformat()
            })
    except Exception as e:
        logger.debug(f"Heartbeat ended for pipeline {pipeline_id}: {e}")


async def handle_client_message(websocket: WebSocket, pipeline_id: str, message: dict):
    """Handle JSON messages from clients"""
    message_type = message.get("type")
    
    if message_type == "subscribe_to_task":
        # Client wants to subscribe to a specific task
        task_id = message.get("task_id")
        if task_id:
            logger.info(f"Client subscribed to task {task_id} for pipeline {pipeline_id}")
            await websocket.send_json({
                "type": "subscription_confirmed",
                "task_id": task_id,
                "pipeline_id": pipeline_id
            })
    
    elif message_type == "get_pipeline_status":
        # Client requests current pipeline status
        # We could fetch and send current status here
        await websocket.send_json({
            "type": "status_requested",
            "pipeline_id": pipeline_id,
            "message": "Status request received"
        })
    
    else:
        logger.debug(f"Unknown message type from {pipeline_id}: {message_type}")

# Helper functions to send updates (can be called from other parts of the app)
async def send_pipeline_update(pipeline_id: str, update_data: dict):
    """Send an update to all clients watching a pipeline"""
    await manager.send_update(pipeline_id, update_data)


async def notify_task_queued(pipeline_id: str, task_id: str, step: str):
    """Notify clients that a task has been queued"""
    await manager.send_task_update(
        pipeline_id,
        UpdateType.TASK_QUEUED,
        {
            "task_id": task_id,
            "step": step,
            "message": f"Task {step} queued for execution"
        }
    )


async def notify_task_progress(pipeline_id: str, task_id: str, step: str, progress_data: dict):
    """Notify clients of task progress"""
    await manager.send_task_update(
        pipeline_id,
        UpdateType.TASK_PROGRESS,
        {
            "task_id": task_id,
            "step": step,
            "progress": progress_data,
            "message": progress_data.get("status", "Task in progress")
        }
    )


async def notify_task_completed(pipeline_id: str, task_id: str, step: str, result_data: dict):
    """Notify clients that a task has completed successfully"""
    await manager.send_task_update(
        pipeline_id,
        UpdateType.TASK_COMPLETED,
        {
            "task_id": task_id,
            "step": step,
            "result": result_data,
            "message": f"Task {step} completed successfully"
        }
    )


async def notify_task_failed(pipeline_id: str, task_id: str, step: str, error: str):
    """Notify clients that a task has failed"""
    await manager.send_task_update(
        pipeline_id,
        UpdateType.TASK_FAILED,
        {
            "task_id": task_id,
            "step": step,
            "error": error,
            "message": f"Task {step} failed: {error}"
        }
    )


async def notify_step_started(pipeline_id: str, step: str):
    """Notify clients that a pipeline step has started"""
    await manager.send_task_update(
        pipeline_id,
        UpdateType.STEP_STARTED,
        {
            "step": step,
            "message": f"Pipeline step {step} started"
        }
    )


async def notify_step_completed(pipeline_id: str, step: str, result_data: dict):
    """Notify clients that a pipeline step has completed"""
    await manager.send_task_update(
        pipeline_id,
        UpdateType.STEP_COMPLETED,
        {
            "step": step,
            "result": result_data,
            "message": f"Pipeline step {step} completed"
        }
    )


async def notify_pipeline_status_change(pipeline_id: str, status: str, message: Optional[str] = None):
    """Notify clients of pipeline status changes"""
    await manager.send_task_update(
        pipeline_id,
        UpdateType.PIPELINE_STATUS,
        {
            "status": status,
            "message": message or f"Pipeline status changed to {status}"
        }
    )


# Export for use in other modules
__all__ = [
    "router", 
    "manager",
    "send_pipeline_update",
    "notify_task_queued",
    "notify_task_progress", 
    "notify_task_completed",
    "notify_task_failed",
    "notify_step_started",
    "notify_step_completed", 
    "notify_pipeline_status_change",
    "UpdateType"
]