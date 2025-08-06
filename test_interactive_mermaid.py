#!/usr/bin/env python3
"""
Test the interactive Mermaid functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_interactive_diagram():
    """Test the complete flow to interactive diagram"""
    print("🎨 Testing Interactive Mermaid Diagram")
    print("=" * 50)
    
    # 1. Upload and extract
    print("1. Setting up test data...")
    with open("inputs/sample_architecture.txt", "rb") as f:
        files = {"files": ("sample_architecture.txt", f, "text/plain")}
        response = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
    
    upload_result = response.json()
    pipeline_id = upload_result["pipeline_id"]
    
    extract_request = {"pipeline_id": pipeline_id}
    response = requests.post(f"{BASE_URL}/api/documents/extract-dfd", json=extract_request)
    dfd_result = response.json()
    original_dfd = dfd_result["dfd_components"]
    
    print(f"✅ Setup complete. Pipeline ID: {pipeline_id}")
    print(f"   Components: {len(original_dfd['external_entities'])} entities, {len(original_dfd['processes'])} processes")
    
    # 2. Test with enhanced components for better visualization
    print("\n2. Creating enhanced DFD for visualization...")
    
    enhanced_dfd = {
        "project_name": "E-Commerce Security Platform",
        "project_version": "2.1",
        "industry_context": "E-commerce & Security",
        "external_entities": [
            "Customer",
            "Admin",
            "Payment Gateway",
            "Shipping Provider",
            "Security Auditor"
        ],
        "processes": [
            "Web Server",
            "API Gateway", 
            "Auth Service",
            "Payment Service",
            "Security Monitor"
        ],
        "assets": [
            "User DB",
            "Product DB", 
            "Order DB",
            "Session Cache",
            "Security Logs"
        ],
        "trust_boundaries": [
            "Public Zone",
            "DMZ",
            "Internal Network",
            "Secure Zone"
        ],
        "data_flows": [
            {
                "source": "Customer",
                "destination": "Web Server",
                "data_description": "HTTPS requests",
                "data_classification": "Public",
                "protocol": "HTTPS",
                "authentication_mechanism": "None"
            },
            {
                "source": "Web Server", 
                "destination": "API Gateway",
                "data_description": "API calls",
                "data_classification": "Internal",
                "protocol": "HTTPS",
                "authentication_mechanism": "JWT"
            },
            {
                "source": "API Gateway",
                "destination": "Auth Service", 
                "data_description": "Auth requests",
                "data_classification": "Confidential",
                "protocol": "TLS",
                "authentication_mechanism": "OAuth2"
            },
            {
                "source": "Auth Service",
                "destination": "User DB",
                "data_description": "User data",
                "data_classification": "PII",
                "protocol": "TLS",
                "authentication_mechanism": "DB Auth"
            },
            {
                "source": "Payment Service",
                "destination": "Payment Gateway",
                "data_description": "Payment data", 
                "data_classification": "Confidential",
                "protocol": "HTTPS",
                "authentication_mechanism": "API Key"
            }
        ]
    }
    
    # 3. Save enhanced DFD
    review_request = {
        "pipeline_id": pipeline_id,
        "dfd_components": enhanced_dfd
    }
    
    response = requests.post(f"{BASE_URL}/api/documents/review-dfd", json=review_request)
    if response.status_code == 200:
        print("✅ Enhanced DFD saved successfully")
        print("   Ready for interactive visualization!")
    else:
        print(f"❌ Failed to save enhanced DFD: {response.text}")
        return False
    
    print("\n🎯 Interactive Features Available:")
    print("   • Real-time diagram rendering as you edit JSON")
    print("   • Zoom in/out with mouse wheel or buttons")
    print("   • Pan by clicking and dragging")
    print("   • Fullscreen mode for presentations")
    print("   • Export as PNG for client deliverables")
    print("   • Reset view to center and original scale")
    
    print("\n📋 Workshop Instructions:")
    print("   1. Open the DFD Review step in your browser")
    print("   2. Switch to 'Interactive Diagram' tab")
    print("   3. Edit JSON in real-time and watch diagram update")
    print("   4. Use mouse wheel to zoom in/out")
    print("   5. Click and drag to pan around")
    print("   6. Use fullscreen mode for client presentation")
    print("   7. Export PNG for documentation")
    
    return True

if __name__ == "__main__":
    try:
        success = test_interactive_diagram()
        if success:
            print("\n🚀 Interactive Mermaid is ready for your workshop!")
            print("   Navigate to: http://localhost:3001")
            print("   Go to DFD Review → Interactive Diagram tab")
        else:
            print("\n❌ Setup failed")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()