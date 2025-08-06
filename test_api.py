#!/usr/bin/env python3
"""
Test script to verify the API is working correctly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_upload_and_extract():
    """Test document upload and DFD extraction"""
    # 1. Upload a test file
    with open("inputs/sample_architecture.txt", "rb") as f:
        files = {"files": ("sample_architecture.txt", f, "text/plain")}
        response = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
    
    print(f"\n1. Upload response: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return False
    
    upload_result = response.json()
    print(json.dumps(upload_result, indent=2))
    
    pipeline_id = upload_result.get("pipeline_id")
    if not pipeline_id:
        print("Error: No pipeline_id in response")
        return False
    
    print(f"\nPipeline ID: {pipeline_id}")
    
    # 2. Check pipeline status
    response = requests.get(f"{BASE_URL}/api/pipeline/{pipeline_id}/status")
    print(f"\n2. Pipeline status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    # 3. Extract DFD
    extract_request = {"pipeline_id": pipeline_id}
    response = requests.post(
        f"{BASE_URL}/api/documents/extract-dfd",
        json=extract_request
    )
    
    print(f"\n3. DFD extraction response: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return False
    
    dfd_result = response.json()
    print(json.dumps(dfd_result, indent=2))
    
    return True

if __name__ == "__main__":
    print("Testing Threat Modeling Pipeline API")
    print("=" * 50)
    
    if test_health():
        print("\n✅ Health check passed")
    else:
        print("\n❌ Health check failed")
        exit(1)
    
    print("\n" + "=" * 50)
    print("Testing document upload and DFD extraction")
    print("=" * 50)
    
    if test_upload_and_extract():
        print("\n✅ Document upload and DFD extraction passed")
    else:
        print("\n❌ Document upload and DFD extraction failed")
        exit(1)
    
    print("\n✅ All tests passed!")