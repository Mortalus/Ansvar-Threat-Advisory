#!/usr/bin/env python3
"""
Final authentication test - no shell escaping issues
"""

import asyncio
import json
from app.services.rbac_service import RBACService
from app.database import get_async_session


async def reset_and_test():
    """Reset admin user with a simple password and test"""
    print("🔧 Resetting admin user with simple password...")
    
    session_gen = get_async_session()
    session = await session_gen.__anext__()
    service = RBACService(session)
    
    # Reset with simple password
    user = await service.get_user_by_username('admin')
    if user:
        user.failed_login_attempts = 0
        user.account_locked = False
        await service.change_password(user.id, 'password123')
        print("✅ Admin password reset to 'password123'")
        
        # Test immediately
        test_user, token = await service.authenticate_user('admin', 'password123')
        print(f"✅ Immediate test: user={bool(test_user)}, token={bool(token)}")
        
    await session.close()


async def test_json_parsing():
    """Test how JSON parsing affects the password"""
    print("\n🔍 Testing JSON password parsing...")
    
    # Simulate what FastAPI does
    json_data = {"username": "admin", "password": "password123"}
    json_str = json.dumps(json_data)
    parsed_data = json.loads(json_str)
    
    print(f"Original password: {repr(json_data['password'])}")
    print(f"JSON string: {json_str}")
    print(f"Parsed password: {repr(parsed_data['password'])}")
    
    # Test with parsed password
    session_gen = get_async_session()
    session = await session_gen.__anext__()
    service = RBACService(session)
    
    user, token = await service.authenticate_user(
        parsed_data['username'], 
        parsed_data['password']
    )
    print(f"JSON parsed auth result: user={bool(user)}, token={bool(token)}")
    
    await session.close()


async def test_fastapi_simulation():
    """Simulate exactly what FastAPI does"""
    print("\n🏗️  Simulating FastAPI request flow...")
    
    from pydantic import BaseModel
    
    class LoginRequest(BaseModel):
        username: str
        password: str
    
    # Create request object like FastAPI does
    request_data = {"username": "admin", "password": "password123"}
    request_obj = LoginRequest(**request_data)
    
    print(f"Pydantic username: {repr(request_obj.username)}")
    print(f"Pydantic password: {repr(request_obj.password)}")
    
    # Test with pydantic-processed data
    session_gen = get_async_session()
    session = await session_gen.__anext__()
    service = RBACService(session)
    
    user, token = await service.authenticate_user(
        request_obj.username, 
        request_obj.password
    )
    print(f"Pydantic auth result: user={bool(user)}, token={bool(token)}")
    
    await session.close()


async def main():
    """Run all tests"""
    print("🧪 COMPREHENSIVE AUTHENTICATION TESTING")
    print("=" * 50)
    
    await reset_and_test()
    await test_json_parsing()
    await test_fastapi_simulation()
    
    print("\n🎯 Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())