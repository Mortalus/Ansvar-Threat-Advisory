"""
Data Flow Analysis Agent

Analyzes data flows and trust boundaries in the system architecture.
Focuses on data movement, storage, and processing security.
"""

import logging
from typing import List, Dict, Any
from ..base import BaseAgent, AgentMetadata, AgentCategory, AgentExecutionContext, ThreatOutput

logger = logging.getLogger(__name__)


class DataFlowAnalysisAgent(BaseAgent):
    """
    Agent specialized in analyzing data flows and trust boundaries.
    Identifies threats related to data movement, storage, and processing.
    """
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="data_flow_analysis",
            version="1.0.0",
            description="Analyzes data flows, trust boundaries, and data security threats",
            category=AgentCategory.ARCHITECTURE,
            priority=25,  # Early execution to map data flows
            requires_document=True,
            requires_components=True,
            estimated_tokens=3500,
            enabled_by_default=True,
            legacy_equivalent=None
        )
    
    async def analyze(
        self,
        context: AgentExecutionContext,
        llm_provider: Any,
        db_session: Any,
        settings_service: Any = None
    ) -> List[ThreatOutput]:
        """
        Analyze data flows and identify security threats.
        """
        metadata = self.get_metadata()
        
        # Build prompt for data flow analysis
        prompt = self._build_analysis_prompt(context)
        
        try:
            # Get LLM response
            response = await llm_provider.generate(prompt)
            
            # Parse response to threats
            threat_dicts = self._parse_llm_response(response)
            
            # Convert to ThreatOutput objects
            threats = []
            for threat_dict in threat_dicts:
                threats.append(
                    self._create_threat_output(
                        threat_dict,
                        metadata.name,
                        confidence=0.85
                    )
                )
            
            logger.info(f"Data flow analysis identified {len(threats)} threats")
            return threats
            
        except Exception as e:
            logger.error(f"Data flow analysis failed: {e}")
            # Return fallback threats
            return self._get_fallback_threats(context, metadata.name)
    
    def _build_analysis_prompt(self, context: AgentExecutionContext) -> str:
        """Build prompt for data flow threat analysis."""
        
        components_text = ""
        if context.components:
            if isinstance(context.components, list):
                comp_names = [c.get("name", "Unknown") if isinstance(c, dict) else str(c) 
                             for c in context.components]
                components_text = ", ".join(comp_names)
            else:
                components_text = str(context.components)
        
        return f"""
        Analyze the following system architecture for DATA FLOW SECURITY THREATS.
        Focus on:
        - Data in transit (network communication, API calls)
        - Data at rest (storage, databases, caches)
        - Data processing (transformations, aggregations)
        - Trust boundaries and data crossing zones
        - Input validation and output encoding
        - Sensitive data exposure risks
        
        System Description:
        {context.document_text}
        
        Components: {components_text}
        
        Identify threats specifically related to data flows.
        
        Return a JSON array with threats in this exact format:
        [{{
            "Threat Name": "Unencrypted Data Transmission",
            "Description": "API endpoints transmit sensitive data without TLS encryption",
            "STRIDE Category": "Information Disclosure",
            "Affected Component": "API Gateway",
            "Potential Impact": "High - Exposure of customer PII and payment data",
            "Likelihood": "Medium",
            "Suggested Mitigation": "Enforce TLS 1.3+ for all API communications"
        }}]
        
        Focus on realistic, specific data flow threats.
        Include 3-5 high-priority threats.
        """
    
    def _get_fallback_threats(self, context: AgentExecutionContext, agent_name: str) -> List[ThreatOutput]:
        """Generate fallback threats when LLM is unavailable."""
        
        fallback_threats = [
            {
                "Threat Name": "Unencrypted Data in Transit",
                "Description": "Sensitive data may be transmitted without encryption between components",
                "STRIDE Category": "Information Disclosure",
                "Affected Component": "Network Communication",
                "Potential Impact": "High - Exposure of sensitive information",
                "Likelihood": "Medium",
                "Suggested Mitigation": "Implement end-to-end encryption for all data transmissions"
            },
            {
                "Threat Name": "Insufficient Input Validation",
                "Description": "Data inputs may not be properly validated before processing",
                "STRIDE Category": "Tampering",
                "Affected Component": "Data Processing Layer",
                "Potential Impact": "High - Data corruption or injection attacks",
                "Likelihood": "High",
                "Suggested Mitigation": "Implement comprehensive input validation and sanitization"
            },
            {
                "Threat Name": "Data Leakage Through Logs",
                "Description": "Sensitive data may be exposed through application logs",
                "STRIDE Category": "Information Disclosure",
                "Affected Component": "Logging System",
                "Potential Impact": "Medium - Unintended data exposure",
                "Likelihood": "Medium",
                "Suggested Mitigation": "Implement log sanitization and sensitive data masking"
            }
        ]
        
        return [
            self._create_threat_output(threat, agent_name, confidence=0.7)
            for threat in fallback_threats
        ]