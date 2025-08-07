"""
Business Financial Risk Agent - Modular Implementation

Migrated from V3 BusinessFinancialRiskAgent with full compatibility preservation.
Connects technical threats to tangible business impact and financial risk.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.agents.base import BaseAgent, AgentMetadata, AgentCategory, ThreatOutput, AgentExecutionContext
from app.core.llm import get_llm_provider, get_system_prompt_for_step

logger = logging.getLogger(__name__)


class BusinessFinancialRiskAgent(BaseAgent):
    """
    Migrated from V3 BusinessFinancialRiskAgent
    Preserves ALL existing functionality and business impact analysis
    """
    
    def __init__(self):
        super().__init__()
        
        # Preserved V3 business impact indicators
        self.impact_indicators = {
            'revenue': ['revenue', 'sales', 'income', 'profit', 'earning'],
            'cost': ['cost', 'expense', 'budget', 'financial', 'money', 'dollar', '$'],
            'downtime': ['downtime', 'availability', 'uptime', 'sla', 'outage'],
            'reputation': ['brand', 'reputation', 'image', 'trust', 'customer'],
            'compliance': ['compliance', 'regulation', 'audit', 'legal', 'fine'],
            'competitive': ['competitive', 'market', 'advantage', 'differentiation']
        }
        
        # Preserved V3 sector-specific risks
        self.sector_risks = {
            'ecommerce': {
                'critical_components': ['payment', 'checkout', 'inventory', 'order'],
                'key_metrics': ['conversion_rate', 'cart_abandonment', 'customer_lifetime_value'],
                'peak_risks': ['black_friday', 'holiday_season', 'flash_sales']
            },
            'fintech': {
                'critical_components': ['transaction', 'payment', 'wallet', 'trading'],
                'key_metrics': ['transaction_volume', 'processing_time', 'error_rate'],
                'regulatory_focus': ['pci_dss', 'aml', 'kyc', 'sox']
            },
            'saas': {
                'critical_components': ['authentication', 'data', 'api', 'subscription'],
                'key_metrics': ['uptime', 'response_time', 'user_growth', 'churn_rate'],
                'subscription_risks': ['billing_failure', 'service_disruption']
            },
            'healthcare': {
                'critical_components': ['patient_data', 'medical_records', 'scheduling'],
                'key_metrics': ['patient_satisfaction', 'appointment_availability'],
                'regulatory_focus': ['hipaa', 'gdpr', 'patient_safety']
            }
        }
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="business_financial",
            version="3.0.0",  # Matches V3 system
            description="Connects technical threats to business impact and quantifies financial risks",
            category=AgentCategory.BUSINESS,
            priority=2,  # Runs after architectural
            requires_document=True,
            requires_components=True,
            estimated_tokens=3800,
            enabled_by_default=True,
            legacy_equivalent="business_financial_agent"
        )
    
    async def analyze(
        self,
        context: AgentExecutionContext,
        llm_provider: Any,
        db_session: Any,
        settings_service: Optional[Any] = None
    ) -> List[ThreatOutput]:
        """
        Direct migration of V3 business financial analysis
        Preserves: Business impact quantification, sector-specific risks
        """
        
        logger.info("💼 Starting business financial risk analysis (modular)")
        
        try:
            # Extract context data
            document_text = context.document_text or ""
            components = context.components or {}
            existing_threats = context.existing_threats or []
            
            # Get custom prompt or use V3 default
            custom_prompt = await self.get_prompt_template(settings_service)
            
            if not custom_prompt:
                # Use exact V3 prompt for compatibility
                fallback_prompt = "You are a Senior Business Risk Analyst and Financial Impact Assessment Expert with deep understanding of how technical vulnerabilities translate into business losses."
                custom_prompt = await get_system_prompt_for_step(
                    step_name="threat_generation",
                    agent_type="business_financial",
                    fallback_prompt=fallback_prompt,
                    db_session=db_session
                ) or fallback_prompt
            
            # Detect business context and sector
            business_context = self._extract_business_context(document_text)
            sector_type = self._detect_business_sector(document_text, components)
            
            # Prepare V3-compatible summaries
            components_summary = self._prepare_business_components_summary(components)
            threats_impact_summary = self._prepare_business_threats_summary(existing_threats)
            
            # Create V3-compatible business analysis prompt
            business_prompt = f"""{custom_prompt}

SYSTEM DOCUMENTATION:
{document_text[:7000]}

BUSINESS CONTEXT DETECTED:
{business_context}

BUSINESS SECTOR: {sector_type}

COMPONENTS FOR BUSINESS IMPACT ANALYSIS:
{components_summary}

EXISTING TECHNICAL THREATS (for business impact analysis):
{threats_impact_summary}

MISSION: You are conducting a Business Impact Assessment (BIA) from a CFO and business continuity perspective. Focus on translating technical vulnerabilities into quantifiable business risks.

ANALYZE THE FOLLOWING BUSINESS DIMENSIONS:
1. Revenue Impact - Direct and indirect revenue loss scenarios
2. Operational Costs - Incident response, recovery, and remediation costs
3. Reputation & Brand - Customer trust and market position risks
4. Regulatory & Compliance - Fines, penalties, and legal exposure
5. Competitive Position - Market advantage and differentiation risks
6. Customer Impact - User experience and customer retention

BUSINESS RISK ASSESSMENT FRAMEWORK:
- Financial Exposure: Quantify potential losses in business terms
- Time-to-Impact: How quickly the threat materializes into business loss
- Recovery Cost: Cost to restore operations and reputation
- Opportunity Cost: Lost business during incident and recovery

OUTPUT FORMAT: Generate business-focused threats as a JSON array with this EXACT structure:
[
  {{
    "Threat Name": "Payment System Failure Leading to Revenue Loss",
    "Description": "If the payment processing system experiences downtime during peak shopping hours, the business could lose significant revenue from abandoned transactions and customer frustration.",
    "STRIDE Category": "Denial of Service",
    "Affected Component": "payment-processor",
    "Potential Impact": "Critical",
    "Likelihood": "Medium", 
    "Suggested Mitigation": "Implement redundant payment providers with automatic failover. Establish revenue protection SLAs and real-time monitoring with instant escalation for payment system issues.",
    "threat_class": "business",
    "financial_exposure": "High - Estimated $50K-500K revenue loss per hour of downtime",
    "business_impact": "Direct revenue loss, customer acquisition cost increase, potential market share erosion",
    "regulatory_implications": ["PCI DSS compliance risk", "Consumer protection regulations"],
    "priority_score": 8.7
  }}
]

IMPORTANT:
- Quantify financial impact in business terms (revenue, costs, fines)
- Consider cascading business effects and opportunity costs
- Include customer and stakeholder impact assessment
- Focus on business continuity and competitive implications
- Output valid JSON only, no markdown or explanations"""
            
            # Execute LLM call with V3 parameters
            response = await llm_provider.generate(
                prompt=business_prompt,
                temperature=0.7,
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
                        agent_name="business_financial",
                        confidence=0.82
                    )
                    # Add business-specific metadata
                    threat_output.threat_class = "business"
                    threats.append(threat_output)
                    
                except Exception as e:
                    logger.warning(f"Failed to create business threat output {i}: {e}")
                    continue
            
            logger.info(f"✅ Business financial analysis complete: {len(threats)} threats identified")
            return threats
            
        except Exception as e:
            logger.error(f"Business financial agent analysis failed: {e}")
            return []
    
    def _extract_business_context(self, document_text: str) -> str:
        """Extract business context from document"""
        try:
            context_indicators = []
            
            # Check for business impact indicators
            for category, keywords in self.impact_indicators.items():
                for keyword in keywords:
                    if keyword.lower() in document_text.lower():
                        context_indicators.append(f"{category.title()} concerns detected")
                        break
            
            # Look for business metrics
            business_metrics = []
            metric_patterns = ['sla', 'kpi', 'rto', 'rpo', 'mttr', 'uptime', '%']
            for pattern in metric_patterns:
                if pattern in document_text.lower():
                    business_metrics.append(pattern.upper())
            
            context_parts = []
            if context_indicators:
                context_parts.append("Business Impact Areas: " + ", ".join(context_indicators))
            if business_metrics:
                context_parts.append("Business Metrics Mentioned: " + ", ".join(business_metrics))
            
            return "\n".join(context_parts) if context_parts else "General business system - no specific indicators detected"
            
        except Exception as e:
            logger.warning(f"Error extracting business context: {e}")
            return "Business context analysis unavailable"
    
    def _detect_business_sector(self, document_text: str, components: Dict[str, Any]) -> str:
        """Detect business sector from document and components"""
        try:
            text_lower = document_text.lower()
            
            # Check for sector indicators in document
            for sector, indicators in self.sector_risks.items():
                for component in indicators.get('critical_components', []):
                    if component in text_lower:
                        return sector.title()
            
            # Check component names for sector indicators
            all_components = []
            for comp_list in components.values():
                if isinstance(comp_list, list):
                    for comp in comp_list:
                        comp_name = comp.get('name', '') if isinstance(comp, dict) else str(comp)
                        all_components.append(comp_name.lower())
            
            component_text = " ".join(all_components)
            
            for sector, indicators in self.sector_risks.items():
                for component in indicators.get('critical_components', []):
                    if component in component_text:
                        return sector.title()
            
            return "General Business"
            
        except Exception as e:
            logger.warning(f"Error detecting business sector: {e}")
            return "Unknown"
    
    def _prepare_business_components_summary(self, components: Dict[str, Any]) -> str:
        """Prepare business-focused components summary"""
        try:
            summary_parts = []
            
            processes = components.get('processes', [])
            data_stores = components.get('assets', []) or components.get('data_stores', [])
            
            # Focus on business-critical components
            business_critical = []
            
            for proc in processes[:15]:
                name = proc.get('name', 'Unknown') if isinstance(proc, dict) else str(proc)
                desc = proc.get('description', '') if isinstance(proc, dict) else ''
                
                # Identify business-critical processes
                critical_indicators = ['payment', 'order', 'transaction', 'user', 'customer', 'auth', 'billing']
                is_critical = any(indicator in name.lower() or indicator in desc.lower() for indicator in critical_indicators)
                
                if is_critical:
                    business_critical.append(f"🔥 {name} (BUSINESS CRITICAL)")
                else:
                    business_critical.append(f"   {name}")
            
            if business_critical:
                summary_parts.append("BUSINESS PROCESSES:")
                summary_parts.extend(business_critical)
            
            # Focus on data stores with business value
            business_data = []
            for store in data_stores[:10]:
                name = store.get('name', 'Unknown') if isinstance(store, dict) else str(store)
                
                value_indicators = ['customer', 'payment', 'transaction', 'user', 'order', 'product', 'financial']
                is_valuable = any(indicator in name.lower() for indicator in value_indicators)
                
                if is_valuable:
                    business_data.append(f"💰 {name} (HIGH BUSINESS VALUE)")
                else:
                    business_data.append(f"   {name}")
            
            if business_data:
                summary_parts.append("\nBUSINESS DATA:")
                summary_parts.extend(business_data)
            
            return "\n".join(summary_parts) if summary_parts else "No business-critical components identified"
            
        except Exception as e:
            logger.warning(f"Error preparing business components summary: {e}")
            return str(components)[:800]
    
    def _prepare_business_threats_summary(self, existing_threats: List[Dict]) -> str:
        """Prepare business-focused threats summary"""
        try:
            if not existing_threats:
                return "No existing threats for business impact analysis"
            
            summary_parts = []
            high_impact_threats = []
            
            for threat in existing_threats:
                name = threat.get('Threat Name', 'Unknown Threat')
                impact = threat.get('Potential Impact', 'Unknown')
                component = threat.get('Affected Component', 'Unknown')
                
                # Prioritize high-impact threats for business analysis
                if impact in ['Critical', 'High']:
                    high_impact_threats.append(f"  🚨 {name} (Impact: {impact}, Component: {component})")
                else:
                    high_impact_threats.append(f"     {name} (Impact: {impact}, Component: {component})")
            
            summary_parts.append(f"EXISTING THREATS FOR BUSINESS IMPACT ANALYSIS ({len(existing_threats)}):")
            summary_parts.extend(high_impact_threats[:10])
            
            if len(existing_threats) > 10:
                summary_parts.append(f"     ... and {len(existing_threats) - 10} additional threats")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.warning(f"Error preparing business threats summary: {e}")
            return f"Existing threats count: {len(existing_threats)}"