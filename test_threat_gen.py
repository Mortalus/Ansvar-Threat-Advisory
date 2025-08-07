#!/usr/bin/env python3
"""
Quick test to verify the threat generation fixes work
"""
import sys
import os
sys.path.append('/Users/jeffreyvonrotz/SynologyDrive/Projects/ThreatModelingPipeline/apps/api')

from app.core.pipeline.steps.threat_generator_v3 import ThreatGeneratorV3

# Test data
test_component_data = {
    'processes': ['Web Server', 'API Gateway'],
    'assets': ['User Database', 'Session Store'],
    'external_entities': ['Customer', 'Admin'],
    'trust_boundaries': ['Internet', 'DMZ'],
    'data_flows': []
}

test_document_text = """
Web Application Security
- React frontend
- Node.js backend  
- MongoDB database
- JWT authentication
"""

# Mock detected controls
test_detected_controls = {
    'authentication': True,
    'encryption': True,
    'input_validation': False
}

def test_executive_summary():
    """Test the _generate_executive_summary method with mock data"""
    generator = ThreatGeneratorV3()
    
    # Mock threats data
    test_threats = [
        {'priority_category': 'Critical', 'Title': 'Test Critical Threat'},
        {'priority_category': 'High', 'Title': 'Test High Threat'},
        {'priority_category': 'Medium', 'Title': 'Test Medium Threat'},
    ]
    
    # Test the method that was failing
    try:
        summary = generator._generate_executive_summary(
            threats=test_threats,
            controls=list(test_detected_controls.keys()),  # Convert to list as expected
            v2_results={}  # Empty dict as we fixed
        )
        print("✅ _generate_executive_summary works correctly")
        print(f"   Risk level: {summary['overall_risk_level']}")
        print(f"   Controls present: {summary['security_controls_present']}")
        return True
    except Exception as e:
        print(f"❌ _generate_executive_summary failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing threat generation fixes...")
    
    if test_executive_summary():
        print("🎉 All fixes verified!")
    else:
        print("💥 Still has issues")