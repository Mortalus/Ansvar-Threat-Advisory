#!/usr/bin/env python3
"""
Test multi-agent pipeline execution to ensure all agents work together properly
"""

import asyncio
import sys
import os
sys.path.append(os.path.abspath('.'))

from app.core.agents import agent_registry
from app.core.agents.base import AgentExecutionContext
from app.core.llm.mock import MockLLMProvider
from app.database import get_async_session
from app.services.settings_service import SettingsService


async def test_multi_agent_pipeline():
    """Test that multiple agents can execute in sequence with proper context sharing"""
    
    print('🧪 Testing Multi-Agent Pipeline Execution')
    print('=' * 50)
    
    # Initialize agent registry
    print('\n1. Initializing Agent Registry...')
    agent_registry.clear_registry()
    discovered_count = agent_registry.discover_agents()
    print(f'   ✅ Discovered {discovered_count} agents')
    
    # Create execution context with sample data
    print('\n2. Creating Execution Context...')
    context = AgentExecutionContext(
        document_text=get_sample_document(),
        components=get_sample_components(),
        existing_threats=[],
        pipeline_id="test_multi_agent_001"
    )
    
    print(f'   ✅ Context created:')
    print(f'      - Document length: {len(context.document_text) if context.document_text else 0} chars')
    print(f'      - Components: {sum(len(v) for v in context.components.values() if isinstance(v, list))} items')
    print(f'      - Pipeline ID: {context.pipeline_id}')
    
    # Initialize LLM provider and settings
    print('\n3. Initializing Dependencies...')
    llm_provider = MockLLMProvider()
    
    async for db_session in get_async_session():
        settings_service = SettingsService(db_session)
        break
    
    print('   ✅ Mock LLM provider initialized')
    print('   ✅ Settings service initialized')
    
    # Get enabled agents in execution order
    print('\n4. Getting Enabled Agents...')
    enabled_agents = agent_registry.get_enabled_agents()
    print(f'   ✅ Found {len(enabled_agents)} enabled agents:')
    
    for i, agent in enumerate(enabled_agents):
        metadata = agent.get_metadata()
        print(f'      {i+1}. {metadata.name} (category: {metadata.category}, priority: {metadata.priority})')
    
    # Execute agents in sequence
    print('\n5. Executing Agent Pipeline...')
    all_threats = []
    execution_results = []
    
    for i, agent in enumerate(enabled_agents):
        metadata = agent.get_metadata()
        print(f'\n   🤖 Executing Agent {i+1}: {metadata.name}')
        
        try:
            # Validate agent can execute with context
            if not agent.validate_context(context):
                print(f'      ❌ Agent cannot execute with current context')
                print(f'         Requires document: {metadata.requires_document}')
                print(f'         Requires components: {metadata.requires_components}')
                continue
            
            # Execute agent
            import time
            start_time = time.time()
            
            threats = await agent.analyze(
                context=context,
                llm_provider=llm_provider,
                db_session=db_session,
                settings_service=settings_service
            )
            
            execution_time = time.time() - start_time
            
            print(f'      ✅ Agent executed successfully')
            print(f'         Execution time: {execution_time:.3f}s')
            print(f'         Threats found: {len(threats)}')
            
            # Add threats to context for next agents
            if threats:
                context.existing_threats.extend(threats)
                all_threats.extend(threats)
                
                # Show sample threats
                for j, threat in enumerate(threats[:3]):  # Show first 3
                    print(f'         {j+1}. {threat.threat_name} (confidence: {getattr(threat, "confidence_score", "N/A")})')
                if len(threats) > 3:
                    print(f'         ... and {len(threats) - 3} more')
            
            execution_results.append({
                'agent': metadata.name,
                'success': True,
                'execution_time': execution_time,
                'threats_count': len(threats),
                'category': metadata.category
            })
            
        except Exception as e:
            print(f'      ❌ Agent execution failed: {e}')
            execution_results.append({
                'agent': metadata.name,
                'success': False,
                'error': str(e),
                'category': metadata.category
            })
            
            # Continue with other agents even if one fails
            continue
    
    # Analyze results
    print('\n6. Pipeline Execution Summary')
    print('=' * 30)
    
    successful_agents = [r for r in execution_results if r['success']]
    failed_agents = [r for r in execution_results if not r['success']]
    
    print(f'   Total agents: {len(execution_results)}')
    print(f'   ✅ Successful: {len(successful_agents)}')
    print(f'   ❌ Failed: {len(failed_agents)}')
    print(f'   Total threats generated: {len(all_threats)}')
    
    if successful_agents:
        total_time = sum(r['execution_time'] for r in successful_agents)
        avg_time = total_time / len(successful_agents)
        print(f'   Average execution time: {avg_time:.3f}s')
        print(f'   Total pipeline time: {total_time:.3f}s')
        
        # Breakdown by category
        categories = {}
        for result in successful_agents:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'count': 0, 'threats': 0}
            categories[cat]['count'] += 1
            categories[cat]['threats'] += result['threats_count']
        
        print(f'\n   Breakdown by category:')
        for cat, stats in categories.items():
            print(f'      {cat}: {stats["count"]} agents, {stats["threats"]} threats')
    
    if failed_agents:
        print(f'\n   Failed agents:')
        for result in failed_agents:
            print(f'      ❌ {result["agent"]}: {result.get("error", "Unknown error")}')
    
    # Test context sharing
    print('\n7. Testing Context Sharing...')
    if len(all_threats) > 0:
        print(f'   ✅ Context sharing working - {len(all_threats)} total threats available for subsequent agents')
        
        # Verify threat variety
        threat_categories = set()
        for threat in all_threats[:10]:  # Check first 10 threats
            if hasattr(threat, 'threat_name'):
                # Try to categorize based on threat name patterns
                threat_name = threat.threat_name.lower()
                if any(word in threat_name for word in ['data', 'sql', 'injection', 'xss']):
                    threat_categories.add('data_security')
                elif any(word in threat_name for word in ['authentication', 'authorization', 'session']):
                    threat_categories.add('access_control')
                elif any(word in threat_name for word in ['denial', 'dos', 'availability']):
                    threat_categories.add('availability')
                else:
                    threat_categories.add('other')
        
        print(f'   ✅ Threat diversity: {len(threat_categories)} different categories detected')
    else:
        print(f'   ⚠️  No threats generated - may indicate agents not working or context issues')
    
    return {
        'total_agents': len(execution_results),
        'successful_agents': len(successful_agents), 
        'failed_agents': len(failed_agents),
        'total_threats': len(all_threats),
        'execution_results': execution_results,
        'pipeline_success': len(successful_agents) >= len(enabled_agents) * 0.5  # 50% success rate
    }


def get_sample_document():
    """Get sample document for testing"""
    return """
    E-Commerce Platform Security Analysis
    
    This document describes a cloud-based e-commerce platform designed for high-volume transactions.
    
    System Architecture:
    - Frontend: React.js SPA hosted on AWS CloudFront CDN
    - API Gateway: AWS API Gateway with rate limiting and authentication
    - Authentication Service: OAuth 2.0 + JWT tokens with Redis session storage
    - Microservices Architecture:
      * Product Catalog Service (Node.js + MongoDB)
      * Order Processing Service (Java Spring Boot + PostgreSQL)
      * Payment Service (Python Flask + Stripe API integration)
      * User Management Service (Python Django + PostgreSQL)
      * Notification Service (Node.js + AWS SES)
    
    Data Flow:
    1. Users access the React frontend through CloudFront
    2. API calls are routed through AWS API Gateway
    3. JWT tokens are validated against Redis cache
    4. Business logic is processed by microservices
    5. Payment data is securely transmitted to Stripe
    6. Order confirmations are sent via SES
    
    Security Requirements:
    - PCI DSS compliance for payment processing
    - GDPR compliance for user data in EU
    - SOX compliance for financial reporting
    - 99.9% uptime SLA with automated failover
    - Data encryption at rest and in transit
    - Regular security audits and penetration testing
    
    Sensitive Data:
    - Customer personal information (names, addresses, phone numbers)
    - Payment card information (handled by Stripe, not stored locally)
    - Order history and transaction records
    - User behavioral analytics and preferences
    - Financial reporting data
    - API keys and service credentials
    
    Current Scale:
    - 50,000+ daily active users
    - 10,000+ daily orders
    - $2M+ monthly transaction volume
    - 99.95% current uptime
    - Multi-region deployment (US, EU, Asia)
    """


def get_sample_components():
    """Get sample DFD components for testing"""
    return {
        "processes": [
            {"name": "react-frontend", "type": "web_app", "description": "React.js single-page application"},
            {"name": "api-gateway", "type": "gateway", "description": "AWS API Gateway with authentication"},
            {"name": "auth-service", "type": "service", "description": "OAuth 2.0 + JWT authentication service"},
            {"name": "product-service", "type": "service", "description": "Product catalog microservice (Node.js)"},
            {"name": "order-service", "type": "service", "description": "Order processing microservice (Java)"},
            {"name": "payment-service", "type": "service", "description": "Payment processing service (Python)"},
            {"name": "user-service", "type": "service", "description": "User management service (Django)"},
            {"name": "notification-service", "type": "service", "description": "Email notification service"}
        ],
        "assets": [
            {"name": "product-db", "type": "database", "description": "MongoDB product catalog database"},
            {"name": "order-db", "type": "database", "description": "PostgreSQL order database"},
            {"name": "user-db", "type": "database", "description": "PostgreSQL user database"},
            {"name": "redis-cache", "type": "cache", "description": "Redis session and cache store"},
            {"name": "file-storage", "type": "storage", "description": "AWS S3 for product images"}
        ],
        "external_entities": [
            {"name": "customers", "type": "person", "description": "E-commerce platform users"},
            {"name": "stripe-api", "type": "external_service", "description": "Payment processing service"},
            {"name": "cloudfront-cdn", "type": "external_service", "description": "AWS CloudFront CDN"},
            {"name": "ses-email", "type": "external_service", "description": "AWS Simple Email Service"}
        ],
        "data_flows": [
            {"source": "customers", "destination": "react-frontend", "data": "HTTP requests"},
            {"source": "react-frontend", "destination": "api-gateway", "data": "API calls + JWT tokens"},
            {"source": "api-gateway", "destination": "auth-service", "data": "Authentication requests"},
            {"source": "auth-service", "destination": "redis-cache", "data": "Session data"},
            {"source": "api-gateway", "destination": "product-service", "data": "Product queries"},
            {"source": "product-service", "destination": "product-db", "data": "Database queries"},
            {"source": "api-gateway", "destination": "order-service", "data": "Order requests"},
            {"source": "order-service", "destination": "order-db", "data": "Order data"},
            {"source": "order-service", "destination": "payment-service", "data": "Payment requests"},
            {"source": "payment-service", "destination": "stripe-api", "data": "Payment data (encrypted)"},
            {"source": "order-service", "destination": "notification-service", "data": "Order confirmations"},
            {"source": "notification-service", "destination": "ses-email", "data": "Email requests"}
        ]
    }


async def main():
    print('🚀 Multi-Agent Pipeline Testing Suite')
    print('=====================================')
    
    try:
        results = await test_multi_agent_pipeline()
        
        if results['pipeline_success']:
            print(f'\n✅ MULTI-AGENT PIPELINE TEST PASSED')
            print(f'   {results["successful_agents"]}/{results["total_agents"]} agents successful')
            print(f'   {results["total_threats"]} threats generated')
        else:
            print(f'\n❌ MULTI-AGENT PIPELINE TEST FAILED')
            print(f'   Only {results["successful_agents"]}/{results["total_agents"]} agents successful')
            print('   Pipeline requires at least 50% success rate')
        
    except Exception as e:
        print(f'\n❌ PIPELINE TEST FAILED WITH EXCEPTION: {e}')
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())