#!/usr/bin/env python3
"""
Test script specifically for threat generation functionality.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import AsyncSessionLocal
from app.services.ingestion_service import IngestionService
from app.services.prompt_service import PromptService
from app.core.pipeline.manager import PipelineManager, PipelineStep
from app.models.pipeline import PipelineStepResult
from app.startup import initialize_default_data

async def test_threat_generation():
    """Test the complete threat generation pipeline."""
    print("🧪 Testing Threat Generation with RAG")
    print("=" * 50)
    
    # Initialize default prompts
    await initialize_default_data()
    print("✅ Default prompts initialized")
    
    # Create some test knowledge base entries
    print("\n📚 Setting up test knowledge base...")
    
    test_data = {
        "vulnerabilities": [
            {
                "cveID": "CVE-2024-TEST1",
                "vendorProject": "TestCorp",
                "product": "AuthService",
                "vulnerabilityName": "SQL Injection in Authentication",
                "dateAdded": "2024-01-01",
                "shortDescription": "SQL injection vulnerability allows attackers to bypass authentication by manipulating login queries",
                "requiredAction": "Implement parameterized queries",
                "dueDate": "2024-12-31"
            },
            {
                "cveID": "CVE-2024-TEST2", 
                "vendorProject": "SecurePay",
                "product": "PaymentGateway",
                "vulnerabilityName": "Buffer Overflow in Payment Processing",
                "dateAdded": "2024-02-01",
                "shortDescription": "Buffer overflow in payment processing allows remote code execution",
                "requiredAction": "Apply security patch",
                "dueDate": "2024-12-31"
            }
        ]
    }
    
    # Process and store test data
    ingestion_service = IngestionService()
    entries = await ingestion_service._process_cisa_kev(test_data, "TEST_THREATS")
    
    async with AsyncSessionLocal() as session:
        for entry in entries:
            session.add(entry)
        await session.commit()
    
    print(f"✅ Added {len(entries)} test threat intelligence entries")
    
    # Test component data (simulating DFD output)
    component_data = {
        "processes": [
            {
                "id": "proc_1",
                "name": "Authentication Service",
                "type": "process", 
                "description": "Handles user login with database queries for credential verification"
            },
            {
                "id": "proc_2",
                "name": "Payment Processor",
                "type": "process",
                "description": "Processes credit card transactions and handles payment data"
            }
        ],
        "data_stores": [
            {
                "id": "db_1",
                "name": "User Database", 
                "type": "data_store",
                "description": "Stores user credentials, profiles, and authentication data"
            }
        ]
    }
    
    print(f"\n🎯 Testing threat generation using PIPELINE MANAGER (with hardcoded V3)...")
    
    try:
        # Create pipeline manager
        pipeline_manager = PipelineManager()
        
        # Create a new pipeline
        pipeline_id = await pipeline_manager.create_pipeline(
            name="Test Threat Generation",
            description="Testing V3 threat generation through pipeline manager"
        )
        print(f"✅ Created pipeline: {pipeline_id}")
        
        # Upload document step (required)
        upload_result = await pipeline_manager.execute_step(
            pipeline_id=pipeline_id,
            step=PipelineStep.DOCUMENT_UPLOAD,
            data={"document_text": "Test document for threat analysis"}
        )
        print("✅ Document upload completed")
        
        # DFD extraction step (required) 
        dfd_result = await pipeline_manager.execute_step(
            pipeline_id=pipeline_id,
            step=PipelineStep.DFD_EXTRACTION,
            data={
                "document_text": "Test document for DFD extraction",
                "use_enhanced_extraction": False  # Use basic for testing
            }
        )
        print("✅ DFD extraction completed")
        
        # DFD review step (required before threat generation)
        review_result = await pipeline_manager.execute_step(
            pipeline_id=pipeline_id,
            step=PipelineStep.DFD_REVIEW,
            data={"dfd_components": component_data}
        )
        print("✅ DFD review completed")
        
        # NOW test threat generation through pipeline manager (will use hardcoded V3)
        print(f"\n🚀 Executing V3 threat generation through pipeline manager...")
        
        result = await pipeline_manager.execute_step(
            pipeline_id=pipeline_id,
            step=PipelineStep.THREAT_GENERATION,
            data={}  # Empty data - V3 is hardcoded
        )
        
        print(f"✅ V3 Threat generation completed successfully!")
        print(f"   📊 Total threats: {result.get('total_count', 0)}")
        print(f"   🔍 Components analyzed: {result.get('components_analyzed', 0)}")
        print(f"   📚 Knowledge sources: {result.get('knowledge_sources_used', [])}")
        
        # Show example threats
        threats = result.get("threats", [])
        if threats:
            print(f"\n🔥 Example V3 threats generated:")
            for i, threat in enumerate(threats[:3], 1):  # Show first 3
                print(f"   {i}. Component: {threat.get('component_name', 'Unknown')}")
                print(f"      Category: {threat.get('Threat Category', 'Unknown')}")
                print(f"      Name: {threat.get('Threat Name', 'Unknown')}")
                print(f"      Description: {threat.get('Description', 'No description')[:100]}...")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline-based threat generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_knowledge_search():
    """Test the knowledge base search functionality."""
    print("\n🔍 Testing Knowledge Base Search...")
    
    ingestion_service = IngestionService()
    
    # Test searches
    test_queries = [
        "SQL injection authentication",
        "buffer overflow payment processing", 
        "authentication vulnerability database"
    ]
    
    for query in test_queries:
        results = await ingestion_service.search_similar(query, limit=2)
        print(f"   Query: '{query}' -> {len(results)} results")
        for result in results:
            print(f"     - {result.get('technique_id', 'Unknown')}: {result.get('content', '')[:50]}...")


if __name__ == "__main__":
    async def main():
        try:
            await test_knowledge_search()
            success = await test_threat_generation()
            
            if success:
                print("\n🎉 Threat Generation Test PASSED!")
                print("✅ RAG-powered threat modeling is working correctly")
                return True
            else:
                print("\n❌ Threat Generation Test FAILED!")
                return False
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)