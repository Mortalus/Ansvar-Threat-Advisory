#!/usr/bin/env python3
"""
Test script for the enhanced DFD review functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_full_pipeline():
    """Test the complete pipeline flow"""
    print("🧪 Testing Enhanced DFD Review Pipeline")
    print("=" * 50)
    
    # 1. Upload document
    print("1. Uploading test document...")
    with open("inputs/sample_architecture.txt", "rb") as f:
        files = {"files": ("sample_architecture.txt", f, "text/plain")}
        response = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        return False
    
    upload_result = response.json()
    pipeline_id = upload_result.get("pipeline_id")
    print(f"✅ Upload successful. Pipeline ID: {pipeline_id}")
    
    # 2. Extract DFD
    print("\n2. Extracting DFD...")
    extract_request = {"pipeline_id": pipeline_id}
    response = requests.post(
        f"{BASE_URL}/api/documents/extract-dfd",
        json=extract_request
    )
    
    if response.status_code != 200:
        print(f"❌ DFD extraction failed: {response.text}")
        return False
    
    dfd_result = response.json()
    original_dfd = dfd_result["dfd_components"]
    print(f"✅ DFD extraction successful. Components extracted:")
    print(f"   - External Entities: {len(original_dfd['external_entities'])}")
    print(f"   - Processes: {len(original_dfd['processes'])}")
    print(f"   - Assets: {len(original_dfd['assets'])}")
    print(f"   - Data Flows: {len(original_dfd['data_flows'])}")
    
    # 3. Test DFD review with modifications
    print("\n3. Testing DFD review with modifications...")
    
    # Modify the DFD by adding a new external entity
    modified_dfd = original_dfd.copy()
    modified_dfd["external_entities"].append("Security Auditor")
    modified_dfd["processes"].append("Security Monitoring Service")
    
    review_request = {
        "pipeline_id": pipeline_id,
        "dfd_components": modified_dfd
    }
    
    response = requests.post(
        f"{BASE_URL}/api/documents/review-dfd",
        json=review_request
    )
    
    if response.status_code != 200:
        print(f"❌ DFD review failed: {response.text}")
        return False
    
    review_result = response.json()
    reviewed_dfd = review_result["dfd_components"]
    
    print("✅ DFD review successful. Updated components:")
    print(f"   - External Entities: {len(reviewed_dfd['external_entities'])}")
    print(f"   - Processes: {len(reviewed_dfd['processes'])}")
    print(f"   - New External Entity: {reviewed_dfd['external_entities'][-1]}")
    print(f"   - New Process: {reviewed_dfd['processes'][-1]}")
    
    # 4. Verify pipeline status
    print("\n4. Checking pipeline status...")
    response = requests.get(f"{BASE_URL}/api/pipeline/{pipeline_id}/status")
    
    if response.status_code != 200:
        print(f"❌ Status check failed: {response.text}")
        return False
    
    status = response.json()
    print(f"✅ Pipeline status: {status['status']}")
    print(f"   - Current step: {status['current_step']}")
    print(f"   - DFD Review status: {status['steps']['dfd_review']['status']}")
    
    print("\n🎉 All tests passed! Enhanced DFD Review is working correctly.")
    return True

if __name__ == "__main__":
    try:
        test_full_pipeline()
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()