#!/usr/bin/env python3
"""Simple WebSocket client for testing real-time notifications

Note: This is a manual E2E helper, not an automated pytest test module.
"""

import pytest
pytestmark = pytest.mark.skip(reason="Manual WebSocket E2E helper; skip during automated pytest runs")

import asyncio
import websockets
import json
import sys
from datetime import datetime

class WebSocketTestClient:
    def __init__(self, pipeline_id: str, url: str = "ws://localhost:8000"):
        self.pipeline_id = pipeline_id
        self.websocket_url = f"{url}/ws/{pipeline_id}"
        self.websocket = None
        self.messages_received = []

    async def connect(self):
        """Connect to WebSocket endpoint"""
        try:
            print(f"🔌 Connecting to {self.websocket_url}")
            self.websocket = await websockets.connect(self.websocket_url)
            print(f"✅ Connected to pipeline {self.pipeline_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    async def listen(self, duration: int = 60):
        """Listen for messages for a specified duration"""
        if not self.websocket:
            print("❌ Not connected")
            return

        print(f"👂 Listening for messages for {duration} seconds...")
        
        try:
            # Set a timeout for receiving messages
            end_time = asyncio.get_event_loop().time() + duration
            
            while asyncio.get_event_loop().time() < end_time:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=5.0
                    )
                    
                    # Parse and display message
                    await self.handle_message(message)
                    
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await self.websocket.send("ping")
                    print("📡 Sent ping to keep connection alive")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed by server")
        except Exception as e:
            print(f"❌ Error while listening: {e}")

    async def handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            timestamp = data.get("timestamp", datetime.now().isoformat())
            
            # Store message
            self.messages_received.append(data)
            
            # Display message based on type
            if message_type == "connection":
                print(f"🟢 [{timestamp}] Connected: {data.get('message')}")
                
            elif message_type == "task_queued":
                task_id = data.get("task_id", "unknown")
                step = data.get("step", "unknown")
                print(f"📋 [{timestamp}] Task Queued: {step} (ID: {task_id})")
                
            elif message_type == "step_started":
                step = data.get("step", "unknown")
                print(f"🚀 [{timestamp}] Step Started: {step}")
                
            elif message_type == "task_progress":
                step = data.get("step", "unknown")
                progress = data.get("progress", {})
                print(f"⏳ [{timestamp}] Task Progress: {step} - {progress.get('status', 'in progress')}")
                
            elif message_type == "step_completed":
                step = data.get("step", "unknown")
                print(f"✅ [{timestamp}] Step Completed: {step}")
                
            elif message_type == "task_completed":
                step = data.get("step", "unknown")
                task_id = data.get("task_id", "unknown")
                print(f"🎉 [{timestamp}] Task Completed: {step} (ID: {task_id})")
                
            elif message_type == "task_failed":
                step = data.get("step", "unknown")
                error = data.get("error", "unknown error")
                print(f"❌ [{timestamp}] Task Failed: {step} - {error}")
                
            elif message_type == "heartbeat":
                print(f"💓 [{timestamp}] Heartbeat")
                
            else:
                print(f"📄 [{timestamp}] Unknown message type: {message_type}")
                print(f"    Data: {json.dumps(data, indent=2)}")
                
        except json.JSONDecodeError:
            # Handle non-JSON messages
            print(f"📄 [{datetime.now().isoformat()}] Text message: {message}")

    async def send_message(self, message: dict):
        """Send a message to the server"""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
            print(f"📤 Sent: {message}")

    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected")

    def print_summary(self):
        """Print summary of received messages"""
        print(f"\n📊 Summary: Received {len(self.messages_received)} messages")
        
        message_counts = {}
        for msg in self.messages_received:
            msg_type = msg.get("type", "unknown")
            message_counts[msg_type] = message_counts.get(msg_type, 0) + 1
        
        for msg_type, count in message_counts.items():
            print(f"   {msg_type}: {count}")


async def test_websocket_with_background_task(pipeline_id: str):
    """Test WebSocket notifications with a real background task"""
    client = WebSocketTestClient(pipeline_id)
    
    # Connect to WebSocket
    if not await client.connect():
        return
    
    try:
        # Start listening in the background
        listen_task = asyncio.create_task(client.listen(120))  # Listen for 2 minutes
        
        # Wait a bit for connection to establish
        await asyncio.sleep(2)
        
        # Trigger a background task via HTTP API
        print("\n🔧 Triggering background DFD extraction task...")
        
        import httpx
        async with httpx.AsyncClient() as http_client:
            try:
                response = await http_client.post(
                    "http://localhost:8000/api/tasks/execute-step",
                    json={
                        "pipeline_id": pipeline_id,
                        "step": "dfd_extraction",
                        "data": {}
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Task queued successfully: {result.get('task_id')}")
                else:
                    print(f"❌ Failed to queue task: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ HTTP request failed: {e}")
        
        # Wait for messages
        await listen_task
        
    finally:
        await client.disconnect()
        client.print_summary()


async def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python test_websocket_client.py <pipeline_id>")
        print("\nExample:")
        print("  python test_websocket_client.py b354080a-6081-4069-8422-12959e75b543")
        return
    
    pipeline_id = sys.argv[1]
    print(f"🧪 Testing WebSocket notifications for pipeline: {pipeline_id}")
    
    await test_websocket_with_background_task(pipeline_id)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")