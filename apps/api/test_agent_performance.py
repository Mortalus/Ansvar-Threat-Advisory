#!/usr/bin/env python3
"""
Performance test to identify the bottleneck in agent management endpoints
Based on the documentation mentioning "50s+ timeouts" in agent registry discovery
"""

import asyncio
import time
import sys
import os
sys.path.append(os.path.abspath('.'))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.agents import agent_registry
from app.database import get_async_session
from app.models.agent_config import AgentConfiguration


async def test_agent_endpoint_performance():
    """Simulate the actual agent management endpoint behavior"""
    
    print('🧪 Testing Agent Management Endpoint Performance')
    print('=' * 60)
    
    # Test 1: Agent Registry Discovery (already tested - fast)
    print('\n1. Testing Agent Registry Discovery...')
    agent_registry.clear_registry()
    start_time = time.time()
    discovered_count = agent_registry.discover_agents()
    discovery_time = time.time() - start_time
    print(f'   ✅ Discovered {discovered_count} agents in {discovery_time:.3f}s')
    
    # Test 2: Database Operations (likely bottleneck)
    print('\n2. Testing Database Operations...')
    
    async for db in get_async_session():
        try:
            # Simulate what the /api/agents/list endpoint does
            start_time = time.time()
            
            agents = []
            for agent_name, agent in agent_registry._instances.items():
                # Get metadata (fast)
                metadata = agent.get_metadata()
                
                # Database query for configuration (potentially slow)
                db_query_start = time.time()
                from sqlalchemy import select
                stmt = select(AgentConfiguration).where(
                    AgentConfiguration.agent_name == agent_name
                )
                result = await db.execute(stmt)
                config = result.scalar_one_or_none()
                db_query_time = time.time() - db_query_start
                
                # Build agent info (similar to endpoint logic)
                agent_info = {
                    "name": metadata.name,
                    "version": metadata.version,
                    "description": metadata.description,
                    "category": metadata.category,
                    "enabled": config.enabled if config else metadata.enabled_by_default,
                    "priority": config.priority if config else metadata.priority,
                    "estimated_tokens": metadata.estimated_tokens,
                    "requires_document": metadata.requires_document,
                    "requires_components": metadata.requires_components,
                    "metrics": {
                        "total_executions": config.total_executions if config else 0,
                        "success_rate": round(config.get_success_rate(), 1) if config else 0.0,
                        "avg_threats": round(config.get_average_threats(), 1) if config else 0.0,
                        "avg_execution_time": round(config.average_execution_time, 2) if config else 0.0,
                        "total_tokens_used": config.total_tokens_used if config else 0,
                        "last_executed": config.last_executed.isoformat() if config and config.last_executed else None
                    }
                }
                agents.append(agent_info)
                
                print(f'   - Agent {agent_name}: DB query {db_query_time:.3f}s')
            
            total_time = time.time() - start_time
            print(f'   ✅ Full agent listing simulation: {total_time:.3f}s')
            
            # Test 3: Individual Agent Details (potentially expensive)
            print('\n3. Testing Individual Agent Details (simulates /{agent_name} endpoint)...')
            
            for agent_name in list(agent_registry._instances.keys())[:1]:  # Test just one
                start_time = time.time()
                
                # Get configuration
                stmt = select(AgentConfiguration).where(
                    AgentConfiguration.agent_name == agent_name
                )
                result = await db.execute(stmt)
                config = result.scalar_one_or_none()
                
                # Get prompt versions (potentially slow)
                from app.models.agent_config import AgentPromptVersion
                version_stmt = (
                    select(AgentPromptVersion)
                    .where(AgentPromptVersion.agent_name == agent_name)
                    .order_by(AgentPromptVersion.version.desc())
                    .limit(10)
                )
                version_result = await db.execute(version_stmt)
                versions = version_result.scalars().all()
                
                # Get recent execution logs (potentially very slow)
                from app.models.agent_config import AgentExecutionLog
                log_stmt = (
                    select(AgentExecutionLog)
                    .where(AgentExecutionLog.agent_name == agent_name)
                    .order_by(AgentExecutionLog.executed_at.desc())
                    .limit(20)
                )
                log_result = await db.execute(log_stmt)
                recent_logs = log_result.scalars().all()
                
                agent_details_time = time.time() - start_time
                print(f'   ✅ Agent {agent_name} details: {agent_details_time:.3f}s')
                print(f'      - Prompt versions: {len(versions)}')
                print(f'      - Execution logs: {len(recent_logs)}')
                
                # Test 4: Performance Trend Calculation (potentially very expensive)
                print(f'\n4. Testing Performance Trend Calculation...')
                start_time = time.time()
                
                # Simulate _calculate_performance_trend function
                from datetime import datetime, timedelta
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                trend_stmt = (
                    select(AgentExecutionLog)
                    .where(
                        AgentExecutionLog.agent_name == agent_name,
                        AgentExecutionLog.executed_at >= cutoff_date
                    )
                    .order_by(AgentExecutionLog.executed_at.asc())
                )
                trend_result = await db.execute(trend_stmt)
                trend_logs = trend_result.scalars().all()
                
                trend_time = time.time() - start_time
                print(f'   ✅ Performance trend calculation: {trend_time:.3f}s')
                print(f'      - Trend logs analyzed: {len(trend_logs)}')
            
            break  # Exit the async for loop
            
        except Exception as e:
            print(f'   ❌ Database test failed: {e}')
            import traceback
            traceback.print_exc()
            break


async def test_database_connection_performance():
    """Test if database connection itself is the bottleneck"""
    print('\n🔌 Testing Database Connection Performance')
    print('-' * 40)
    
    connection_times = []
    
    for i in range(5):
        start_time = time.time()
        try:
            async for db in get_async_session():
                connection_time = time.time() - start_time
                connection_times.append(connection_time)
                
                # Simple query
                query_start = time.time()
                result = await db.execute("SELECT 1")
                query_time = time.time() - query_start
                
                print(f'   Connection {i+1}: {connection_time:.3f}s, Query: {query_time:.3f}s')
                break
        except Exception as e:
            print(f'   ❌ Connection {i+1} failed: {e}')
    
    if connection_times:
        avg_connection = sum(connection_times) / len(connection_times)
        print(f'   📊 Average connection time: {avg_connection:.3f}s')
        
        if avg_connection > 1.0:
            print('   ⚠️  SLOW DATABASE CONNECTIONS DETECTED')
        elif avg_connection > 0.5:
            print('   ⚠️  Moderate database connection latency')
        else:
            print('   ✅ Database connections are fast')


async def main():
    print('🔍 Agent Registry Performance Analysis')
    print('=====================================')
    print('Investigating the "50s+ timeout" issue mentioned in documentation\n')
    
    await test_database_connection_performance()
    await test_agent_endpoint_performance()
    
    print('\n📊 Performance Analysis Complete')
    print('================================')
    print('If any operation took >5 seconds, that is likely the bottleneck.')
    print('The documented 50s+ timeout is probably due to:')
    print('1. Database connection issues')  
    print('2. Large execution log queries')
    print('3. Complex performance trend calculations')
    print('4. Missing database indexes')


if __name__ == "__main__":
    asyncio.run(main())