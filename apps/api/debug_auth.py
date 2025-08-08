#!/usr/bin/env python3
"""
Debug authentication integration step by step
"""

import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Import our components
from app.database import get_async_session
from app.services.rbac_service import RBACService
from app.models import User


class LoginRequest(BaseModel):
    username: str
    password: str


# Debug FastAPI app
debug_app = FastAPI(title="RBAC Debug")


async def get_rbac_service_debug():
    """Debug version of RBAC service dependency"""
    print("🔍 Creating RBAC service...")
    
    async for session in get_async_session():
        print("✅ Got database session")
        service = RBACService(session)
        print("✅ Created RBAC service")
        yield service
        print("🔄 Closing RBAC service session")
        break


@debug_app.post("/debug/auth")
async def debug_authenticate(
    request: LoginRequest,
    rbac_service: RBACService = Depends(get_rbac_service_debug)
):
    """Debug authentication endpoint"""
    print(f"🔐 Debug auth called with username: {request.username}")
    
    try:
        print("🔄 Calling authenticate_user...")
        user, token = await rbac_service.authenticate_user(
            request.username, 
            request.password
        )
        print(f"📤 Auth result: user={bool(user)}, token={bool(token)}")
        
        if user and token:
            return {
                "success": True,
                "username": user.username,
                "token": token[:20] + "...",
                "roles": [role.name for role in user.roles]
            }
        else:
            print("❌ Authentication failed in service")
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        print(f"❌ Exception in debug auth: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@debug_app.get("/debug/health")
async def debug_health():
    """Simple health check"""
    return {"status": "healthy"}


async def test_debug_server():
    """Test the debug server"""
    import httpx
    import uvicorn
    import threading
    import time
    
    # Start server in thread
    def run_server():
        uvicorn.run(debug_app, host="127.0.0.1", port=8001, log_level="info")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    print("🧪 Testing debug authentication...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test health
            health_response = await client.get("http://127.0.0.1:8001/debug/health")
            print(f"Health check: {health_response.status_code}")
            
            # Test auth
            auth_response = await client.post(
                "http://127.0.0.1:8001/debug/auth",
                json={"username": "admin", "password": "admin123!"}
            )
            print(f"Auth response: {auth_response.status_code}")
            if auth_response.status_code == 200:
                data = auth_response.json()
                print(f"✅ Debug auth successful: {data}")
            else:
                print(f"❌ Debug auth failed: {auth_response.text}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_debug_server())