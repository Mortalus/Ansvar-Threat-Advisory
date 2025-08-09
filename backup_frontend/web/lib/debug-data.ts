/**
 * Debug/Test data for rapid development and testing
 */
import { DFDComponents, Threat, RefinedThreat } from './api'

export const SAMPLE_DFD_COMPONENTS: DFDComponents = {
  project_name: "E-Commerce Platform Debug",
  project_version: "1.0",
  industry_context: "Retail/E-commerce",
  external_entities: [
    "Customer",
    "Admin User", 
    "Payment Processor",
    "Shipping Partner",
    "Marketing Analytics"
  ],
  assets: [
    "Customer Database",
    "Product Catalog",
    "Order Management System",
    "Payment Gateway",
    "Session Store",
    "Admin Dashboard"
  ],
  processes: [
    "Web Application Server",
    "API Gateway",
    "Authentication Service",
    "Order Processing Service",
    "Payment Processing Service",
    "Inventory Management"
  ],
  trust_boundaries: [
    "Internet",
    "DMZ", 
    "Internal Network",
    "Database Network",
    "Admin Network"
  ],
  data_flows: [
    {
      source: "Customer",
      destination: "Web Application Server",
      data_description: "Login credentials, product searches, order data",
      data_classification: "PII/Financial",
      protocol: "HTTPS",
      authentication_mechanism: "Session Cookies + JWT"
    },
    {
      source: "Web Application Server", 
      destination: "Customer Database",
      data_description: "User profile data, order history",
      data_classification: "PII/Financial",
      protocol: "TLS 1.3",
      authentication_mechanism: "Database Authentication"
    },
    {
      source: "Payment Processing Service",
      destination: "Payment Processor",
      data_description: "Credit card data, payment amounts",
      data_classification: "PCI Data",
      protocol: "HTTPS",
      authentication_mechanism: "API Keys + OAuth"
    },
    {
      source: "Admin User",
      destination: "Admin Dashboard", 
      data_description: "Administrative commands, user management",
      data_classification: "Administrative",
      protocol: "HTTPS",
      authentication_mechanism: "Multi-Factor Authentication"
    }
  ]
}

export const SAMPLE_THREATS: Threat[] = [
  {
    "Threat Category": "Spoofing",
    "Threat Name": "Session Hijacking Attack",
    "Description": "An attacker intercepts or steals a user's session token to impersonate them and gain unauthorized access to their account. This could occur through XSS, man-in-the-middle attacks, or insecure session handling.",
    "Potential Impact": "High",
    "Likelihood": "Medium", 
    "Suggested Mitigation": "Implement secure session management with HttpOnly cookies, session rotation, and proper CSRF protection",
    component_id: "web_app_1",
    component_name: "Web Application Server",
    component_type: "Process"
  },
  {
    "Threat Category": "Tampering",
    "Threat Name": "SQL Injection in User Queries",
    "Description": "Malicious SQL code injected through user input fields could allow attackers to manipulate database queries, access unauthorized data, or modify database contents.",
    "Potential Impact": "Critical",
    "Likelihood": "High",
    "Suggested Mitigation": "Use parameterized queries, input validation, and principle of least privilege for database access",
    component_id: "db_1", 
    component_name: "Customer Database",
    component_type: "Data Store"
  },
  {
    "Threat Category": "Information Disclosure",
    "Threat Name": "Payment Data Exposure",
    "Description": "Sensitive payment information could be exposed through inadequate encryption, logging of sensitive data, or insecure API responses containing PCI data.",
    "Potential Impact": "Critical",
    "Likelihood": "Medium",
    "Suggested Mitigation": "Implement PCI DSS compliant data handling, encryption at rest and in transit, and secure logging practices",
    component_id: "payment_1",
    component_name: "Payment Processing Service", 
    component_type: "Process"
  },
  {
    "Threat Category": "Denial of Service",
    "Threat Name": "API Rate Limiting Bypass",
    "Description": "Attackers could overwhelm the API gateway with requests, bypassing rate limiting mechanisms and causing service degradation or complete unavailability.",
    "Potential Impact": "High", 
    "Likelihood": "Medium",
    "Suggested Mitigation": "Implement robust rate limiting, request throttling, and DDoS protection mechanisms",
    component_id: "api_gw_1",
    component_name: "API Gateway",
    component_type: "Process"
  },
  {
    "Threat Category": "Elevation of Privilege",
    "Threat Name": "Admin Privilege Escalation", 
    "Description": "A regular user could exploit vulnerabilities in the authentication system to gain administrative privileges and access sensitive administrative functions.",
    "Potential Impact": "Critical",
    "Likelihood": "Low",
    "Suggested Mitigation": "Implement role-based access control, regular privilege reviews, and multi-factor authentication for admin accounts",
    component_id: "auth_1",
    component_name: "Authentication Service",
    component_type: "Process"
  },
  {
    "Threat Category": "Repudiation",
    "Threat Name": "Transaction Log Tampering",
    "Description": "Attackers could modify or delete transaction logs to hide fraudulent activities or dispute legitimate transactions, affecting audit trails and compliance.",
    "Potential Impact": "High",
    "Likelihood": "Low", 
    "Suggested Mitigation": "Implement tamper-proof logging, log integrity checks, and secure centralized log management",
    component_id: "order_1",
    component_name: "Order Management System",
    component_type: "Process"
  }
]

export const SAMPLE_REFINED_THREATS: RefinedThreat[] = [
  {
    ...SAMPLE_THREATS[1], // SQL Injection - highest priority
    risk_score: "Critical",
    priority_rank: 1,
    priority_ranking: "#1",
    implementation_priority: "Immediate",
    business_risk_statement: "SQL injection vulnerabilities could lead to massive customer data breaches, resulting in regulatory fines up to $4.7M under GDPR, complete loss of customer trust, and potential business closure.",
    financial_impact_range: "$1M - $10M+ in direct costs, fines, and lost revenue",
    exploitability: "High",
    estimated_effort: "Days",
    assessment_reasoning: "Critical risk due to high likelihood and catastrophic business impact. Database contains PII and financial data making this a prime target.",
    primary_mitigation: "Immediately implement parameterized queries across all database interactions, deploy a Web Application Firewall with SQL injection detection, and conduct emergency code review of all user input handling."
  },
  {
    ...SAMPLE_THREATS[2], // Payment Data Exposure
    risk_score: "Critical", 
    priority_rank: 2,
    priority_ranking: "#2",
    implementation_priority: "Immediate",
    business_risk_statement: "Payment data exposure would trigger immediate PCI DSS compliance violations, result in losing ability to process credit cards, and face regulatory fines exceeding $500K monthly.",
    financial_impact_range: "$500K - $5M+ plus loss of payment processing",
    exploitability: "Medium",
    estimated_effort: "Weeks",
    assessment_reasoning: "Critical business risk due to PCI compliance requirements. Any payment data exposure could shut down payment processing immediately.",
    primary_mitigation: "Implement end-to-end encryption for all payment data, deploy tokenization for stored payment information, and establish secure key management with HSMs.",
  },
  {
    ...SAMPLE_THREATS[0], // Session Hijacking
    risk_score: "High",
    priority_rank: 3, 
    priority_ranking: "#3",
    implementation_priority: "High",
    business_risk_statement: "Session hijacking attacks could lead to unauthorized account access, fraudulent purchases, and customer data theft, damaging brand reputation and customer confidence.",
    financial_impact_range: "$100K - $1M in fraud costs and reputation damage",
    exploitability: "Medium",
    estimated_effort: "Days", 
    assessment_reasoning: "High risk due to direct impact on customer accounts and relatively common attack vector in e-commerce platforms.",
    primary_mitigation: "Deploy secure session management with HttpOnly/Secure cookies, implement session rotation on privilege changes, and add real-time session monitoring.",
  },
  {
    ...SAMPLE_THREATS[4], // Admin Privilege Escalation
    risk_score: "High",
    priority_rank: 4,
    priority_ranking: "#4", 
    implementation_priority: "High",
    business_risk_statement: "Admin privilege escalation could give attackers complete control over the e-commerce platform, enabling them to steal all customer data, manipulate orders, and completely compromise business operations.",
    financial_impact_range: "$500K - $3M+ in comprehensive breach costs",
    exploitability: "Low",
    estimated_effort: "Weeks",
    assessment_reasoning: "High impact but lower likelihood. Administrative access compromise would be catastrophic but requires sophisticated attack.",
    primary_mitigation: "Enforce strict role-based access controls, implement mandatory multi-factor authentication for all admin accounts, and deploy privileged access management (PAM) solutions."
  },
  {
    ...SAMPLE_THREATS[3], // API DoS
    risk_score: "Medium",
    priority_rank: 5,
    priority_ranking: "#5",
    implementation_priority: "Medium", 
    business_risk_statement: "API denial of service attacks could make the e-commerce platform unavailable during peak shopping periods, resulting in direct revenue loss and customer frustration.",
    financial_impact_range: "$50K - $500K in lost sales during outages",
    exploitability: "Medium",
    estimated_effort: "Days",
    assessment_reasoning: "Medium risk with direct revenue impact but multiple mitigation options available. Availability critical for e-commerce.",
    primary_mitigation: "Deploy robust API rate limiting with sliding windows, implement DDoS protection services, and establish auto-scaling capabilities for traffic spikes.",
  },
  {
    ...SAMPLE_THREATS[5], // Log Tampering
    risk_score: "Medium",
    priority_rank: 6,
    priority_ranking: "#6",
    implementation_priority: "Medium",
    business_risk_statement: "Transaction log tampering could hide fraudulent activities and impact regulatory compliance, potentially leading to audit failures and regulatory scrutiny.",
    financial_impact_range: "$25K - $250K in compliance and audit costs",
    exploitability: "Low", 
    estimated_effort: "Weeks",
    assessment_reasoning: "Medium risk focused on compliance and audit integrity. Lower likelihood but important for regulatory requirements.",
    primary_mitigation: "Implement tamper-evident logging with cryptographic signatures, deploy centralized log management with immutable storage, and establish log integrity monitoring.",
  }
]

export const DEBUG_PIPELINE_DATA = {
  pipeline_id: "debug-pipeline-12345",
  document_text: "Debug: Sample e-commerce architecture with web servers, databases, and payment processing...",
  files: [
    { filename: "debug-architecture.txt", size: 2048, content_type: "text/plain" }
  ],
  text_length: 2048
}