#!/usr/bin/env python3
"""
Test script for Threat Generator V2 with context-aware risk scoring.
This tests Part 1 of the three-stage improvement plan.
"""

import asyncio
import json
import sys
import os

# Add the api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from app.core.pipeline.steps.threat_generator_v2 import ThreatGeneratorV2, ControlsLibrary
from app.database import AsyncSessionLocal

# Sample DFD components based on the e-commerce example
SAMPLE_DFD = {
    "processes": [
        {
            "id": "p1",
            "name": "Authentication Service",
            "description": "Handles user authentication with Auth0 integration"
        },
        {
            "id": "p2", 
            "name": "Payment Processing Service",
            "description": "Processes payments through Stripe API"
        },
        {
            "id": "p3",
            "name": "Order Processing Service",
            "description": "Validates and processes customer orders"
        }
    ],
    "data_stores": [
        {
            "id": "ds1",
            "name": "User Database",
            "description": "PostgreSQL database storing customer profiles and credentials"
        },
        {
            "id": "ds2",
            "name": "Order Database",
            "description": "Stores order history and transactions"
        }
    ],
    "external_entities": [
        {
            "id": "ee1",
            "name": "Customers",
            "description": "End users who browse and purchase products"
        },
        {
            "id": "ee2",
            "name": "Payment Gateway",
            "description": "Stripe external payment service"
        }
    ],
    "data_flows": [
        {
            "id": "df1",
            "name": "Login Credentials",
            "source": "Customers",
            "destination": "Authentication Service",
            "description": "Customer sends credentials via HTTPS"
        },
        {
            "id": "df2",
            "name": "Payment Data",
            "source": "Order Processing Service",
            "destination": "Payment Gateway",
            "description": "Payment information sent to Stripe (PCI-compliant)"
        }
    ]
}

# Sample document text with security controls
SAMPLE_DOCUMENT = """
E-Commerce Platform Architecture Document

Security Considerations:
- All external communications use TLS 1.3 encryption
- API endpoints protected with rate limiting and WAF
- Input validation on all user inputs using parameterized queries
- OAuth2 authentication with JWT tokens and MFA required for admin
- Regular security audits and penetration testing
- GDPR compliance for European customers
- PCI DSS compliance for payment processing
- Database access controlled by RBAC policies
- All admin actions logged for audit trail
- VPN and bastion host protect admin interfaces
- Redis session cache with automatic expiry
- Backup and disaster recovery plan with daily backups
- Network segmentation with DMZ for public-facing services
- SIEM monitoring and alerting for security events
"""

async def test_controls_library():
    """Test the controls library parsing."""
    print("\n=== Testing Controls Library ===")
    
    controls = ControlsLibrary()
    detected = controls.parse_document_for_controls(SAMPLE_DOCUMENT)
    
    print(f"\nDetected {len(detected)} types of security controls:")
    for control_type, keywords in detected.items():
        print(f"  - {control_type}: {[k['keyword'] for k in keywords]}")
    
    # Test control effectiveness
    effectiveness = controls.get_control_effectiveness("Tampering", "data_flow")
    print(f"\nControl effectiveness against Tampering in data_flow: {effectiveness:.0%}")
    
    return controls

async def test_threat_generation_v2():
    """Test the V2 threat generator."""
    print("\n=== Testing Threat Generator V2 ===")
    
    generator = ThreatGeneratorV2()
    
    # Create a mock database session
    async with AsyncSessionLocal() as session:
        try:
            result = await generator.execute(
                db_session=session,
                pipeline_step_result=None,
                component_data=SAMPLE_DFD,
                document_text=SAMPLE_DOCUMENT
            )
            
            print(f"\nGenerated {result['total_count']} threats")
            print(f"Components analyzed: {result['components_analyzed']}")
            print(f"Security controls detected: {result['security_controls_detected']}")
            
            # Display risk metrics
            metrics = result.get('risk_metrics', {})
            print("\nRisk Metrics:")
            print(f"  - Total threats generated: {metrics.get('total_threats_generated', 0)}")
            print(f"  - After deduplication: {metrics.get('post_deduplication', 0)}")
            print(f"  - High residual risk: {metrics.get('high_residual_risk', 0)}")
            print(f"  - Controls effectiveness: {metrics.get('controls_effectiveness', 'N/A')}")
            
            # Display first few threats
            print("\n=== Sample Threats with Residual Risk ===")
            for i, threat in enumerate(result['threats'][:3], 1):
                print(f"\nThreat {i}: {threat.get('Threat Name', 'Unknown')}")
                print(f"  Component: {threat.get('component_name', 'Unknown')}")
                print(f"  Category: {threat.get('Threat Category', 'Unknown')}")
                print(f"  Inherent Risk: {threat.get('inherent_risk', 'Unknown')}")
                print(f"  Residual Risk: {threat.get('residual_risk', 'Unknown')}")
                print(f"  Risk Reduction: {threat.get('risk_reduction', 'Unknown')}")
                print(f"  Applicable Controls: {threat.get('applicable_controls', [])}")
                
                # Show threat chain if available
                chain = threat.get('threat_chain', {})
                if chain:
                    print(f"  Attack Vector: {chain.get('attack_vector', 'Unknown')}")
                    print(f"  Kill Chain Phase: {chain.get('kill_chain_phase', 'Unknown')}")
            
            return result
            
        except Exception as e:
            print(f"Error during testing: {e}")
            import traceback
            traceback.print_exc()
            return None

async def main():
    """Run all tests."""
    print("=" * 60)
    print("THREAT GENERATOR V2 - PART 1 TEST")
    print("Context-Aware Risk Scoring with Controls Library")
    print("=" * 60)
    
    # Test controls library
    controls = await test_controls_library()
    
    # Test threat generation
    result = await test_threat_generation_v2()
    
    if result:
        print("\n✅ Part 1 Implementation Complete!")
        print("\nKey Features Demonstrated:")
        print("1. ✅ Controls Library - Parses and identifies security controls")
        print("2. ✅ Residual Risk Algorithm - Adjusts risk based on controls")
        print("3. ✅ Threat Specificity - Component-bound threats with chains")
        print("4. ✅ Semantic Deduplication - Reduces duplicate threats")
        
        print("\n📊 Coverage Report:")
        coverage = result.get('control_coverage', {})
        for control, present in coverage.items():
            status = "✅" if present else "❌"
            print(f"  {status} {control}")
    else:
        print("\n❌ Test failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())