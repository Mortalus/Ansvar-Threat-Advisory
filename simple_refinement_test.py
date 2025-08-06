#!/usr/bin/env python3
"""
Simple test to verify threat refinement endpoint works.
"""
import requests
import time

API_BASE = "http://localhost:8000"

def quick_test():
    """Quick test of basic functionality."""
    
    print("🔧 Quick Threat Refinement Test")
    print("=" * 35)
    
    try:
        # Simple document
        test_document = """
        Simple System:
        - Web Server: Serves web pages
        - Database: Stores user data
        """
        
        # Upload and process through pipeline quickly
        files = {'files': ('simple.txt', test_document, 'text/plain')}
        response = requests.post(f"{API_BASE}/api/documents/upload", files=files)
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            return False
            
        pipeline_id = response.json()["pipeline_id"]
        print(f"✓ Uploaded: {pipeline_id}")
        
        # Extract DFD
        response = requests.post(f"{API_BASE}/api/documents/extract-dfd", 
                               json={"pipeline_id": pipeline_id})
        if response.status_code != 200:
            print(f"❌ DFD extraction failed: {response.status_code}")
            return False
        print("✓ DFD extracted")
        
        # Review DFD
        dfd_data = response.json()
        response = requests.post(f"{API_BASE}/api/documents/review-dfd",
                               json={
                                   "pipeline_id": pipeline_id,
                                   "dfd_components": dfd_data['dfd_components']
                               })
        if response.status_code != 200:
            print(f"❌ DFD review failed: {response.status_code}")
            return False
        print("✓ DFD reviewed")
        
        # Generate threats 
        response = requests.post(f"{API_BASE}/api/documents/generate-threats",
                               json={"pipeline_id": pipeline_id})
        if response.status_code != 200:
            print(f"❌ Threat generation failed: {response.status_code} - {response.text}")
            return False
        
        threat_data = response.json()
        print(f"✓ Generated {len(threat_data.get('threats', []))} threats")
        
        # Test refinement endpoint
        print("🧠 Testing refinement...")
        response = requests.post(f"{API_BASE}/api/documents/refine-threats",
                               json={"pipeline_id": pipeline_id})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Refinement successful!")
            print(f"   - Refined threats: {len(result.get('refined_threats', []))}")
            print(f"   - Original count: {result.get('refinement_stats', {}).get('original_count', 0)}")
            return True
        else:
            print(f"❌ Refinement failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    time.sleep(2)
    success = quick_test()
    print(f"\n{'✅ Success!' if success else '❌ Failed'}")
    exit(0 if success else 1)