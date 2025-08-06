from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from datetime import datetime

router = APIRouter(prefix="/debug", tags=["debug"])
logger = logging.getLogger(__name__)

# Sample data for debug mode
SAMPLE_DFD_COMPONENTS = {
    "project_name": "E-Commerce Platform Debug",
    "project_version": "1.0",
    "industry_context": "Retail/E-commerce",
    "external_entities": [
        "Customer", "Admin User", "Payment Processor", "Shipping Partner"
    ],
    "assets": [
        "Customer Database", "Product Catalog", "Order Management System", 
        "Payment Gateway", "Session Store", "Admin Dashboard"
    ],
    "processes": [
        "Web Application Server", "API Gateway", "Authentication Service",
        "Order Processing Service", "Payment Processing Service"
    ],
    "trust_boundaries": [
        "Internet", "DMZ", "Internal Network", "Database Network"
    ],
    "data_flows": [
        {
            "source": "Customer",
            "destination": "Web Application Server",
            "data_description": "Login credentials, product searches, order data",
            "data_classification": "PII/Financial",
            "protocol": "HTTPS",
            "authentication_mechanism": "Session Cookies + JWT"
        }
    ]
}

SAMPLE_THREATS = [
    {
        "Threat Category": "Spoofing",
        "Threat Name": "Session Hijacking Attack",
        "Description": "An attacker intercepts or steals a user's session token to impersonate them and gain unauthorized access to their account.",
        "Potential Impact": "High",
        "Likelihood": "Medium",
        "Suggested Mitigation": "Implement secure session management with HttpOnly cookies, session rotation, and proper CSRF protection",
        "component_id": "web_app_1",
        "component_name": "Web Application Server",
        "component_type": "Process"
    },
    {
        "Threat Category": "Tampering",
        "Threat Name": "SQL Injection in User Queries",
        "Description": "Malicious SQL code injected through user input fields could allow attackers to manipulate database queries.",
        "Potential Impact": "Critical",
        "Likelihood": "High",
        "Suggested Mitigation": "Use parameterized queries, input validation, and principle of least privilege for database access",
        "component_id": "db_1",
        "component_name": "Customer Database",
        "component_type": "Data Store"
    },
    {
        "Threat Category": "Information Disclosure",
        "Threat Name": "Payment Data Exposure",
        "Description": "Sensitive payment information could be exposed through inadequate encryption or insecure API responses.",
        "Potential Impact": "Critical",
        "Likelihood": "Medium",
        "Suggested Mitigation": "Implement PCI DSS compliant data handling, encryption at rest and in transit",
        "component_id": "payment_1",
        "component_name": "Payment Processing Service",
        "component_type": "Process"
    }
]

@router.post("/quick-refine", response_model=dict)
async def quick_threat_refinement():
    """
    Debug endpoint that returns sample refined threats instantly.
    Bypasses actual LLM processing for testing.
    """
    logger.info("Debug: Quick threat refinement called")
    
    # Sample refined threats with AI enhancements
    refined_threats = [
        {
            **SAMPLE_THREATS[1],  # SQL Injection - highest priority
            "risk_score": "Critical",
            "priority_rank": 1,
            "priority_ranking": "#1",
            "implementation_priority": "Immediate",
            "business_risk_statement": "SQL injection vulnerabilities could lead to massive customer data breaches, resulting in regulatory fines up to $4.7M under GDPR.",
            "financial_impact_range": "$1M - $10M+ in direct costs, fines, and lost revenue",
            "exploitability": "High",
            "estimated_effort": "Days",
            "assessment_reasoning": "Critical risk due to high likelihood and catastrophic business impact. Database contains PII and financial data.",
            "primary_mitigation": "Immediately implement parameterized queries across all database interactions and deploy WAF with SQL injection detection.",
            "business_enhancement_method": "debug_mode",
            "risk_assessment_method": "debug_batch"
        },
        {
            **SAMPLE_THREATS[2],  # Payment Data
            "risk_score": "Critical",
            "priority_rank": 2,
            "priority_ranking": "#2", 
            "implementation_priority": "Immediate",
            "business_risk_statement": "Payment data exposure would trigger PCI DSS violations and loss of payment processing capabilities.",
            "financial_impact_range": "$500K - $5M+ plus loss of payment processing",
            "exploitability": "Medium",
            "estimated_effort": "Weeks",
            "assessment_reasoning": "Critical business risk due to PCI compliance requirements and payment processing dependency.",
            "primary_mitigation": "Implement end-to-end encryption for payment data and deploy tokenization for stored payment information.",
            "business_enhancement_method": "debug_mode",
            "risk_assessment_method": "debug_batch"
        },
        {
            **SAMPLE_THREATS[0],  # Session Hijacking
            "risk_score": "High",
            "priority_rank": 3,
            "priority_ranking": "#3",
            "implementation_priority": "High", 
            "business_risk_statement": "Session hijacking could lead to unauthorized account access and fraudulent purchases, damaging brand reputation.",
            "financial_impact_range": "$100K - $1M in fraud costs and reputation damage",
            "exploitability": "Medium",
            "estimated_effort": "Days",
            "assessment_reasoning": "High risk due to direct impact on customer accounts and common attack vector in e-commerce.",
            "primary_mitigation": "Deploy secure session management with HttpOnly/Secure cookies and implement session rotation.",
            "business_enhancement_method": "debug_mode",
            "risk_assessment_method": "debug_batch"
        }
    ]
    
    return {
        "pipeline_id": "debug-pipeline-12345",
        "refined_threats": refined_threats,
        "total_count": len(refined_threats),
        "refinement_stats": {
            "original_count": len(SAMPLE_THREATS),
            "deduplicated_count": 0,
            "final_count": len(refined_threats),
            "risk_distribution": {
                "Critical": 2,
                "High": 1,
                "Medium": 0,
                "Low": 0
            },
            "refinement_timestamp": datetime.utcnow().isoformat(),
            "refinement_method": "debug_mode"
        },
        "refined_at": datetime.utcnow().isoformat(),
        "status": "refined"
    }

@router.get("/sample-dfd", response_model=dict)
async def get_sample_dfd():
    """Get sample DFD components for debug mode."""
    return {
        "pipeline_id": "debug-pipeline-12345",
        "dfd_components": SAMPLE_DFD_COMPONENTS,
        "validation": {
            "quality_score": 0.85,
            "suggestions": ["Consider adding more specific trust boundaries"],
            "completeness": 0.9
        },
        "status": "extracted"
    }

@router.get("/sample-threats", response_model=dict)  
async def get_sample_threats():
    """Get sample threats for debug mode."""
    return {
        "pipeline_id": "debug-pipeline-12345",
        "threats": SAMPLE_THREATS,
        "total_count": len(SAMPLE_THREATS),
        "components_analyzed": 5,
        "knowledge_sources_used": ["STRIDE", "OWASP Top 10", "Debug Mode"],
        "generated_at": datetime.utcnow().isoformat(),
        "status": "generated"
    }