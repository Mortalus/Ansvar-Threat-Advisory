#!/usr/bin/env python3
"""
Test script for RBAC API endpoints
"""

import asyncio
import httpx
import json
import subprocess
import time
import signal
import os


class RBACAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_token = None
        self.server_process = None
    
    async def start_server(self):
        """Start the FastAPI server"""
        print("🚀 Starting API server...")
        
        # Start server in background
        self.server_process = subprocess.Popen([
            "python", "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], cwd=os.getcwd())
        
        # Wait for server to start
        await asyncio.sleep(3)
        print("✅ Server started")
    
    async def stop_server(self):
        """Stop the FastAPI server"""
        if self.server_process:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            self.server_process.wait()
            print("✅ Server stopped")
    
    async def login(self, username="admin", password="admin123!"):
        """Test login endpoint"""
        print(f"\n🔐 Testing login with {username}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/api/v1/auth/login", json={
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.session_token = data["session_token"]
                print(f"✅ Login successful")
                print(f"   User: {data['username']}")
                print(f"   Roles: {data['roles']}")
                print(f"   Permissions: {len(data['permissions'])} permissions")
                return data
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return None
    
    async def test_create_client_user(self):
        """Test client user creation"""
        if not self.session_token:
            print("❌ No session token, skipping client user creation")
            return None
            
        print(f"\n👤 Testing client user creation...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/clients/users",
                headers={"Authorization": f"Bearer {self.session_token}"},
                json={
                    "username": "test_client", 
                    "email": "test@client.com",
                    "password": "client123!",
                    "client_id": "test-corp-001",
                    "client_organization": "Test Corp",
                    "full_name": "Test Client User"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Client user created")
                print(f"   Username: {data['username']}")
                print(f"   Client ID: {data['client_id']}")
                print(f"   Organization: {data['client_organization']}")
                print(f"   External client: {data['is_external_client']}")
                return data
            else:
                print(f"❌ Client user creation failed: {response.status_code} - {response.text}")
                return None
    
    async def test_list_users(self):
        """Test listing users"""
        if not self.session_token:
            print("❌ No session token, skipping user list")
            return None
            
        print(f"\n📋 Testing user list...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/auth/users",
                headers={"Authorization": f"Bearer {self.session_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {len(data)} users")
                for user in data:
                    client_info = f" (Client: {user['client_id']})" if user['client_id'] else ""
                    print(f"   - {user['username']}: {', '.join(user['roles'])}{client_info}")
                return data
            else:
                print(f"❌ User list failed: {response.status_code} - {response.text}")
                return None
    
    async def test_roles_and_permissions(self):
        """Test roles and permissions endpoints"""
        if not self.session_token:
            print("❌ No session token, skipping roles/permissions")
            return None
            
        print(f"\n🔐 Testing roles and permissions...")
        
        async with httpx.AsyncClient() as client:
            # Test roles
            response = await client.get(
                f"{self.base_url}/api/v1/auth/roles",
                headers={"Authorization": f"Bearer {self.session_token}"}
            )
            
            if response.status_code == 200:
                roles = response.json()
                print(f"✅ Retrieved {len(roles)} roles")
                client_role = next((r for r in roles if r['name'] == 'client'), None)
                if client_role:
                    print(f"   ✅ Client role found: {client_role['display_name']}")
                    print(f"      Permissions: {len(client_role['permissions'])}")
                else:
                    print(f"   ❌ Client role not found")
            else:
                print(f"❌ Roles retrieval failed: {response.status_code}")
            
            # Test permissions
            response = await client.get(
                f"{self.base_url}/api/v1/auth/permissions",
                headers={"Authorization": f"Bearer {self.session_token}"}
            )
            
            if response.status_code == 200:
                permissions = response.json()
                print(f"✅ Retrieved {len(permissions)} permissions")
                client_perms = [p for p in permissions if p['resource'] == 'client']
                print(f"   ✅ Found {len(client_perms)} client portal permissions")
                for perm in client_perms:
                    print(f"      - {perm['name']}: {perm['display_name']}")
            else:
                print(f"❌ Permissions retrieval failed: {response.status_code}")
    
    async def test_client_login(self):
        """Test client user login"""
        print(f"\n🔐 Testing client user login...")
        
        # First create a client user if not exists
        await self.test_create_client_user()
        
        # Try to login as client
        client_data = await self.login("test_client", "client123!")
        if client_data:
            print(f"✅ Client login successful")
            print(f"   Has client permissions: {'client:dashboard_view' in client_data.get('permissions', [])}")
        
        # Restore admin session
        await self.login("admin", "admin123!")
    
    async def run_all_tests(self):
        """Run all RBAC tests"""
        print("🧪 RBAC API Testing Suite")
        print("=" * 50)
        
        try:
            await self.start_server()
            
            # Test basic authentication
            await self.login()
            
            # Test user management
            await self.test_create_client_user()
            await self.test_list_users()
            
            # Test roles and permissions
            await self.test_roles_and_permissions()
            
            # Test client authentication
            await self.test_client_login()
            
            print(f"\n✅ RBAC testing completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Testing failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.stop_server()


async def main():
    tester = RBACAPITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())