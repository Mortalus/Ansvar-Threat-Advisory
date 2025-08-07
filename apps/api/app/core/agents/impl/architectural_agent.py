"""
Architectural Risk Agent - Modular Implementation

Migrated from V3 ArchitecturalRiskAgent with full compatibility preservation.
Detects systemic architectural flaws and design vulnerabilities.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.agents.base import BaseAgent, AgentMetadata, AgentCategory, ThreatOutput, AgentExecutionContext
from app.core.llm import get_llm_provider, get_system_prompt_for_step

logger = logging.getLogger(__name__)


class ArchitecturalRiskAgent(BaseAgent):
    """
    Migrated from V3 ArchitecturalRiskAgent
    Preserves ALL existing functionality and output format
    """
    
    def __init__(self):
        super().__init__()
        
        # Preserved V3 anti-patterns detection
        self.anti_patterns = {
            'single_point_of_failure': [
                'single point of failure', 'spof', 'no redundancy', 
                'single instance', 'no failover', 'single server'
            ],
            'shared_database': [
                'shared database', 'shared db', 'common database',
                'monolithic database', 'single database for all'
            ],
            'insufficient_segmentation': [
                'no segmentation', 'flat network', 'same vpc',
                'no isolation', 'shared environment', 'no dmz'
            ],
            'untested_dr': [
                'dr not tested', 'recovery never tested', 'no dr test',
                'backup not verified', 'untested backup'
            ],
            'tight_coupling': [
                'tightly coupled', 'direct dependency', 'synchronous only',
                'no message queue', 'no event bus'
            ],
            'missing_caching': [
                'no cache', 'no caching', 'without cache',
                'direct database access', 'no cdn'
            ],
            'no_rate_limiting': [
                'no rate limit', 'unlimited requests', 'no throttling',
                'no api limits', 'unprotected endpoint'
            ]
        }
        
        # Preserved V3 risky patterns
        self.risky_patterns = {
            'centralized_auth': {
                'indicators': ['authentication service', 'auth service', 'login service'],
                'risk': 'Single authentication service is a critical SPOF'
            },
            'public_database': {
                'indicators': ['external', 'public', 'internet'],
                'component_type': 'data_store',
                'risk': 'Database exposed to public network'
            },
            'missing_gateway': {
                'indicators': ['direct access', 'no gateway', 'no proxy'],
                'risk': 'Services exposed without API gateway protection'
            }
        }
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="architectural_risk",
            version="3.0.0",  # Matches V3 system
            description="Detects systemic architectural flaws and design vulnerabilities that traditional scanners miss",
            category=AgentCategory.ARCHITECTURE,
            priority=1,  # Runs first like in V3
            requires_document=True,
            requires_components=True,
            estimated_tokens=3500,
            enabled_by_default=True,
            legacy_equivalent="architectural_risk_agent"
        )
    
    async def analyze(
        self,
        context: AgentExecutionContext,
        llm_provider: Any,
        db_session: Any,
        settings_service: Optional[Any] = None
    ) -> List[ThreatOutput]:
        """
        Direct migration of V3 architectural analysis
        Preserves: Single points of failure, redundancy, patterns
        """
        
        logger.info("🏗️ Starting architectural risk analysis (modular)")
        
        try:
            # Extract context data
            document_text = context.document_text or ""
            components = context.components or {}
            existing_threats = context.existing_threats or []
            
            # Get custom prompt or use V3 default
            custom_prompt = await self.get_prompt_template(settings_service)
            
            if not custom_prompt:
                # Use exact V3 prompt for compatibility
                fallback_prompt = "You are an expert Enterprise Architect and Security Professional specializing in identifying systemic architectural vulnerabilities that traditional security scans miss."
                custom_prompt = await get_system_prompt_for_step(
                    step_name="threat_generation",
                    agent_type="architectural_risk", 
                    fallback_prompt=fallback_prompt,
                    db_session=db_session
                ) or fallback_prompt
            
            # Prepare V3-compatible data summaries
            components_summary = self._prepare_components_summary(components)
            existing_threats_summary = self._prepare_existing_threats_summary(existing_threats)
            
            # Create V3-compatible architectural prompt
            architectural_prompt = f"""{custom_prompt}

SYSTEM DOCUMENTATION:
{document_text[:8000]}  

COMPONENTS IDENTIFIED:
{components_summary}

EXISTING THREATS (for context):
{existing_threats_summary}

MISSION: You are an expert architect conducting a comprehensive security review. Focus on ARCHITECTURAL and DESIGN-LEVEL vulnerabilities that could affect the entire system.

ANALYZE THE FOLLOWING AREAS:
1. Single Points of Failure (SPOF) - Components with no redundancy
2. Trust Boundaries - Missing isolation and segmentation
3. Component Dependencies - Tight coupling and cascading failures
4. Scalability Bottlenecks - Performance and availability risks
5. Recovery and Resilience - DR and backup strategies
6. Architectural Patterns - Anti-patterns and design flaws

OUTPUT FORMAT: Generate architectural threats as a JSON array with this EXACT structure:
[
  {{
    "Threat Name": "Single Point of Failure in Authentication Service",
    "Description": "The authentication service appears to be a single instance with no redundancy or failover mechanism. If this service becomes unavailable, all user authentication would fail, effectively shutting down the entire application.",
    "STRIDE Category": "Denial of Service",
    "Affected Component": "auth-service",
    "Potential Impact": "Critical", 
    "Likelihood": "Medium",
    "Suggested Mitigation": "Implement active-active clustering for the authentication service with proper health checks and automatic failover. Consider implementing circuit breakers and graceful degradation.",
    "threat_class": "architectural",
    "priority_score": 9.2
  }}
]

IMPORTANT: 
- Focus on SYSTEM-LEVEL risks, not individual vulnerabilities
- Each threat must include realistic business impact
- Prioritize threats that could cause cascading failures
- Consider both technical and operational perspectives
- Output valid JSON only, no markdown or explanations"""
            
            # Execute LLM call with V3 parameters
            response = await llm_provider.generate(
                prompt=architectural_prompt,
                temperature=0.7,
                max_tokens=4000
            )
            
            # Parse response using inherited method
            threat_dicts = self._parse_llm_response(response.content)
            
            # Convert to ThreatOutput objects
            threats = []
            for i, threat_dict in enumerate(threat_dicts):
                try:
                    threat_output = self._create_threat_output(
                        threat_dict=threat_dict,
                        agent_name="architectural_risk",
                        confidence=0.85
                    )
                    # Add architectural-specific metadata
                    threat_output.threat_class = "architectural"
                    threats.append(threat_output)
                    
                except Exception as e:
                    logger.warning(f"Failed to create threat output {i}: {e}")
                    continue
            
            logger.info(f"✅ Architectural analysis complete: {len(threats)} threats identified")
            return threats
            
        except Exception as e:
            logger.error(f"Architectural agent analysis failed: {e}")
            return []
    
    def _prepare_components_summary(self, components: Dict[str, Any]) -> str:
        """Prepare V3-compatible components summary"""
        try:
            summary_parts = []
            
            # Handle both V3 format and new format
            processes = components.get('processes', [])
            data_stores = components.get('assets', []) or components.get('data_stores', [])
            external_entities = components.get('external_entities', [])
            data_flows = components.get('data_flows', [])
            
            if processes:
                summary_parts.append(f"PROCESSES ({len(processes)}):")
                for proc in processes[:10]:  # Limit for token management
                    name = proc.get('name', 'Unknown') if isinstance(proc, dict) else str(proc)
                    summary_parts.append(f"  - {name}")
            
            if data_stores:
                summary_parts.append(f"\nDATA STORES ({len(data_stores)}):")
                for store in data_stores[:10]:
                    name = store.get('name', 'Unknown') if isinstance(store, dict) else str(store)
                    summary_parts.append(f"  - {name}")
            
            if external_entities:
                summary_parts.append(f"\nEXTERNAL ENTITIES ({len(external_entities)}):")
                for entity in external_entities[:10]:
                    name = entity.get('name', 'Unknown') if isinstance(entity, dict) else str(entity)
                    summary_parts.append(f"  - {name}")
            
            if data_flows:
                summary_parts.append(f"\nDATA FLOWS ({len(data_flows)}):")
                for flow in data_flows[:5]:
                    if isinstance(flow, dict):
                        src = flow.get('source', 'Unknown')
                        dst = flow.get('destination', 'Unknown')
                        summary_parts.append(f"  - {src} → {dst}")
            
            return "\n".join(summary_parts) if summary_parts else "No components identified"
            
        except Exception as e:
            logger.warning(f"Error preparing components summary: {e}")
            return str(components)[:1000]  # Fallback to raw data
    
    def _prepare_existing_threats_summary(self, existing_threats: List[Dict]) -> str:
        """Prepare V3-compatible existing threats summary"""
        try:
            if not existing_threats:
                return "No existing threats to consider"
            
            summary_parts = []
            for i, threat in enumerate(existing_threats[:5]):  # Limit for token management
                name = threat.get('Threat Name', f'Threat {i+1}')
                component = threat.get('Affected Component', 'Unknown')
                impact = threat.get('Potential Impact', 'Unknown')
                summary_parts.append(f"  - {name} (Component: {component}, Impact: {impact})")
            
            if len(existing_threats) > 5:
                summary_parts.append(f"  ... and {len(existing_threats) - 5} more threats")
            
            return f"EXISTING THREATS ({len(existing_threats)}):\n" + "\n".join(summary_parts)
            
        except Exception as e:
            logger.warning(f"Error preparing threats summary: {e}")
            return f"Existing threats count: {len(existing_threats)}"