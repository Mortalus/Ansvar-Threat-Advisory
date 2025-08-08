"""
Document Analysis Agent

Analyzes uploaded documents to extract architectural information
and identify potential security concerns at the document level.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional

from ..base import BaseAgent, AgentMetadata, AgentCategory, ThreatOutput, AgentExecutionContext

logger = logging.getLogger(__name__)


class DocumentAnalysisAgent(BaseAgent):
    """
    Agent that analyzes document content for architectural patterns,
    data flows, and document-level security considerations.
    """
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="document_analysis",
            version="1.0.0",
            description="Document Analysis Agent",
            category=AgentCategory.ARCHITECTURE,
            priority=10,  # Run early in the workflow
            requires_document=True,
            requires_components=False,
            estimated_tokens=2000,
            enabled_by_default=True,
            legacy_equivalent=None
        )
    
    async def analyze(
        self,
        context: AgentExecutionContext,
        llm_provider: Any,
        db_session: Any,
        settings_service: Optional[Any] = None
    ) -> List[ThreatOutput]:
        """
        Analyze document content for architectural patterns and security concerns
        """
        logger.info("Starting document analysis...")
        
        if not context.document_text:
            logger.warning("No document content provided")
            return []
        
        try:
            # Get custom prompt if available
            custom_prompt = await self.get_prompt_template(settings_service)
            
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self._get_default_prompt()
            
            # Prepare the analysis prompt
            analysis_prompt = prompt.format(
                document_content=context.document_text[:4000],  # Limit content to avoid token limits
                additional_context=self._get_document_analysis_context()
            )
            
            logger.info("Sending document analysis request to LLM...")
            
            # Call LLM service
            response = await llm_provider.generate_completion(
                prompt=analysis_prompt,
                max_tokens=3000,
                temperature=0.3
            )
            
            if not response or not response.get('content'):
                logger.warning("Empty response from LLM")
                return []
            
            # Parse the response
            threat_dicts = self._parse_llm_response(response['content'])
            
            # Convert to ThreatOutput objects
            threats = []
            for i, threat_dict in enumerate(threat_dicts):
                try:
                    threat = self._create_threat_output(
                        threat_dict=threat_dict,
                        agent_name=self.get_metadata().name,
                        confidence=0.75  # Document-level analysis has moderate confidence
                    )
                    threats.append(threat)
                except Exception as e:
                    logger.warning(f"Failed to create threat output {i}: {e}")
                    continue
            
            logger.info(f"Document analysis completed: {len(threats)} threats identified")
            return threats
            
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            return []
    
    def _get_default_prompt(self) -> str:
        """Default prompt for document analysis"""
        return """
Analyze the following document for architectural patterns and security concerns.

Document Content:
{document_content}

Analysis Context:
{additional_context}

Please identify potential security threats at the document level, focusing on:
1. Architectural patterns that may introduce vulnerabilities
2. Data handling practices mentioned in the document
3. Authentication and authorization mechanisms described
4. Network communications and data flows
5. Third-party integrations and dependencies

For each threat identified, provide a JSON object with the following structure:
{{
    "Threat Name": "Clear, descriptive name",
    "Description": "Detailed description of the threat",
    "STRIDE Category": "One of: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege",
    "Affected Component": "Document section or architectural component",
    "Potential Impact": "High/Medium/Low - describe the potential business impact",
    "Likelihood": "High/Medium/Low - probability of exploitation",
    "Suggested Mitigation": "Specific mitigation recommendations"
}}

Return your analysis as a JSON array of threat objects.
"""
    
    def _get_document_analysis_context(self) -> str:
        """Additional context for document analysis"""
        return """
Focus on threats that can be identified from documentation alone:
- Design patterns that are known to be vulnerable
- Missing security controls in architectural descriptions  
- Inadequate separation of concerns
- Insufficient input validation descriptions
- Weak authentication/authorization mechanisms
- Insecure data storage or transmission patterns
- Missing logging and monitoring capabilities
- Third-party integration security gaps

Consider common document-level security issues:
- Overprivileged service accounts described
- Hardcoded credentials or secrets mentioned
- Insecure default configurations
- Missing security headers or protections
- Inadequate error handling descriptions
- Lack of rate limiting or DoS protection
"""


class DataFlowAnalysisAgent(BaseAgent):
    """
    Agent that analyzes data flow diagrams and component relationships
    to identify data-centric security threats.
    """
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="data_flow_analysis",
            version="1.0.0", 
            description="Data Flow Analysis Agent",
            category=AgentCategory.ARCHITECTURE,
            priority=20,  # Run after document analysis
            requires_document=False,
            requires_components=True,
            estimated_tokens=2500,
            enabled_by_default=True,
            legacy_equivalent=None
        )
    
    async def analyze(
        self,
        context: AgentExecutionContext,
        llm_provider: Any,
        db_session: Any,
        settings_service: Optional[Any] = None
    ) -> List[ThreatOutput]:
        """
        Analyze data flow diagrams for security threats
        """
        logger.info("Starting data flow analysis...")
        
        if not context.components:
            logger.warning("No components provided for analysis")
            return []
        
        try:
            # Get custom prompt if available
            custom_prompt = await self.get_prompt_template(settings_service)
            
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self._get_default_dfd_prompt()
            
            # Prepare components data for analysis
            components_json = str(context.components)[:3000]  # Limit size
            
            # Prepare the analysis prompt
            analysis_prompt = prompt.format(
                components_data=components_json,
                existing_threats=str(context.existing_threats or [])[:1000]
            )
            
            logger.info("Sending DFD analysis request to LLM...")
            
            # Call LLM service
            response = await llm_provider.generate_completion(
                prompt=analysis_prompt,
                max_tokens=3500,
                temperature=0.2
            )
            
            if not response or not response.get('content'):
                logger.warning("Empty response from LLM")
                return []
            
            # Parse the response
            threat_dicts = self._parse_llm_response(response['content'])
            
            # Convert to ThreatOutput objects
            threats = []
            for i, threat_dict in enumerate(threat_dicts):
                try:
                    threat = self._create_threat_output(
                        threat_dict=threat_dict,
                        agent_name=self.get_metadata().name,
                        confidence=0.85  # DFD analysis has high confidence
                    )
                    threats.append(threat)
                except Exception as e:
                    logger.warning(f"Failed to create threat output {i}: {e}")
                    continue
            
            logger.info(f"Data flow analysis completed: {len(threats)} threats identified")
            return threats
            
        except Exception as e:
            logger.error(f"Data flow analysis failed: {e}")
            return []
    
    def _get_default_dfd_prompt(self) -> str:
        """Default prompt for DFD analysis"""
        return """
Analyze the following data flow diagram components for security threats.

Components and Data Flows:
{components_data}

Existing Threats (to avoid duplicates):
{existing_threats}

Perform STRIDE analysis on the data flows and component interactions:

1. **Spoofing**: Can external entities or processes be impersonated?
2. **Tampering**: Can data be modified in transit or storage?
3. **Repudiation**: Are there insufficient audit trails?
4. **Information Disclosure**: Can sensitive data be accessed inappropriately?
5. **Denial of Service**: Are there components vulnerable to DoS attacks?
6. **Elevation of Privilege**: Can attackers gain unauthorized access levels?

Focus on:
- Trust boundaries between components
- Data stores with sensitive information
- Network communications between processes
- External entity interactions
- Data transformation points

For each threat identified, provide a JSON object:
{{
    "Threat Name": "Clear, descriptive name",
    "Description": "Detailed description focusing on data flow aspects",
    "STRIDE Category": "Primary STRIDE category",
    "Affected Component": "Specific component or data flow",
    "Potential Impact": "High/Medium/Low with business context",
    "Likelihood": "High/Medium/Low based on attack vectors",
    "Suggested Mitigation": "Technical mitigation recommendations"
}}

Return your analysis as a JSON array of threat objects.
"""