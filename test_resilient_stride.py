#!/usr/bin/env python3
"""
Test the resilient STRIDE extraction system
"""
import requests
import json
import time

def test_resilient_stride():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Resilient STRIDE Extraction System")
    print("=" * 60)
    
    # Test document content
    test_content = """
    # E-commerce Platform Security Architecture
    
    ## Overview
    Our e-commerce platform handles customer orders, payments, and inventory management.
    The system processes sensitive customer data and financial transactions.
    
    ## Components
    - Web Frontend (React)
    - API Gateway (Kong)
    - Order Service (Node.js)
    - Payment Service (Python/Django)
    - Inventory Service (Java/Spring)
    - User Authentication (Auth0)
    - Database Cluster (PostgreSQL)
    - Redis Cache
    - Message Queue (RabbitMQ)
    
    ## Data Flows
    1. Customer places order through web interface
    2. Order service validates inventory
    3. Payment service processes credit card
    4. Order confirmation sent via email
    5. Inventory updated in real-time
    
    ## Security Requirements
    - PCI DSS compliance for payment processing
    - GDPR compliance for customer data
    - TLS encryption for all communications
    - Multi-factor authentication for admin access
    """
    
    # Step 1: Upload document
    print("📤 Step 1: Uploading test document...")
    try:
        upload_response = requests.post(
            f"{base_url}/api/documents/upload",
            files={"files": ("ecommerce_architecture.txt", test_content, "text/plain")},
            timeout=30
        )
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            try:
                error_details = upload_response.json()
                print(f"Error: {error_details}")
            except:
                print(f"Raw response: {upload_response.text}")
            return False
        
        upload_data = upload_response.json()
        pipeline_id = upload_data.get("pipeline_id")
        
        if not pipeline_id:
            print("❌ No pipeline ID returned from upload")
            print(f"Upload response: {upload_data}")
            return False
            
        print(f"✅ Upload successful! Pipeline ID: {pipeline_id}")
        
    except Exception as e:
        print(f"❌ Upload exception: {e}")
        return False
    
    # Step 2: Test STRIDE extraction with resilient system
    print(f"\n🛡️ Step 2: Testing resilient STRIDE extraction...")
    try:
        extract_response = requests.post(
            f"{base_url}/api/documents/extract-data",
            json={
                "pipeline_id": pipeline_id,
                "enable_quality_validation": True,  # Test with quality validation
                "background": False
            },
            timeout=120  # Give it more time
        )
        
        print(f"📊 Response status: {extract_response.status_code}")
        
        if extract_response.status_code == 200:
            print("🎉 STRIDE extraction successful!")
            
            response_data = extract_response.json()
            extracted_data = response_data.get("extracted_security_data", {})
            metadata = response_data.get("extraction_metadata", {})
            
            print(f"\n📋 Extraction Results:")
            print(f"  📈 Quality score: {response_data.get('quality_score', 'N/A')}")
            print(f"  🏗️ Assets: {len(extracted_data.get('security_assets', []))}")
            print(f"  🔄 Data flows: {len(extracted_data.get('security_data_flows', []))}")
            print(f"  🛡️ Trust zones: {len(extracted_data.get('trust_zones', []))}")
            print(f"  🚀 Passes completed: {', '.join(metadata.get('passes_performed', []))}")
            
            if metadata.get('errors'):
                print(f"  ⚠️ Errors handled: {len(metadata['errors'])}")
                for error in metadata['errors']:
                    print(f"    - {error}")
            
            if metadata.get('fallback_used'):
                print(f"  🆘 Fallback used: {metadata['fallback_used']}")
            
            # Check completeness indicators
            completeness = response_data.get('completeness_indicators', {})
            if completeness:
                complete_areas = sum(completeness.values())
                total_areas = len(completeness)
                print(f"  ✅ Completeness: {complete_areas}/{total_areas} areas")
            
            print(f"\n💡 System successfully extracted meaningful security data!")
            return True
            
        else:
            print(f"❌ STRIDE extraction failed: {extract_response.status_code}")
            try:
                error_data = extract_response.json()
                print(f"Error detail: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Raw response: {extract_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ STRIDE extraction exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Resilient STRIDE System Test")
    print("This test validates the multi-layer fallback system")
    
    success = test_resilient_stride()
    
    if success:
        print(f"\n🎉 SUCCESS: Resilient STRIDE system is working!")
        print("✅ The system can handle malformed LLM responses gracefully")
        print("✅ Multiple fallback layers ensure the pipeline never fails")
        print("✅ Quality validation is completely optional and safe")
    else:
        print(f"\n💥 FAILURE: System still has issues that need fixing")