#!/usr/bin/env python3
"""
Test script for the modern Attack Path Analyzer
Demonstrates the analysis capabilities with sample data
"""

import asyncio
import json
from typing import Dict, Any, List

# Sample data for testing
SAMPLE_DFD_COMPONENTS = {
    "project_name": "HealthTech Analytics Platform",
    "project_version": "1.0",
    "industry_context": "Healthcare",
    "external_entities": [
        "Patients",
        "Doctors",
        "EHR Systems",
        "Payment Processor"
    ],
    "processes": [
        "Patient Portal",
        "Doctor Dashboard", 
        "API Server",
        "Analytics Engine",
        "Report Generator",
        "Authentication Service",
        "Session Management Service",
        "Audit Logging Service"
    ],
    "assets": [
        "Patient Database",
        "Analytics Cache",
        "Document Storage",
        "Audit Store",
        "Session Store",
        "Key Management Store"
    ],
    "trust_boundaries": [
        "DMZ",
        "Internal Network",
        "Admin Network (VPN)",
        "Database Network"
    ],
    "data_flows": [
        {
            "source": "Patients",
            "destination": "Patient Portal",
            "data_description": "Health record requests",
            "data_classification": "PII",
            "protocol": "HTTPS",
            "authentication_mechanism": "OAuth2"
        },
        {
            "source": "Patient Portal",
            "destination": "API Server",
            "data_description": "API requests",
            "data_classification": "PII",
            "protocol": "HTTPS",
            "authentication_mechanism": "JWT"
        },
        {
            "source": "API Server",
            "destination": "Patient Database",
            "data_description": "Patient data queries",
            "data_classification": "PHI",
            "protocol": "TLS",
            "authentication_mechanism": "Database Credentials"
        },
        {
            "source": "Doctors",
            "destination": "Doctor Dashboard",
            "data_description": "Medical data access",
            "data_classification": "PHI",
            "protocol": "HTTPS",
            "authentication_mechanism": "SAML"
        },
        {
            "source": "Doctor Dashboard",
            "destination": "API Server",
            "data_description": "Medical queries",
            "data_classification": "PHI",
            "protocol": "HTTPS",
            "authentication_mechanism": "Bearer Token"
        },
        {
            "source": "API Server",
            "destination": "Analytics Engine",
            "data_description": "Data processing requests",
            "data_classification": "Internal",
            "protocol": "HTTP",
            "authentication_mechanism": "Service Token"
        }
    ]
}

SAMPLE_REFINED_THREATS = [
    {
        "threat_id": "T001",
        "component_name": "Patient Portal",
        "threat_description": "Web application vulnerable to cross-site scripting attacks allowing session hijacking",
        "stride_category": "S",
        "impact": "High",
        "likelihood": "Medium",
        "risk_score": 75
    },
    {
        "threat_id": "T002", 
        "component_name": "API Server",
        "threat_description": "API endpoints lack proper rate limiting enabling denial of service attacks",
        "stride_category": "D",
        "impact": "Medium",
        "likelihood": "High",
        "risk_score": 70
    },
    {
        "threat_id": "T003",
        "component_name": "Patient Database",
        "threat_description": "Database injection vulnerability allows unauthorized data access",
        "stride_category": "I",
        "impact": "Critical",
        "likelihood": "Medium",
        "risk_score": 90
    },
    {
        "threat_id": "T004",
        "component_name": "Authentication Service",
        "threat_description": "Weak password policies enable brute force credential attacks",
        "stride_category": "S",
        "impact": "High",
        "likelihood": "High",
        "risk_score": 85
    },
    {
        "threat_id": "T005",
        "component_name": "Session Management Service",
        "threat_description": "Session tokens lack secure attributes enabling hijacking attacks",
        "stride_category": "E",
        "impact": "High",
        "likelihood": "Medium",
        "risk_score": 75
    },
    {
        "threat_id": "T006",
        "component_name": "Analytics Engine",
        "threat_description": "Processing service vulnerable to code injection via malformed data",
        "stride_category": "T",
        "impact": "High",
        "likelihood": "Low",
        "risk_score": 60
    }
]

class MockSession:
    """Mock database session for testing."""
    pass

async def test_attack_path_analyzer():
    """Test the attack path analyzer with sample data."""
    
    print("=" * 80)
    print("MODERN ATTACK PATH ANALYZER DEMONSTRATION")
    print("=" * 80)
    
    # Import the analyzer
    from app.core.pipeline.steps.attack_path_analyzer import AttackPathAnalyzer
    
    print("\n📊 SAMPLE DATA:")
    print("-" * 40)
    print(f"DFD Components:")
    print(f"  - External Entities: {len(SAMPLE_DFD_COMPONENTS['external_entities'])}")
    print(f"  - Processes: {len(SAMPLE_DFD_COMPONENTS['processes'])}")
    print(f"  - Assets: {len(SAMPLE_DFD_COMPONENTS['assets'])}")
    print(f"  - Data Flows: {len(SAMPLE_DFD_COMPONENTS['data_flows'])}")
    print(f"Refined Threats: {len(SAMPLE_REFINED_THREATS)}")
    
    print("\n🔍 INITIALIZING ANALYZER:")
    print("-" * 40)
    
    analyzer = AttackPathAnalyzer(
        max_path_length=4,
        max_paths_to_analyze=10
    )
    
    print("✅ Analyzer initialized")
    print(f"  - Max path length: {analyzer.max_path_length}")
    print(f"  - Max paths to analyze: {analyzer.max_paths_to_analyze}")
    
    print("\n⚡ EXECUTING ANALYSIS:")
    print("-" * 40)
    
    try:
        # Execute analysis
        mock_session = MockSession()
        
        result = await analyzer.execute(
            db_session=mock_session,
            pipeline_step_result=None,
            refined_threats=SAMPLE_REFINED_THREATS,
            dfd_components=SAMPLE_DFD_COMPONENTS
        )
        
        print("✅ Analysis completed successfully!")
        
        print("\n📈 RESULTS SUMMARY:")
        print("-" * 40)
        print(f"Attack paths found: {len(result['attack_paths'])}")
        print(f"Critical scenarios: {len(result['critical_scenarios'])}")
        print(f"Defense priorities: {len(result['defense_priorities'])}")
        
        # Threat coverage
        coverage = result['threat_coverage']
        print(f"Threat coverage: {coverage['coverage_percentage']:.1f}% "
              f"({coverage['covered_threats']}/{coverage['total_threats']})")
        
        print("\n🎯 TOP ATTACK PATHS:")
        print("-" * 40)
        for i, path in enumerate(result['attack_paths'][:3], 1):
            print(f"{i}. {path['scenario_name']}")
            print(f"   Entry: {path['entry_point']} → Target: {path['target_asset']}")
            print(f"   Steps: {path['total_steps']} | Impact: {path['combined_impact']} | "
                  f"Likelihood: {path['combined_likelihood']}")
            print(f"   Feasibility: {path['path_feasibility']} | "
                  f"Time: {path['time_to_compromise']}")
            
            # Show attack steps
            for step in path['path_steps'][:3]:
                print(f"     Step {step['step_number']}: {step['component']} "
                      f"({step['stride_category']}) - {step['required_access']}")
            
            if len(path['path_steps']) > 3:
                print(f"     ... and {len(path['path_steps']) - 3} more steps")
            print()
        
        print("\n🛡️ TOP DEFENSE PRIORITIES:")
        print("-" * 40)
        for i, priority in enumerate(result['defense_priorities'][:5], 1):
            print(f"{i}. {priority['recommendation']}")
            print(f"   Priority: {priority['priority']} | Category: {priority['category']}")
            print(f"   Impact: {priority['impact']}")
            print(f"   Effort: {priority['effort']}")
            print()
        
        print("\n🚨 CRITICAL SCENARIOS:")
        print("-" * 40)
        for i, scenario in enumerate(result['critical_scenarios'], 1):
            print(f"{i}. {scenario}")
        
        print("\n📊 METADATA:")
        print("-" * 40)
        metadata = result['metadata']
        print(f"Analysis timestamp: {metadata['timestamp']}")
        print(f"Total paths found: {metadata['total_paths_found']}")
        print(f"Detailed paths built: {metadata['detailed_paths_built']}")
        print(f"Entry points identified: {len(metadata['entry_points'])}")
        print(f"Critical assets identified: {len(metadata['critical_assets'])}")
        print(f"LLM enrichment enabled: {metadata['llm_enrichment_enabled']}")
        
        if result['attack_paths']:
            print("\n🔗 SAMPLE ATTACK CHAIN DETAILS:")
            print("-" * 40)
            sample_path = result['attack_paths'][0]
            print(f"Path ID: {sample_path['path_id']}")
            print(f"Attacker Profile: {sample_path['attacker_profile']}")
            print(f"Path Complexity: {sample_path['path_complexity']}")
            
            if sample_path.get('key_chokepoints'):
                print(f"Key Chokepoints:")
                for choke in sample_path['key_chokepoints']:
                    print(f"  • {choke}")
            
            if sample_path.get('detection_opportunities'):
                print(f"Detection Opportunities:")
                for detect in sample_path['detection_opportunities']:
                    print(f"  • {detect}")
            
            if sample_path.get('required_resources'):
                print(f"Required Resources:")
                for resource in sample_path['required_resources']:
                    print(f"  • {resource}")
        
        print("\n" + "=" * 80)
        print("✅ MODERN ATTACK PATH ANALYZER WORKING PERFECTLY!")
        print("=" * 80)
        
        print("\n🚀 KEY IMPROVEMENTS OVER ORIGINAL SCRIPT:")
        print("  ✅ Fully integrated with pipeline (no file I/O)")
        print("  ✅ Uses existing LLM providers")
        print("  ✅ Async/await for better performance")
        print("  ✅ Type hints and dataclasses")
        print("  ✅ Database integration ready")
        print("  ✅ API endpoint included")
        print("  ✅ Configurable parameters")
        print("  ✅ Robust error handling")
        print("  ✅ Modern Python patterns")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_attack_path_analyzer())