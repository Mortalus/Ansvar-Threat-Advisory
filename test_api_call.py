#!/usr/bin/env python3
"""
Test the actual API call to see the fix in action
"""
import requests
import json
import time

def test_stride_extraction():
    base_url = "http://localhost:8000"
    
    # First upload a document
    print("🚀 Testing STRIDE data extraction API...")
    
    # Create a test document
    test_content = """
    # Banking Application Architecture
    
    ## Overview
    This is a web-based banking application that allows customers to view account balances, 
    transfer money, and manage their profiles.
    
    ## Components
    - Web Frontend (React)
    - API Gateway 
    - User Service
    - Account Service
    - Transaction Service
    - Database (PostgreSQL)
    - Redis Cache
    
    ## Data Flows
    1. User authenticates through API Gateway
    2. Frontend calls Account Service for balance
    3. Transaction Service processes transfers
    4. All data stored in PostgreSQL database
    """
    
    # Step 1: Upload document
    print("📤 Step 1: Uploading document...")
    upload_response = requests.post(
        f"{base_url}/api/documents/upload",
        files={"files": ("test_doc.txt", test_content, "text/plain")}
    )
    
    if upload_response.status_code != 200:
        print(f"❌ Upload failed: {upload_response.status_code}")
        print(upload_response.text)
        return False
    
    upload_data = upload_response.json()
    print(f"📄 Upload response: {upload_data}")
    
    # Extract pipeline ID from different possible locations
    pipeline_id = upload_data.get("pipeline_id") or upload_data.get("id")
    if not pipeline_id and "pipeline_status" in upload_data:
        # Try to find pipeline_id in nested structure
        for key, value in upload_data.items():
            if isinstance(value, str) and len(value) == 36 and value.count('-') == 4:
                pipeline_id = value
                break
    
    print(f"✅ Upload successful! Pipeline ID: {pipeline_id}")
    
    # Step 2: Extract STRIDE data  
    print("🛡️ Step 2: Extracting STRIDE data...")
    extract_response = requests.post(
        f"{base_url}/api/documents/extract-data",
        json={
            "pipeline_id": pipeline_id,
            "enable_quality_validation": True,
            "background": False
        }
    )
    
    print(f"📊 Response status: {extract_response.status_code}")
    
    if extract_response.status_code == 200:
        print("✅ STRIDE extraction successful!")
        response_data = extract_response.json()
        print(f"📈 Quality score: {response_data.get('quality_score', 'N/A')}")
        print(f"📋 Assets extracted: {len(response_data.get('extracted_security_data', {}).get('security_assets', []))}")
        return True
    else:
        print(f"❌ STRIDE extraction failed: {extract_response.status_code}")
        try:
            error_data = extract_response.json()
            print(f"Error detail: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"Raw response: {extract_response.text}")
        return False

if __name__ == "__main__":
    success = test_stride_extraction()
    if success:
        print("\n🎉 API test successful!")
    else:
        print("\n💥 API test failed - check logs for details")