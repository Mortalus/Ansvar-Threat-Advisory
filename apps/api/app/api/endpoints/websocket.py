from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
from typing import Set

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@router.websocket("/pipeline/{pipeline_id}")
async def websocket_endpoint(websocket: WebSocket, pipeline_id: str):
    await manager.connect(websocket)
    try:
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "message": f"Connected to pipeline {pipeline_id}",
                "pipeline_id": pipeline_id
            }),
            websocket
        )
        
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client disconnected from pipeline {pipeline_id}")