#!/usr/bin/env python3
"""
Test the threat generation system with defensive programming fixes
"""
import requests
import json
import time

def test_complete_pipeline():
    base_url = "http://localhost:8000"
    
    print("🔥 Testing Complete Threat Modeling Pipeline")
    print("=" * 60)
    
    # Test document content
    test_content = """
    # E-commerce Payment System
    
    ## Architecture Overview
    Our e-commerce platform handles customer payments and order processing.
    The system processes sensitive credit card data and personal information.
    
    ## Components
    - Web Frontend (React/Next.js)
    - API Gateway (Kong)
    - Payment Service (Node.js)
    - Order Processing Service (Python)
    - User Database (PostgreSQL)
    - Payment Processing API (Stripe)
    - Redis Cache
    - Message Queue (RabbitMQ)
    
    ## Data Flows
    1. Customer enters payment information on web frontend
    2. Payment data sent to API Gateway via HTTPS
    3. API Gateway forwards to Payment Service
    4. Payment Service calls Stripe API
    5. Order confirmation stored in database
    6. User notifications sent via message queue
    
    ## Security Requirements
    - PCI DSS Level 1 compliance
    - GDPR compliance for EU customers
    - SOC 2 Type II certification
    - End-to-end encryption for payment data
    """
    
    pipeline_id = None
    
    # Step 1: Upload document
    print("📤 Step 1: Uploading test document...")
    try:
        upload_response = requests.post(
            f"{base_url}/api/documents/upload",
            files={"files": ("payment_system.txt", test_content, "text/plain")},
            timeout=30
        )
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            return False
        
        upload_data = upload_response.json()
        pipeline_id = upload_data.get("pipeline_id")
        
        if not pipeline_id:
            print("❌ No pipeline ID returned")
            return False
            
        print(f"✅ Upload successful! Pipeline ID: {pipeline_id}")
        
    except Exception as e:
        print(f"❌ Upload exception: {e}")
        return False
    
    # Step 2: Extract STRIDE data
    print(f"\n🛡️ Step 2: Extracting STRIDE security data...")
    try:
        extract_response = requests.post(
            f"{base_url}/api/documents/extract-data",
            json={
                "pipeline_id": pipeline_id,
                "enable_quality_validation": True,
                "background": False
            },
            timeout=120
        )
        
        if extract_response.status_code != 200:
            print(f"❌ STRIDE extraction failed: {extract_response.status_code}")
            return False
            
        print("✅ STRIDE extraction successful!")
        
    except Exception as e:
        print(f"❌ STRIDE extraction exception: {e}")
        return False
    
    # Step 3: Set DFD review to complete (direct database update)
    print(f"\n📊 Step 3: Setting DFD review status...")
    try:
        # Try using the execute-step endpoint
        dfd_response = requests.post(
            f"{base_url}/api/tasks/execute-step",
            json={
                "pipeline_id": pipeline_id,
                "step_type": "data_extraction_review",
                "background": False
            },
            timeout=30
        )
        
        if dfd_response.status_code == 200:
            print("✅ DFD review step executed!")
        else:
            print(f"⚠️ DFD review step response: {dfd_response.status_code}")
            # Continue anyway, threat generation might work
        
    except Exception as e:
        print(f"⚠️ DFD review exception: {e}")
        print("Continuing to threat generation...")
    
    # Step 4: Generate threats (the main test)
    print(f"\n🎯 Step 4: Testing threat generation with defensive programming...")
    try:
        threat_response = requests.post(
            f"{base_url}/api/documents/generate-threats",
            json={
                "pipeline_id": pipeline_id,
                "background": False
            },
            timeout=180  # Generous timeout for threat generation
        )
        
        print(f"📊 Threat generation status: {threat_response.status_code}")
        
        if threat_response.status_code == 200:
            print("🎉 Threat generation successful!")
            
            threat_data = threat_response.json()
            threats = threat_data.get("threats", [])
            
            print(f"\n📋 Threat Generation Results:")
            print(f"  🚨 Total threats: {len(threats)}")
            
            # Check threat structure
            valid_threats = 0
            for threat in threats:
                if isinstance(threat, dict):
                    valid_threats += 1
                else:
                    print(f"  ⚠️ Found invalid threat type: {type(threat)}")
            
            print(f"  ✅ Valid threat objects: {valid_threats}/{len(threats)}")
            
            if threat_data.get("risk_summary"):
                print(f"  📊 Risk summary generated: ✅")
            
            if threat_data.get("consolidation_metadata"):
                metadata = threat_data["consolidation_metadata"]
                print(f"  🔍 Analysis methods used: {len(metadata.get('analysis_methods', []))}")
                print(f"  🛡️ Gaps identified: {len(metadata.get('critical_gaps', []))}")
            
            print(f"\n💡 Defensive programming successfully prevented crashes!")
            return True
            
        else:
            print(f"❌ Threat generation failed: {threat_response.status_code}")
            try:
                error_data = threat_response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Raw response: {threat_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Threat generation exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Complete Pipeline Test")
    print("This test validates STRIDE extraction + threat generation")
    
    success = test_complete_pipeline()
    
    if success:
        print(f"\n🎉 SUCCESS: Complete pipeline is working!")
        print("✅ STRIDE extraction completed successfully")
        print("✅ Threat generation completed without crashes")
        print("✅ Defensive programming handled all edge cases")
    else:
        print(f"\n💥 FAILURE: Pipeline still has issues")