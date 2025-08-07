"""
Compliance Governance Agent - Modular Implementation

Migrated from V3 ComplianceGovernanceAgent with full compatibility preservation.
Views system through auditor's lens and identifies regulatory compliance gaps.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.agents.base import BaseAgent, AgentMetadata, AgentCategory, ThreatOutput, AgentExecutionContext
from app.core.llm import get_llm_provider, get_system_prompt_for_step

logger = logging.getLogger(__name__)


class ComplianceGovernanceAgent(BaseAgent):
    """
    Migrated from V3 ComplianceGovernanceAgent  
    Preserves ALL existing functionality and regulatory analysis
    """
    
    def __init__(self):
        super().__init__()
        
        # Preserved V3 compliance frameworks
        self.compliance_frameworks = {
            'gdpr': {
                'keywords': ['gdpr', 'personal data', 'eu', 'privacy', 'consent', 'data subject'],
                'critical_controls': ['data encryption', 'access logging', 'data retention', 'consent management'],
                'penalties': 'Up to 4% of annual revenue or €20M',
                'key_requirements': ['Privacy by Design', 'Data Protection Impact Assessment', 'Right to Erasure']
            },
            'hipaa': {
                'keywords': ['hipaa', 'phi', 'healthcare', 'medical', 'patient', 'health information'],
                'critical_controls': ['access controls', 'audit logs', 'encryption', 'business associate agreements'],
                'penalties': 'Up to $1.5M per incident',
                'key_requirements': ['Administrative Safeguards', 'Physical Safeguards', 'Technical Safeguards']
            },
            'pci_dss': {
                'keywords': ['pci', 'payment', 'card', 'transaction', 'cardholder', 'payment processor'],
                'critical_controls': ['network security', 'encryption', 'access control', 'monitoring'],
                'penalties': 'Fines + loss of payment processing',
                'key_requirements': ['Secure Network', 'Protect Cardholder Data', 'Regular Testing']
            },
            'sox': {
                'keywords': ['sox', 'sarbanes', 'financial', 'public company', 'audit', 'controls'],
                'critical_controls': ['segregation of duties', 'change management', 'access reviews'],
                'penalties': 'Up to $5M + imprisonment',
                'key_requirements': ['Internal Controls', 'Management Assessment', 'Auditor Attestation']
            },
            'iso27001': {
                'keywords': ['iso', '27001', 'information security', 'isms', 'risk management'],
                'critical_controls': ['risk assessment', 'security policies', 'incident management'],
                'penalties': 'Certification loss + reputation damage',
                'key_requirements': ['ISMS Implementation', 'Continuous Improvement', 'Risk-based Approach']
            },
            'nist': {
                'keywords': ['nist', 'cybersecurity framework', 'federal', 'government'],
                'critical_controls': ['identify', 'protect', 'detect', 'respond', 'recover'],
                'penalties': 'Contract loss + regulatory action',
                'key_requirements': ['Cybersecurity Framework', 'Risk Management', 'Continuous Monitoring']
            }
        }
        
        # Preserved V3 governance areas
        self.governance_areas = {
            'data_governance': {
                'focus': 'Data classification, retention, and lifecycle management',
                'common_gaps': ['unclassified data', 'no retention policy', 'unclear ownership']
            },
            'access_governance': {
                'focus': 'Identity and access management, privilege escalation',
                'common_gaps': ['excessive privileges', 'no access reviews', 'shared accounts']
            },
            'change_governance': {
                'focus': 'Change management, deployment controls, rollback procedures',
                'common_gaps': ['unauthorized changes', 'no approval process', 'no testing']
            },
            'vendor_governance': {
                'focus': 'Third-party risk, vendor assessments, contract management',
                'common_gaps': ['no vendor assessment', 'unclear sla', 'data sharing risks']
            }
        }
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="compliance_governance",
            version="3.0.0",  # Matches V3 system
            description="Views system through auditor's lens and identifies regulatory compliance gaps",
            category=AgentCategory.COMPLIANCE,
            priority=3,  # Runs last like in V3
            requires_document=True,
            requires_components=True,
            estimated_tokens=4000,
            enabled_by_default=True,
            legacy_equivalent="compliance_governance_agent"
        )
    
    async def analyze(
        self,
        context: AgentExecutionContext,
        llm_provider: Any,
        db_session: Any,
        settings_service: Optional[Any] = None
    ) -> List[ThreatOutput]:
        """
        Direct migration of V3 compliance governance analysis
        Preserves: Regulatory framework analysis, governance gap detection
        """
        
        logger.info("⚖️ Starting compliance governance analysis (modular)")
        
        try:
            # Extract context data
            document_text = context.document_text or ""
            components = context.components or {}
            existing_threats = context.existing_threats or []
            
            # Get custom prompt or use V3 default
            custom_prompt = await self.get_prompt_template(settings_service)
            
            if not custom_prompt:
                # Use exact V3 prompt for compatibility
                fallback_prompt = "You are a Chief Compliance Officer and Senior Auditor with expertise in regulatory frameworks, governance controls, and compliance risk assessment."
                custom_prompt = await get_system_prompt_for_step(
                    step_name="threat_generation",
                    agent_type="compliance_governance",
                    fallback_prompt=fallback_prompt,
                    db_session=db_session
                ) or fallback_prompt
            
            # Detect applicable compliance frameworks
            applicable_frameworks = self._detect_compliance_frameworks(document_text, components)
            governance_gaps = self._identify_governance_gaps(document_text, components)
            
            # Prepare V3-compatible summaries
            compliance_summary = self._prepare_compliance_summary(applicable_frameworks)
            governance_summary = self._prepare_governance_summary(governance_gaps)
            components_summary = self._prepare_compliance_components_summary(components)
            
            # Create V3-compatible compliance analysis prompt
            compliance_prompt = f"""{custom_prompt}

SYSTEM DOCUMENTATION:
{document_text[:6000]}

APPLICABLE COMPLIANCE FRAMEWORKS DETECTED:
{compliance_summary}

GOVERNANCE AREAS REQUIRING ATTENTION:
{governance_summary}

COMPONENTS FOR COMPLIANCE REVIEW:
{components_summary}

EXISTING THREATS FOR COMPLIANCE IMPACT:
{self._prepare_compliance_threats_summary(existing_threats)}

MISSION: You are conducting a comprehensive compliance and governance assessment. View this system through an auditor's lens and identify gaps that could result in regulatory violations, failed audits, or governance failures.

ANALYZE THE FOLLOWING COMPLIANCE DIMENSIONS:
1. Data Protection & Privacy - GDPR, CCPA, HIPAA compliance gaps
2. Financial Controls - SOX, banking regulations, audit trail requirements  
3. Industry Standards - PCI DSS, ISO 27001, NIST framework alignment
4. Governance Controls - Access management, change control, segregation of duties
5. Documentation & Evidence - Policies, procedures, audit trails
6. Incident Response - Breach notification, regulatory reporting requirements

COMPLIANCE RISK ASSESSMENT FRAMEWORK:
- Regulatory Exposure: Specific regulations at risk of violation
- Audit Impact: Likelihood of audit findings or failures
- Penalty Risk: Potential fines, sanctions, or enforcement actions
- Remediation Urgency: Time-sensitive compliance requirements

OUTPUT FORMAT: Generate compliance-focused threats as a JSON array with this EXACT structure:
[
  {{
    "Threat Name": "GDPR Data Subject Rights Violation Risk",
    "Description": "The system lacks automated mechanisms to respond to data subject requests (erasure, portability, rectification), potentially leading to GDPR violations if requests cannot be fulfilled within the 30-day requirement.",
    "STRIDE Category": "Information Disclosure",
    "Affected Component": "user-data-store", 
    "Potential Impact": "High",
    "Likelihood": "Medium",
    "Suggested Mitigation": "Implement automated data subject request handling system with audit trails. Establish clear data mapping and retention policies. Train staff on GDPR response procedures.",
    "threat_class": "compliance",
    "regulatory_implications": ["GDPR Article 12-22 violations", "Up to 4% annual revenue fine", "Data Protection Authority investigation"],
    "business_impact": "Regulatory fines, reputational damage, operational disruption from audits",
    "priority_score": 8.1
  }}
]

IMPORTANT:
- Cite specific regulatory requirements and standards
- Quantify compliance risk and potential penalties
- Consider audit and examination perspectives
- Include remediation timelines and regulatory deadlines
- Focus on systemic compliance gaps, not individual vulnerabilities
- Output valid JSON only, no markdown or explanations"""
            
            # Execute LLM call with V3 parameters
            response = await llm_provider.generate(
                prompt=compliance_prompt,
                temperature=0.6,  # Lower temperature for compliance (more conservative)
                max_tokens=4500
            )
            
            # Parse response using inherited method
            threat_dicts = self._parse_llm_response(response.content)
            
            # Convert to ThreatOutput objects
            threats = []
            for i, threat_dict in enumerate(threat_dicts):
                try:
                    threat_output = self._create_threat_output(
                        threat_dict=threat_dict,
                        agent_name="compliance_governance",
                        confidence=0.88  # High confidence for regulatory analysis
                    )
                    # Add compliance-specific metadata
                    threat_output.threat_class = "compliance"
                    threats.append(threat_output)
                    
                except Exception as e:
                    logger.warning(f"Failed to create compliance threat output {i}: {e}")
                    continue
            
            logger.info(f"✅ Compliance governance analysis complete: {len(threats)} threats identified")
            return threats
            
        except Exception as e:
            logger.error(f"Compliance governance agent analysis failed: {e}")
            return []
    
    def _detect_compliance_frameworks(self, document_text: str, components: Dict[str, Any]) -> List[str]:
        """Detect applicable compliance frameworks"""
        try:
            text_lower = document_text.lower()
            applicable = []
            
            for framework, details in self.compliance_frameworks.items():
                # Check for framework keywords in document
                for keyword in details['keywords']:
                    if keyword in text_lower:
                        applicable.append(framework.upper())
                        break
            
            # Check component names for compliance indicators  
            all_component_text = ""
            for comp_list in components.values():
                if isinstance(comp_list, list):
                    for comp in comp_list:
                        comp_name = comp.get('name', '') if isinstance(comp, dict) else str(comp)
                        comp_desc = comp.get('description', '') if isinstance(comp, dict) else ''
                        all_component_text += f" {comp_name} {comp_desc}".lower()
            
            for framework, details in self.compliance_frameworks.items():
                if framework.upper() not in applicable:
                    for keyword in details['keywords']:
                        if keyword in all_component_text:
                            applicable.append(framework.upper())
                            break
            
            return applicable if applicable else ["General Compliance"]
            
        except Exception as e:
            logger.warning(f"Error detecting compliance frameworks: {e}")
            return ["General Compliance"]
    
    def _identify_governance_gaps(self, document_text: str, components: Dict[str, Any]) -> List[str]:
        """Identify potential governance gaps"""
        try:
            text_lower = document_text.lower()
            gaps = []
            
            for area, details in self.governance_areas.items():
                for gap in details['common_gaps']:
                    # Look for indicators of this gap
                    gap_indicators = gap.split()
                    if any(indicator in text_lower for indicator in gap_indicators):
                        gaps.append(f"{area}: {gap}")
            
            return gaps if gaps else ["General governance review needed"]
            
        except Exception as e:
            logger.warning(f"Error identifying governance gaps: {e}")
            return ["Governance analysis unavailable"]
    
    def _prepare_compliance_summary(self, frameworks: List[str]) -> str:
        """Prepare compliance frameworks summary"""
        try:
            if not frameworks or frameworks == ["General Compliance"]:
                return "No specific compliance frameworks detected - general compliance review applies"
            
            summary_parts = []
            for framework in frameworks:
                fw_key = framework.lower()
                if fw_key in self.compliance_frameworks:
                    details = self.compliance_frameworks[fw_key]
                    summary_parts.append(
                        f"{framework}: {details['penalties']} - Key: {', '.join(details['key_requirements'])}"
                    )
                else:
                    summary_parts.append(f"{framework}: Framework detected")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.warning(f"Error preparing compliance summary: {e}")
            return "Compliance summary unavailable"
    
    def _prepare_governance_summary(self, gaps: List[str]) -> str:
        """Prepare governance gaps summary"""
        try:
            if not gaps or gaps == ["General governance review needed"]:
                return "General governance review - no specific gaps identified"
            
            return "\n".join([f"- {gap}" for gap in gaps[:10]])
            
        except Exception as e:
            logger.warning(f"Error preparing governance summary: {e}")
            return "Governance summary unavailable"
    
    def _prepare_compliance_components_summary(self, components: Dict[str, Any]) -> str:
        """Prepare compliance-focused components summary"""
        try:
            summary_parts = []
            
            # Focus on compliance-sensitive components
            processes = components.get('processes', [])
            data_stores = components.get('assets', []) or components.get('data_stores', [])
            external_entities = components.get('external_entities', [])
            
            # Identify high-risk components
            sensitive_data = []
            for store in data_stores[:10]:
                name = store.get('name', 'Unknown') if isinstance(store, dict) else str(store)
                desc = store.get('description', '') if isinstance(store, dict) else ''
                
                # Check for sensitive data indicators
                sensitive_indicators = ['personal', 'payment', 'financial', 'medical', 'customer', 'user']
                is_sensitive = any(indicator in f"{name} {desc}".lower() for indicator in sensitive_indicators)
                
                if is_sensitive:
                    sensitive_data.append(f"🔒 {name} (SENSITIVE DATA)")
                else:
                    sensitive_data.append(f"   {name}")
            
            if sensitive_data:
                summary_parts.append("SENSITIVE DATA STORES:")
                summary_parts.extend(sensitive_data)
            
            # Identify external connections (compliance risk)
            external_risks = []
            for entity in external_entities[:8]:
                name = entity.get('name', 'Unknown') if isinstance(entity, dict) else str(entity)
                external_risks.append(f"🌐 {name}")
            
            if external_risks:
                summary_parts.append("\nEXTERNAL CONNECTIONS (Compliance Review):")
                summary_parts.extend(external_risks)
            
            return "\n".join(summary_parts) if summary_parts else "No compliance-sensitive components identified"
            
        except Exception as e:
            logger.warning(f"Error preparing compliance components summary: {e}")
            return str(components)[:800]
    
    def _prepare_compliance_threats_summary(self, existing_threats: List[Dict]) -> str:
        """Prepare compliance-focused threats summary"""
        try:
            if not existing_threats:
                return "No existing threats for compliance impact analysis"
            
            summary_parts = []
            compliance_relevant = []
            
            for threat in existing_threats:
                name = threat.get('Threat Name', 'Unknown Threat')
                component = threat.get('Affected Component', 'Unknown')
                
                # Check if threat has compliance implications
                threat_text = f"{name} {component}".lower()
                compliance_keywords = ['data', 'access', 'auth', 'log', 'audit', 'privacy', 'breach']
                
                is_compliance_relevant = any(keyword in threat_text for keyword in compliance_keywords)
                
                if is_compliance_relevant:
                    compliance_relevant.append(f"  ⚖️ {name} (Component: {component}) - COMPLIANCE IMPACT")
                else:
                    compliance_relevant.append(f"     {name} (Component: {component})")
            
            summary_parts.append(f"EXISTING THREATS WITH COMPLIANCE IMPLICATIONS ({len(existing_threats)}):")
            summary_parts.extend(compliance_relevant[:8])
            
            if len(existing_threats) > 8:
                summary_parts.append(f"     ... and {len(existing_threats) - 8} additional threats")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.warning(f"Error preparing compliance threats summary: {e}")
            return f"Existing threats count: {len(existing_threats)}"