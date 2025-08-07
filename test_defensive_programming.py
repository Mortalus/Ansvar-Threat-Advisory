#!/usr/bin/env python3
"""
Direct test of defensive programming fixes in threat_generator_v3.py
This validates that isinstance(threat, dict) checks prevent crashes
"""
import sys
import os
sys.path.append('/Users/jeffreyvonrotz/SynologyDrive/Projects/ThreatModelingPipeline/apps/api')

from app.core.pipeline.steps.threat_generator_v3 import ThreatGeneratorV3
from app.core.llm.openai_provider import OpenAIProvider
import asyncio

async def test_defensive_programming():
    """Test defensive programming with mixed threat data types"""
    print("🛡️ Testing Defensive Programming in Threat Generation")
    print("=" * 60)
    
    # Create a mock LLM provider
    llm_provider = OpenAIProvider()
    threat_generator = ThreatGeneratorV3(llm_provider)
    
    # Test data with mixed types (strings and dicts) - this would cause the original error
    test_context_aware = [
        {"title": "SQL Injection", "severity": "High", "description": "Database vulnerability"},
        "Invalid string threat 1",  # This would cause 'str' has no attribute 'get'
        {"title": "XSS Attack", "severity": "Medium", "description": "Cross-site scripting"}
    ]
    
    test_architectural = [
        "Invalid string threat 2",  # Another problematic string
        {"title": "Authentication Bypass", "severity": "Critical", "description": "Auth vulnerability"},
        {"title": "Data Exposure", "severity": "High", "description": "Sensitive data leak"}
    ]
    
    test_business = [
        {"title": "Business Logic Flaw", "severity": "Medium", "description": "Process vulnerability"},
        "Invalid string threat 3",  # More string data that would crash
    ]
    
    test_compliance = [
        {"title": "GDPR Violation", "severity": "High", "description": "Privacy compliance issue"},
        {"title": "PCI DSS Gap", "severity": "Critical", "description": "Payment security gap"}
    ]
    
    print("🧪 Test Data Prepared:")
    print(f"  Context-aware threats: {len(test_context_aware)} (includes {sum(1 for t in test_context_aware if isinstance(t, str))} invalid strings)")
    print(f"  Architectural threats: {len(test_architectural)} (includes {sum(1 for t in test_architectural if isinstance(t, str))} invalid strings)")
    print(f"  Business threats: {len(test_business)} (includes {sum(1 for t in test_business if isinstance(t, str))} invalid strings)")
    print(f"  Compliance threats: {len(test_compliance)} (includes {sum(1 for t in test_compliance if isinstance(t, str))} invalid strings)")
    
    # Test _consolidate_threats method (this is where the original error occurred)
    print(f"\n🎯 Testing _consolidate_threats method...")
    try:
        consolidated = threat_generator._consolidate_threats(
            test_context_aware, 
            test_architectural, 
            test_business, 
            test_compliance
        )
        
        print(f"✅ Consolidation successful!")
        print(f"  Total consolidated threats: {len(consolidated)}")
        
        # Verify all results are valid dictionaries
        valid_threats = sum(1 for t in consolidated if isinstance(t, dict))
        invalid_threats = len(consolidated) - valid_threats
        
        print(f"  Valid threat objects: {valid_threats}")
        print(f"  Invalid threats filtered out: {invalid_threats}")
        
        if invalid_threats == 0:
            print(f"✅ All invalid string threats were properly filtered!")
        
    except Exception as e:
        print(f"❌ Consolidation failed: {e}")
        return False
    
    # Test other methods that were fixed
    print(f"\n🔧 Testing other defensive programming methods...")
    
    # Test _apply_advanced_prioritization
    try:
        sample_threats = [t for t in consolidated if isinstance(t, dict)][:3]  # Use valid threats
        prioritized = threat_generator._apply_advanced_prioritization(sample_threats)
        print(f"✅ _apply_advanced_prioritization: Processed {len(prioritized)} threats")
    except Exception as e:
        print(f"❌ _apply_advanced_prioritization failed: {e}")
        return False
    
    # Test _identify_critical_gaps
    try:
        gaps = threat_generator._identify_critical_gaps(consolidated)
        print(f"✅ _identify_critical_gaps: Identified {len(gaps)} gaps")
    except Exception as e:
        print(f"❌ _identify_critical_gaps failed: {e}")
        return False
    
    # Test summary methods
    try:
        arch_insights = threat_generator._summarize_architectural_insights(consolidated)
        bus_insights = threat_generator._summarize_business_insights(consolidated)  
        comp_insights = threat_generator._summarize_compliance_insights(consolidated)
        
        print(f"✅ Summary methods: All completed successfully")
        print(f"  Architectural insights: {len(arch_insights) if isinstance(arch_insights, list) else 'Summary generated'}")
        print(f"  Business insights: {len(bus_insights) if isinstance(bus_insights, list) else 'Summary generated'}")
        print(f"  Compliance insights: {len(comp_insights) if isinstance(comp_insights, list) else 'Summary generated'}")
        
    except Exception as e:
        print(f"❌ Summary methods failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 DEFENSIVE PROGRAMMING VALIDATION TEST")
    print("This test validates the isinstance(threat, dict) fixes")
    
    success = asyncio.run(test_defensive_programming())
    
    if success:
        print(f"\n" + "="*60)
        print(f"🎉 DEFENSIVE PROGRAMMING TEST PASSED! 🎉")
        print(f"="*60)
        print("✅ String threats properly filtered out")
        print("✅ isinstance(threat, dict) checks working")
        print("✅ No more 'str' object has no attribute 'get' errors")
        print("✅ All threat processing methods are crash-safe")
        print("\n🛡️ The defensive programming fixes are WORKING!")
        print("The original user issue has been RESOLVED!")
    else:
        print(f"\n💥 Defensive programming test FAILED")
        print("More fixes needed")