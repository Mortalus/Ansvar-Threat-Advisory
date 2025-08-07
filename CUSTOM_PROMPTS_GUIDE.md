# 🎯 Custom LLM Prompts Guide

This guide explains how to customize the system prompts for every LLM step in the Threat Modeling Pipeline, allowing you to fine-tune the AI analysis without editing code.

## 🔧 Overview

The system now supports **customizable system prompts** for all LLM-powered steps:
- **DFD Extraction** - Data Flow Diagram extraction from documents  
- **DFD Validation** - Quality assessment of extracted DFDs
- **Threat Generation** - Multi-agent threat analysis (V3)
  - Architectural Risk Agent
  - Business & Financial Risk Agent  
  - Compliance & Governance Agent
- **Threat Refinement** - Risk assessment and prioritization
- **Attack Path Analysis** - Attack vector identification

## 🚀 Quick Start

### 1. Initialize Default Prompts
First, initialize the default prompt templates:

```bash
curl -X POST http://localhost:8000/api/settings/prompts/initialize-defaults
```

### 2. View Available Steps
See all available LLM steps and agents:

```bash
curl http://localhost:8000/api/settings/llm-steps
```

### 3. List Current Prompts
View all current prompt templates:

```bash
curl http://localhost:8000/api/settings/prompts
```

## 📝 Managing Custom Prompts

### View Active Prompt for a Step
Get the currently active prompt for a specific step:

```bash
# Main threat generation step
curl http://localhost:8000/api/settings/prompts/active/threat_generation

# Specific agent
curl "http://localhost:8000/api/settings/prompts/active/threat_generation?agent_type=architectural_risk"
```

### Create Custom Prompt
Create a new custom prompt template:

```bash
curl -X POST http://localhost:8000/api/settings/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "step_name": "threat_generation",
    "agent_type": "architectural_risk", 
    "system_prompt": "You are a Senior Cloud Security Architect with 15+ years experience specializing in AWS, Azure, and GCP security patterns. Focus on cloud-native threats and container security.",
    "description": "Custom prompt for cloud-focused architectural analysis",
    "is_active": true
  }'
```

### Update Existing Prompt
Modify an existing prompt template:

```bash
curl -X PUT http://localhost:8000/api/settings/prompts/{template_id} \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt": "You are an expert in Zero Trust Architecture and micro-segmentation strategies...",
    "description": "Updated prompt focusing on Zero Trust principles"
  }'
```

## 🎭 Agent-Specific Customization

### Architectural Risk Agent
**Step:** `threat_generation`, **Agent:** `architectural_risk`

**Example Custom Prompt:**
```json
{
  "system_prompt": "You are a Principal Solutions Architect at AWS with deep expertise in Well-Architected Framework security pillar. Focus on identifying architectural patterns that violate AWS security best practices, emphasizing IAM, network segmentation, and data protection patterns.",
  "description": "AWS-focused architectural risk analysis"
}
```

### Business Financial Agent
**Step:** `threat_generation`, **Agent:** `business_financial`

**Example Custom Prompt:**
```json
{
  "system_prompt": "You are a Chief Financial Officer with cybersecurity risk quantification expertise. Translate technical threats into precise financial impact statements using industry-standard methodologies. Reference specific regulatory costs (SOX, PCI-DSS fines) and calculate downtime costs based on revenue metrics.",
  "description": "Finance-focused business impact analysis with quantified costs"
}
```

### Compliance Governance Agent
**Step:** `threat_generation`, **Agent:** `compliance_governance`

**Example Custom Prompt:**
```json
{
  "system_prompt": "You are a Senior Compliance Manager specializing in healthcare HIPAA requirements. Focus exclusively on PHI protection, BAA compliance, access controls for medical data, and healthcare-specific audit requirements. Ignore non-healthcare frameworks unless explicitly mentioned.",
  "description": "Healthcare HIPAA-focused compliance analysis"
}
```

## 🏭 Industry-Specific Examples

### Financial Services
```json
{
  "step_name": "threat_generation",
  "agent_type": "compliance_governance",
  "system_prompt": "You are a PCI-DSS Qualified Security Assessor (QSA) with expertise in banking regulations. Focus on cardholder data protection, PCI-DSS requirements, SOX controls for financial reporting, and regulatory requirements from OCC, FDIC, and Federal Reserve.",
  "description": "Financial services regulatory compliance focus"
}
```

### SaaS Applications
```json
{
  "step_name": "threat_generation", 
  "agent_type": "architectural_risk",
  "system_prompt": "You are a SaaS Security Architect specializing in multi-tenant applications. Focus on tenant isolation, API security, data segregation between customers, and SaaS-specific attack patterns like tenant enumeration and privilege escalation across organizations.",
  "description": "Multi-tenant SaaS security architecture focus"
}
```

## 📊 API Reference

### Base URL
All endpoints are prefixed with: `http://localhost:8000/api/settings`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/llm-steps` | List available LLM steps and agents |
| GET | `/prompts` | List all prompt templates |
| GET | `/prompts/{id}` | Get specific prompt template |
| GET | `/prompts/active/{step_name}` | Get active prompt for step |
| POST | `/prompts` | Create new prompt template |
| PUT | `/prompts/{id}` | Update prompt template |
| DELETE | `/prompts/{id}` | Delete prompt template |
| POST | `/prompts/initialize-defaults` | Initialize default templates |

### Request Schema
```json
{
  "step_name": "threat_generation",           // Required: LLM step name
  "agent_type": "architectural_risk",         // Optional: Agent type  
  "system_prompt": "Your custom prompt...",   // Required: Prompt text
  "description": "What this prompt does",     // Required: Description
  "is_active": true                          // Optional: Default true
}
```

## 🔄 How It Works

1. **Fallback System**: If no custom prompt exists, the system uses built-in defaults
2. **Single Active**: Only one prompt template per step/agent can be active at a time
3. **Real-time**: Changes take effect immediately for new analyses
4. **Database Storage**: All custom prompts are stored in the database and persist across restarts

## ⚠️ Best Practices

1. **Test Gradually**: Start by customizing one agent, test thoroughly before modifying others
2. **Keep Focused**: Maintain the agent's core mission while adding your specialization
3. **Preserve Format**: Keep the JSON output format requirements in your prompts
4. **Version Control**: Document your prompt changes and reasons
5. **Monitor Results**: Check that custom prompts produce expected threat quality

## 🛠️ Troubleshooting

**Q: My custom prompt isn't being used**
- Verify the prompt is marked as `is_active: true`
- Check the step_name and agent_type match exactly
- Restart may be needed if database changes aren't reflected

**Q: Threats seem lower quality after customization**  
- Compare with default prompts to see what elements were lost
- Ensure output format requirements are preserved
- Consider if the customization is too narrow for your use cases

**Q: Getting JSON parsing errors**
- Verify your custom prompt maintains the required JSON output format
- Check that the prompt doesn't conflict with the structured output requirements

## 📈 Advanced Usage

### Environment-Specific Prompts
Create different prompts for development, staging, and production environments by swapping active templates.

### A/B Testing Prompts  
Create multiple prompt templates and switch between them to compare threat analysis quality.

### Domain Expert Integration
Work with subject matter experts to create highly specialized prompts for your specific industry or technology stack.

---

🎯 **Result**: You now have complete control over how the AI analyzes your systems, without touching any code!