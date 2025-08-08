#!/usr/bin/env python3
"""
Test script to verify agent discovery endpoints are working properly
and identify any performance issues
"""

import asyncio
import httpx
import subprocess
import time
import os
import signal


class AgentEndpointTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
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
    
    async def test_simple_agents_endpoint(self):
        """Test the simple agents endpoint (should be fast)"""
        print("\n📡 Testing Simple Agents Endpoint (/api/agents/list)")
        
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/agents/list", timeout=10.0)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Simple agents endpoint: {response_time:.3f}s")
                    print(f"   - Agents returned: {data.get('total', 0)}")
                    print(f"   - Categories: {data.get('categories', [])}")
                    print(f"   - Enabled: {data.get('enabled_count', 0)}")
                else:
                    print(f"❌ Simple agents endpoint failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                
            except httpx.TimeoutException:
                response_time = time.time() - start_time
                print(f"⏰ Simple agents endpoint TIMEOUT after {response_time:.1f}s")
            except Exception as e:
                response_time = time.time() - start_time
                print(f"❌ Simple agents endpoint error ({response_time:.3f}s): {e}")
    
    async def test_full_agent_management_endpoints(self):
        """Test the full agent management endpoints (potentially slow)"""
        print("\n🔧 Testing Full Agent Management Endpoints")
        
        # Test the list endpoint that caused the original 50s timeout
        await self._test_endpoint("GET", "/api/agents/list", "Full Agent List", timeout=60.0)
        
        # Test individual agent details
        await self._test_endpoint("GET", "/api/agents/architectural_risk", "Agent Details", timeout=30.0)
        
        # Test agent testing endpoint
        await self._test_endpoint("POST", "/api/agents/architectural_risk/test", "Agent Test", 
                                 timeout=30.0, json={"use_mock_llm": True})
        
        # Test agent performance stats
        await self._test_endpoint("GET", "/api/agents/architectural_risk/performance", "Performance Stats", timeout=30.0)
        
        # Test agent execution history
        await self._test_endpoint("GET", "/api/agents/architectural_risk/history", "Execution History", timeout=30.0)
    
    async def _test_endpoint(self, method: str, path: str, name: str, timeout: float = 10.0, **kwargs):
        """Test a specific endpoint and measure response time"""
        print(f"\n📡 Testing {name} ({method} {path})")
        
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(f"{self.base_url}{path}", timeout=timeout)
                elif method.upper() == "POST":
                    response = await client.post(f"{self.base_url}{path}", timeout=timeout, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    print(f"✅ {name}: {response_time:.3f}s")
                    
                    # Show some response details
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            if 'agents' in data:
                                print(f"   - Agents: {len(data['agents'])}")
                            elif 'status' in data:
                                print(f"   - Status: {data['status']}")
                            elif 'metadata' in data:
                                print(f"   - Agent: {data['metadata']['name']}")
                    except:
                        print(f"   - Response size: {len(response.text)} chars")
                        
                    # Warn if slow
                    if response_time > 5.0:
                        print(f"   ⚠️  SLOW RESPONSE: {response_time:.1f}s > 5s threshold")
                    elif response_time > 1.0:
                        print(f"   ⚠️  Moderate response time: {response_time:.1f}s")
                        
                else:
                    print(f"❌ {name} failed: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                
            except httpx.TimeoutException:
                response_time = time.time() - start_time
                print(f"⏰ {name} TIMEOUT after {response_time:.1f}s")
                print(f"   🚨 THIS COULD BE THE 50s+ TIMEOUT ISSUE!")
            except Exception as e:
                response_time = time.time() - start_time
                print(f"❌ {name} error ({response_time:.3f}s): {e}")
    
    async def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("\n🏥 Testing Health Endpoints")
        
        await self._test_endpoint("GET", "/health", "Health Check", timeout=5.0)
        await self._test_endpoint("GET", "/health/live", "Liveness Check", timeout=5.0)
        await self._test_endpoint("GET", "/health/db", "Database Health", timeout=10.0)
    
    async def run_all_tests(self):
        """Run all agent endpoint tests"""
        print("🧪 Agent Endpoint Performance Testing")
        print("=" * 50)
        
        try:
            await self.start_server()
            
            # Test basic health first
            await self.test_health_endpoints()
            
            # Test simple agents (should be fast)
            await self.test_simple_agents_endpoint()
            
            # Test full agent management (may be slow) 
            await self.test_full_agent_management_endpoints()
            
            print(f"\n✅ Agent endpoint testing completed!")
            
        except Exception as e:
            print(f"\n❌ Testing failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.stop_server()


async def main():
    tester = AgentEndpointTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())