#!/usr/bin/env python3
"""
Direct test of the optimized threat refinement system
"""
import asyncio
import sys
sys.path.append('/Users/jeffreyvonrotz/SynologyDrive/Projects/ThreatModelingPipeline/apps/api')

from app.core.pipeline.steps.threat_refiner_optimized import OptimizedThreatRefiner

async def test_optimized_refinement():
    """Test the optimized refinement directly"""
    print("🧠 Testing Optimized Threat Refinement Directly")
    print("=" * 50)
    
    # Sample threat data
    sample_threats = [
        {
            "Threat Category": "S",
            "Threat Name": "SQL Injection",
            "Description": "Attacker injects malicious SQL code through user input fields",
            "Potential Impact": "High", 
            "Likelihood": "Medium",
            "Suggested Mitigation": "Use parameterized queries",
            "component_name": "Web Application",
            "component_type": "Process"
        },
        {
            "Threat Category": "T",
            "Threat Name": "Data Tampering",
            "Description": "Unauthorized modification of data in transit",
            "Potential Impact": "Medium",
            "Likelihood": "Low", 
            "Suggested Mitigation": "Use encryption and integrity checks",
            "component_name": "Database",
            "component_type": "Data Store"
        },
        {
            "Threat Category": "I",
            "Threat Name": "Information Disclosure",
            "Description": "Sensitive data exposed to unauthorized users",
            "Potential Impact": "High",
            "Likelihood": "High",
            "Suggested Mitigation": "Implement access controls",
            "component_name": "User Database", 
            "component_type": "Data Store"
        }
    ]
    
    threat_data = {
        "threats": sample_threats,
        "components_analyzed": 2,
        "total_count": len(sample_threats)
    }
    
    try:
        # Create refiner instance
        refiner = OptimizedThreatRefiner()
        
        print(f"Input: {len(sample_threats)} sample threats")
        
        # Execute refinement
        import time
        start_time = time.time()
        
        result = await refiner.execute(
            db_session=None,  # Not needed for this test
            pipeline_step_result=None,
            threat_data=threat_data
        )
        
        elapsed = time.time() - start_time
        print(f"⏱️  Refinement completed in {elapsed:.2f} seconds")
        
        # Display results
        refined_threats = result.get("refined_threats", [])
        stats = result.get("refinement_stats", {})
        
        print(f"\n📊 Results:")
        print(f"  - Original threats: {stats.get('original_count', 0)}")
        print(f"  - Final threats: {stats.get('final_count', 0)}")
        print(f"  - Refinement method: {stats.get('refinement_method', 'unknown')}")
        
        # Show risk distribution
        risk_dist = stats.get('risk_distribution', {})
        if risk_dist:
            print(f"\n🎯 Risk Distribution:")
            for level, count in risk_dist.items():
                if count > 0:
                    print(f"    {level}: {count} threats")
        
        # Show sample enhanced threat
        if refined_threats:
            print(f"\n🔍 Sample Enhanced Threat:")
            sample = refined_threats[0]
            print(f"  Name: {sample.get('Threat Name', 'N/A')}")
            print(f"  Risk Score: {sample.get('risk_score', 'N/A')}")
            print(f"  Priority Rank: {sample.get('priority_rank', 'N/A')}")
            print(f"  Business Risk: {sample.get('business_risk_statement', 'N/A')[:100]}...")
            print(f"  Implementation Priority: {sample.get('implementation_priority', 'N/A')}")
            
        print(f"\n✅ Direct refinement test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Direct refinement test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_optimized_refinement())
    exit(0 if success else 1)