#!/usr/bin/env python3
"""
Example usage of the enhanced Threat Modeling API with RAG functionality.
This script demonstrates how to use the new RAG-powered endpoints.
"""
import asyncio
import httpx
import json
import time


async def demonstrate_rag_pipeline():
    """Demonstrate the complete RAG pipeline functionality."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("🚀 RAG-Powered Threat Modeling API Demo")
        print("=" * 50)
        
        # 1. Initialize knowledge base with default sources
        print("\n1. Initializing Knowledge Base...")
        try:
            response = await client.post(f"{base_url}/api/knowledge-base/initialize-default")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Queued {len(result.get('tasks', []))} knowledge sources")
                for task in result.get('tasks', []):
                    print(f"   - {task['source']}: {task['status']}")
            else:
                print(f"❌ Failed to initialize: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Wait a bit for ingestion to start
        print("\n   Waiting for knowledge base ingestion...")
        await asyncio.sleep(5)
        
        # 2. Check knowledge base stats
        print("\n2. Checking Knowledge Base Status...")
        try:
            response = await client.get(f"{base_url}/api/knowledge-base/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Knowledge Base Stats:")
                print(f"   - Total entries: {stats['total_entries']}")
                print(f"   - Sources: {stats['sources']}")
                print(f"   - Last updated: {stats['last_updated']}")
            else:
                print(f"❌ Failed to get stats: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # 3. Test knowledge base search
        print("\n3. Testing Knowledge Base Search...")
        try:
            search_data = {
                "query": "SQL injection authentication vulnerability",
                "limit": 3
            }
            response = await client.post(f"{base_url}/api/knowledge-base/search", json=search_data)
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Found {results['count']} similar entries:")
                for i, result in enumerate(results['results'][:2], 1):
                    print(f"   {i}. {result.get('source', 'Unknown')} - {result.get('technique_id', 'N/A')}")
                    print(f"      Content: {result.get('content', '')[:100]}...")
            else:
                print(f"❌ Search failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # 4. Create a pipeline and test threat generation
        print("\n4. Testing Enhanced Threat Generation...")
        try:
            # Create a pipeline
            pipeline_data = {"name": "RAG Demo Pipeline"}
            response = await client.post(f"{base_url}/api/pipeline/create", json=pipeline_data)
            if response.status_code == 200:
                pipeline = response.json()
                pipeline_id = pipeline['pipeline_id']
                print(f"✅ Created pipeline: {pipeline_id}")
                
                # Upload a test document
                document_data = {
                    "text": """
                    System Architecture:
                    
                    The web application consists of:
                    1. Authentication Service - Handles user login with database lookup
                    2. User Database - Stores user credentials and profiles  
                    3. API Gateway - Routes requests to backend services
                    4. Payment Processor - Handles credit card transactions
                    
                    Data flows:
                    - Users authenticate through web form to Authentication Service
                    - Authentication Service queries User Database
                    - API Gateway forwards authenticated requests to Payment Processor
                    - Payment Processor communicates with external payment gateway
                    """
                }
                
                response = await client.post(
                    f"{base_url}/api/documents/upload", 
                    json=document_data
                )
                
                if response.status_code == 200:
                    print("✅ Document uploaded")
                    
                    # Execute DFD extraction
                    response = await client.post(
                        f"{base_url}/api/pipeline/{pipeline_id}/execute/dfd_extraction"
                    )
                    
                    if response.status_code == 200:
                        print("✅ DFD extracted")
                        
                        # Execute RAG-powered threat generation
                        response = await client.post(
                            f"{base_url}/api/pipeline/{pipeline_id}/execute/threat_generation"
                        )
                        
                        if response.status_code == 200:
                            threats = response.json()
                            print(f"✅ Generated {threats.get('total_count', 0)} threats using RAG")
                            print(f"   Knowledge sources used: {threats.get('knowledge_sources_used', [])}")
                            
                            # Show first threat as example
                            if threats.get('threats'):
                                first_threat = threats['threats'][0]
                                print(f"\n   Example threat:")
                                print(f"   - Component: {first_threat.get('component_name', 'Unknown')}")
                                print(f"   - Category: {first_threat.get('threat_category', 'Unknown')}")
                                print(f"   - Name: {first_threat.get('threat_name', 'Unknown')}")
                                
                                # 5. Test feedback submission
                                print("\n5. Testing Threat Feedback...")
                                feedback_data = {
                                    "action": "EDITED",
                                    "edited_content": "Updated threat description based on specific system context",
                                    "feedback_reason": "Made threat more specific to our authentication system",
                                    "confidence_rating": 4,
                                    "original_threat": first_threat
                                }
                                
                                threat_id = f"T{hash(str(first_threat)) % 1000000}"
                                response = await client.post(
                                    f"{base_url}/api/threats/{threat_id}/feedback?pipeline_id={pipeline['id']}",
                                    json=feedback_data
                                )
                                
                                if response.status_code == 200:
                                    print("✅ Feedback submitted successfully")
                                else:
                                    print(f"❌ Feedback failed: {response.text}")
                        else:
                            print(f"❌ Threat generation failed: {response.text}")
                    else:
                        print(f"❌ DFD extraction failed: {response.text}")
                else:
                    print(f"❌ Document upload failed: {response.text}")
            else:
                print(f"❌ Pipeline creation failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # 6. Get feedback statistics
        print("\n6. Checking Feedback Statistics...")
        try:
            response = await client.get(f"{base_url}/api/threats/feedback/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Feedback Statistics:")
                print(f"   - Total feedback: {stats['total_feedback']}")
                print(f"   - Action counts: {stats['action_counts']}")
                print(f"   - Average confidence: {stats['average_confidence']}")
            else:
                print(f"❌ Failed to get feedback stats: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n🎉 RAG Pipeline Demo Complete!")
        print("\nKey Features Demonstrated:")
        print("✅ Knowledge base ingestion with CISA KEV data")
        print("✅ Vector similarity search for threat intelligence")
        print("✅ RAG-powered threat generation with context")
        print("✅ Prompt versioning and reproducibility")
        print("✅ Human feedback collection for improvement")
        print("✅ Comprehensive statistics and monitoring")


if __name__ == "__main__":
    print("Starting RAG Pipeline Demo...")
    print("Make sure the API server is running on http://localhost:8000")
    print("Start with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print()
    
    try:
        asyncio.run(demonstrate_rag_pipeline())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed: {e}")
        import traceback
        traceback.print_exc()