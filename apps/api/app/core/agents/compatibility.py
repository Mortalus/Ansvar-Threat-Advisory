"""
V3 Compatibility Layer

Ensures 100% backward compatibility during migration from V3 multi-agent
system to the new modular architecture. Provides adapters and wrappers
to maintain existing API contracts.
"""

from typing import Dict, List, Any, Optional
import logging
import time
import asyncio

from .base import BaseAgent, AgentExecutionContext
from .registry import AgentRegistry

logger = logging.getLogger(__name__)


class V3CompatibilityLayer:
    """
    Adapter to run new modular agents with V3 interface
    Ensures zero breaking changes during migration
    """
    
    def __init__(self, registry: AgentRegistry, legacy_orchestrator=None):
        self.registry = registry
        self.legacy = legacy_orchestrator  # Fallback to old system
    
    async def run_as_v3(
        self,
        document_text: str,
        dfd_components: Dict,
        existing_threats: List[Dict],
        db_session: Any,
        llm_provider: Any,
        settings_service: Any = None
    ) -> Dict[str, Any]:
        """
        Executes modular agents but returns V3-compatible output
        This ensures ZERO breaking changes to existing API consumers
        """
        
        logger.info("🔄 Running modular agents in V3 compatibility mode")
        
        try:
            # Build execution context in new format
            context = AgentExecutionContext(
                document_text=document_text,
                components=dfd_components,
                existing_threats=existing_threats
            )
            
            # Get V3-equivalent agents
            agents = self.registry.get_enabled_agents({
                "enabled_agents": [
                    "architectural_risk",
                    "business_financial", 
                    "compliance_governance"
                ]
            })
            
            if not agents:
                logger.warning("No V3-compatible agents found, using legacy fallback")
                if self.legacy:
                    return await self.legacy.analyze_system(
                        document_text, dfd_components, existing_threats, db_session
                    )
                else:
                    raise RuntimeError("No agents available and no legacy fallback")
            
            # Execute agents in parallel (like V3)
            logger.info(f"Executing {len(agents)} agents in parallel")
            tasks = []
            
            for agent in agents:
                if agent.validate_context(context):
                    task = agent.analyze(
                        context=context,
                        llm_provider=llm_provider,
                        db_session=db_session,
                        settings_service=settings_service
                    )
                    tasks.append((agent, task))
                else:
                    logger.warning(f"Agent {agent.get_metadata().name} failed context validation")
            
            # Execute all valid agents
            results = await asyncio.gather(
                *[task for _, task in tasks], 
                return_exceptions=True
            )
            
            # Map results back to V3 format
            v3_results = {
                "architectural_risks": [],
                "business_risks": [],
                "compliance_risks": [],
                "total_threats": 0,
                "summary": {}
            }
            
            for (agent, _), threats in zip(tasks, results):
                if isinstance(threats, Exception):
                    logger.error(f"Agent {agent.get_metadata().name} failed: {threats}")
                    continue
                
                # Convert to V3 format and map to correct result key
                v3_threats = [threat.to_v3_format() for threat in threats]
                agent_name = agent.get_metadata().name
                
                if "architectural" in agent_name:
                    v3_results["architectural_risks"] = v3_threats
                elif "business" in agent_name:
                    v3_results["business_risks"] = v3_threats  
                elif "compliance" in agent_name:
                    v3_results["compliance_risks"] = v3_threats
                
                v3_results["total_threats"] += len(v3_threats)
            
            # Generate V3-compatible summary
            v3_results["summary"] = self._generate_v3_summary(v3_results)
            
            logger.info(f"✅ V3 compatibility run complete: {v3_results['total_threats']} threats found")
            return v3_results
            
        except Exception as e:
            logger.error(f"V3 compatibility layer failed: {e}")
            
            # Fallback to legacy system if available
            if self.legacy:
                logger.warning("Falling back to legacy V3 system")
                return await self.legacy.analyze_system(
                    document_text, dfd_components, existing_threats, db_session
                )
            else:
                raise RuntimeError(f"V3 compatibility failed and no fallback available: {e}")
    
    def _generate_v3_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate V3-compatible summary from results"""
        
        total_threats = results["total_threats"]
        arch_count = len(results.get("architectural_risks", []))
        biz_count = len(results.get("business_risks", []))
        comp_count = len(results.get("compliance_risks", []))
        
        # Calculate severity distribution
        all_threats = (
            results.get("architectural_risks", []) +
            results.get("business_risks", []) + 
            results.get("compliance_risks", [])
        )
        
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for threat in all_threats:
            impact = threat.get("Potential Impact", "Medium")
            if impact in severity_counts:
                severity_counts[impact] += 1
        
        return {
            "total_threats": total_threats,
            "by_agent": {
                "architectural": arch_count,
                "business": biz_count,
                "compliance": comp_count
            },
            "severity_distribution": severity_counts,
            "execution_time": time.time(),  # Timestamp
            "agents_executed": ["architectural_risk", "business_financial", "compliance_governance"],
            "compatibility_mode": True  # Indicates V3 compatibility was used
        }


class LegacyAgentAdapter:
    """
    Adapter to wrap old V3 agents in new modular interface
    Useful during migration period
    """
    
    def __init__(self, legacy_agent_class, agent_name: str):
        self.legacy_class = legacy_agent_class
        self.agent_name = agent_name
        self.legacy_instance = None
    
    def get_metadata(self):
        """Return metadata for legacy agent"""
        from .base import AgentMetadata, AgentCategory
        
        return AgentMetadata(
            name=self.agent_name,
            version="3.0.0-legacy",
            description=f"Legacy V3 {self.agent_name} agent",
            category=AgentCategory.CUSTOM,
            priority=100,
            requires_document=True,
            requires_components=True,
            estimated_tokens=3000,
            enabled_by_default=True,
            legacy_equivalent=f"{self.agent_name}_legacy"
        )
    
    async def analyze(self, context, llm_provider, db_session, settings_service=None):
        """Run legacy agent and convert output"""
        
        if not self.legacy_instance:
            self.legacy_instance = self.legacy_class()
        
        # Convert new context to legacy format
        result = await self.legacy_instance.some_legacy_method(
            document_text=context.document_text,
            components=context.components,
            db_session=db_session
        )
        
        # Convert legacy output to new format
        threats = []
        for threat_dict in result:
            threats.append(self._convert_to_threat_output(threat_dict))
        
        return threats
    
    def _convert_to_threat_output(self, threat_dict):
        """Convert legacy threat format to new ThreatOutput"""
        from .base import ThreatOutput
        
        return ThreatOutput(
            threat_id=f"legacy_{hash(str(threat_dict))}",
            threat_name=threat_dict.get("Threat Name", "Legacy Threat"),
            description=threat_dict.get("Description", ""),
            stride_category=threat_dict.get("STRIDE Category", "Unknown"),
            affected_component=threat_dict.get("Affected Component", ""),
            potential_impact=threat_dict.get("Potential Impact", "Medium"),
            likelihood=threat_dict.get("Likelihood", "Medium"),
            mitigation_strategy=threat_dict.get("Suggested Mitigation", ""),
            agent_source=self.agent_name,
            confidence_score=0.7  # Lower confidence for legacy agents
        )