# 🔍 Threat Generation & Refinement Pipeline: Complete Functional Walkthrough

This document explains exactly how threats are generated and refined in the system, from document upload to final prioritized threats.

## 📋 **High-Level Pipeline Overview**

```
📄 Document Upload → 🔍 DFD Extraction → 🎯 Threat Generation (V3) → ⚖️ Threat Refinement → 📊 Final Results
```

## 🚀 **Step 1: Document Processing & DFD Extraction**

### **Input**: User uploads documents (PDF, DOCX, TXT)

### **Process**:

**1.1 Document Text Extraction**
- Documents converted to plain text
- Combined into single text blob
- Limited to 15,000 characters for LLM processing

**1.2 LLM-Powered DFD Component Extraction**
The system uses a specialized prompt to extract structured components:

```
You are a senior cybersecurity analyst specializing in threat modeling and Data Flow Diagram (DFD) extraction. 

Required JSON Schema:
{
  "project_name": "string - Name of the system/project",
  "project_version": "string - Version number",
  "industry_context": "string - Industry or domain",
  "external_entities": ["External users, systems, third-party services"],
  "assets": ["Data stores, databases, file systems, caches"],
  "processes": ["Services, applications, functions, APIs"],
  "trust_boundaries": ["Network zones, security perimeters"],
  "data_flows": [
    {
      "source": "Origin component",
      "destination": "Target component",
      "data_description": "What data is transferred",
      "data_classification": "Confidential/PII/Internal/Public",
      "protocol": "HTTPS/TLS/SSH/etc",
      "authentication_mechanism": "OAuth2/API Key/Certificate/etc"
    }
  ]
}
```

**Analysis Guidelines:**
1. **External Entities**: Users, external systems, third-party APIs, payment gateways
2. **Assets**: Databases, file storage, caches, data warehouses, S3 buckets
3. **Processes**: Microservices, APIs, web servers, processing engines, Lambda functions
4. **Trust Boundaries**: DMZs, VPCs, network segments, cloud boundaries
5. **Data Flows**: Connections showing data movement between components

### **Output**: Structured DFD components in JSON format:
```json
{
  "external_entities": ["User", "Payment Gateway", "Admin"],
  "assets": ["User Database", "Payment Database", "Log Files"],
  "processes": ["Web Server", "API Gateway", "Auth Service"],
  "trust_boundaries": ["DMZ", "Internal Network"],
  "data_flows": [
    {
      "source": "User",
      "destination": "Web Server", 
      "data_description": "Login credentials",
      "data_classification": "Confidential"
    }
  ]
}
```

## 🎯 **Step 2: Threat Generation (V3 Multi-Agent System)**

This is where the magic happens! V3 uses **three specialized AI agents** running concurrently.

### **Phase 1: Context-Aware Threat Generation (V2)**
First, V3 runs the V2 generator to get baseline STRIDE threats:

**V2 Process:**
1. **STRIDE Analysis**: Applies traditional STRIDE methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
2. **Context-Aware Risk Scoring**: Uses a controls library to calculate residual risk
3. **Component-Specific Threats**: Generates threats specific to each DFD component

**V2 Output Example**:
```json
{
  "Threat Category": "Information Disclosure",
  "Threat Name": "Database Connection String Exposure", 
  "component_name": "User Database",
  "Potential Impact": "High",
  "Likelihood": "Medium",
  "residual_risk": "Medium",
  "inherent_risk": "High"
}
```

### **Phase 2: Multi-Agent Specialized Analysis** 

Now the **three specialized agents** run **concurrently** to analyze from different perspectives:

#### **🏗️ Agent 1: Architectural Risk Agent**

**Mission**: Detect systemic, foundational flaws

**Focus Areas:**
- Single points of failure that could paralyze operations
- Architectural anti-patterns that create security blind spots  
- Missing defense-in-depth layers
- Scalability bottlenecks that enable DoS attacks
- Data flow vulnerabilities that bypass security controls
- Insecure architectural patterns (tight coupling, shared resources)
- Missing resilience patterns (circuit breakers, failover)

**Input**: 
- System documentation (first 3000 chars)
- DFD components summary  
- Existing STRIDE threats summary

**Process**: LLM analyzes with custom system prompt (customizable via API):
```
"You are an expert Enterprise Architect specializing in identifying 
systemic architectural vulnerabilities that traditional security scans miss."
```

**Output Example**:
```json
{
  "threat_id": "ARCH_001", 
  "threat_name": "Single Point of Failure in Authentication Service",
  "threat_description": "The centralized auth service creates a systemic risk where compromise or failure would disable access to all system components",
  "attack_vector": "Attacker targets single auth service to disable entire system",
  "business_impact": "Complete system unavailability affecting all users",
  "agent_source": "Architectural Risk Agent"
}
```

#### **💼 Agent 2: Business & Financial Risk Agent**

**Mission**: Connect technical threats to tangible business impact

**Focus Areas:**
- Revenue-generating processes vulnerable to cyber disruption
- Customer-facing systems whose compromise would damage trust/retention
- Operational processes whose failure would create cascading business impact
- Compliance/regulatory exposure from data breaches or system failures
- Supply chain dependencies vulnerable to cyber disruption
- Financial systems and processes at risk of fraud or manipulation
- Intellectual property and competitive advantage threats

**Process**: LLM with business-focused prompt:
```
"You are a Chief Risk Officer with expertise in quantifying 
cybersecurity threats' impact on business operations and financial performance."
```

**Output Example**:
```json
{
  "threat_name": "Customer Service Disruption Risk", 
  "business_impact": "Payment system outage could result in $50K/hour revenue loss",
  "financial_impact_range": "$100K - $2M for extended outage",
  "customer_impact": "Customer trust erosion leading to 15% churn rate",
  "regulatory_exposure": "PCI-DSS compliance violation fines up to $500K"
}
```

#### **⚖️ Agent 3: Compliance & Governance Agent**

**Mission**: View system through auditor's lens

**Focus Areas:**
- Data protection violations (GDPR, HIPAA, PCI-DSS non-compliance)
- Missing audit trails and logging for regulated data
- Insufficient access controls for sensitive information
- Lack of data retention/deletion policies
- Missing business continuity planning for regulated systems
- Inadequate change management and version control
- Absence of regular security testing and assessments
- Governance control gaps that auditors would flag

**Regulatory Frameworks Considered:**
- **GDPR**: EU data protection, consent, right to erasure
- **PCI-DSS**: Payment card data security standards
- **HIPAA**: Healthcare information protection
- **SOX**: Financial reporting controls and audit trails
- **ISO 27001**: Information security management systems

**Process**: LLM with compliance-focused prompt:
```
"You are a Chief Compliance Officer and Regulatory Audit Expert with deep 
expertise in cybersecurity compliance frameworks (GDPR, PCI-DSS, HIPAA, SOX, ISO 27001)."
```

**Output Example**:
```json
{
  "threat_name": "GDPR Data Protection Violation",
  "regulatory_framework": "GDPR", 
  "potential_penalties": "GDPR fines up to 4% of annual revenue",
  "audit_findings": "No documented consent management for PII processing",
  "mitigation_strategy": "Implement GDPR requirements: encryption, consent, right to deletion"
}
```

### **Phase 3: Threat Consolidation & Prioritization**

**Process**:
1. **Deduplication**: Remove duplicate threats with same name/component
2. **Source Tagging**: Mark each threat with its analysis source
3. **Advanced Prioritization**: Multi-factor scoring algorithm

**Advanced Prioritization Algorithm**:
- **Severity Weight**: 30% (Critical=4, High=3, Medium=2, Low=1)
- **Likelihood Weight**: 20% 
- **Business Impact Weight**: 25% (bonus for business threats)
- **Compliance Impact Weight**: 15% (bonus for compliance threats)
- **Architectural Impact Weight**: 10% (bonus for architectural threats)
- **Financial Exposure Bonus**: 1.5x multiplier if quantified financial impact exists

**Final V3 Output**: Top 50 prioritized threats with comprehensive metadata

## ⚖️ **Step 3: Threat Refinement**

Takes the raw threats from V3 and applies additional intelligence and business context.

### **Refinement Process**:

**Phase 1: Quick Deduplication**
- Creates signatures from threat name, component, and description 
- Removes exact duplicates

**Phase 2: Batch Risk Assessment** 
- Processes top 15 threats through LLM for risk scoring
- Uses prompt: *"Assess risk levels for these cybersecurity threats"*
- Returns JSON array with risk scores, priority ranks, and exploitability ratings

```
For each threat, provide:
[
    {"risk_score": "Critical|High|Medium|Low", "priority_rank": 1-5, "exploitability": "High|Medium|Low"}
]
```

**Phase 3: Business Context Enhancement**
- Takes top 5 critical/high threats
- Uses LLM to translate technical threats into business language

```
Translate these top cybersecurity threats into business risk language:
Return JSON array with business statements:
[
    {"business_risk_statement": "Clear business risk in 1-2 sentences"}
]
```

**Phase 4: Final Prioritization & Ranking**
- Sorts by risk score  
- Adds priority rankings (#1, #2, etc.)
- Assigns implementation priority (Immediate, High, Medium, Low)

## 📊 **Final Result Structure**

The complete output includes:

```json
{
  "refined_threats": [
    {
      "Threat Name": "Authentication Bypass in API Gateway",
      "component_name": "API Gateway", 
      "Potential Impact": "Critical",
      "Likelihood": "Medium",
      "risk_score": "Critical",           // From refinement
      "priority_rank": 1,                 // From V3 prioritization  
      "business_risk_statement": "API compromise could expose all customer data leading to regulatory fines and customer loss",
      "analysis_source": "architectural_agent", // V3 agent source
      "threat_class": "architectural",    // V3 classification
      "agent_source": "Architectural Risk Agent"
    }
  ],
  "threat_breakdown": {
    "technical_stride": 25,               // From V2  
    "architectural": 8,                   // From architectural agent
    "business": 5,                        // From business agent
    "compliance": 3                       // From compliance agent
  },
  "refinement_stats": {
    "original_count": 41,
    "deduplicated_count": 38,
    "final_count": 38,
    "risk_distribution": {"Critical": 5, "High": 12, "Medium": 18, "Low": 3}
  }
}
```

## 🔄 **Summary: How We Get to Threats**

1. **📄 Documents** → **🔍 DFD Components** (External entities, processes, data stores, flows)

2. **🎯 V3 Multi-Agent Generation**:
   - **V2 STRIDE Analysis** → Technical threats with context-aware risk scoring
   - **🏗️ Architectural Agent** → Systemic vulnerabilities (SPOFs, anti-patterns)  
   - **💼 Business Agent** → Financial/operational impact quantification
   - **⚖️ Compliance Agent** → Regulatory violations and audit gaps
   - **🔗 Consolidation** → Advanced multi-factor prioritization

3. **⚖️ Refinement**:
   - **Deduplication** → Remove duplicates
   - **Risk Assessment** → LLM-powered risk scoring  
   - **Business Translation** → Technical → Business language
   - **Final Ranking** → Priority order for remediation

4. **📊 Result**: Prioritized, business-contextualized threats from multiple expert perspectives

## 🎯 **Key Innovation: Multi-Agent Approach**

Instead of one AI trying to do everything, the system employs **three specialized AI agents** (architectural, business, compliance) each focusing on their expertise, then consolidating their findings for comprehensive coverage.

This approach ensures:
- **Comprehensive Coverage**: Different threat perspectives captured
- **Expert Focus**: Each agent specializes in specific risk domains
- **Business Relevance**: Technical threats translated to business impact
- **Regulatory Compliance**: Audit and compliance gaps identified
- **Prioritized Action**: Multi-factor scoring for remediation planning

## 🛠️ **Customization**

All agent prompts are **fully customizable** via the Settings API without code changes:
- Industry-specific focus (healthcare, finance, SaaS)
- Technology-specific analysis (AWS, Azure, containers)
- Compliance framework specialization (HIPAA, PCI-DSS, GDPR)
- Custom risk scoring criteria

See `CUSTOM_PROMPTS_GUIDE.md` for detailed customization instructions.

---

🎯 **Result**: A comprehensive, multi-perspective threat analysis that goes far beyond traditional STRIDE methodology to provide actionable, business-relevant security insights!