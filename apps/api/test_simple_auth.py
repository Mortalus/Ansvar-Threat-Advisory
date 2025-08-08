#!/usr/bin/env python3
"""
Simple authentication test to isolate the issue
"""

import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import httpx
import threading
import time

from app.services.rbac_service import RBACService
from app.database import get_async_session


class LoginRequest(BaseModel):
    username: str
    password: str


simple_app = FastAPI()


@simple_app.post("/simple-login")
async def simple_login(request: LoginRequest):
    """Ultra-simple login endpoint"""
    print(f"🔍 Simple login called: {request.username}")
    
    try:
        # Create session manually
        session_gen = get_async_session()
        session = await session_gen.__anext__()
        
        print("✅ Got session")
        
        # Create service
        rbac_service = RBACService(session)
        print("✅ Created RBAC service")
        
        # Authenticate
        user, token = await rbac_service.authenticate_user(
            request.username, 
            request.password
        )
        
        print(f"📤 Auth result: user={bool(user)}, token={bool(token)}")
        
        # Cleanup
        await session.close()
        
        if user and token:
            return {
                "success": True,
                "username": user.username,
                "token": token[:20] + "..."
            }
        else:
            raise HTTPException(status_code=401, detail="Authentication failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@simple_app.get("/health")
async def health():
    return {"status": "ok"}


async def test_simple():
    """Test the simple endpoint"""
    
    # Start server in background
    def run_server():
        uvicorn.run(simple_app, host="127.0.0.1", port=8002, log_level="warning")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for startup
    time.sleep(3)
    
    print("🧪 Testing simple authentication...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:8002/simple-login",
                json={"username": "admin", "password": "admin123!"}
            )
            
            print(f"Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Simple auth worked: {data}")
                return True
            else:
                print(f"❌ Simple auth failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_simple())
    print(f"\nSimple test result: {'✅ PASSED' if result else '❌ FAILED'}")