"""
Modular Agent Orchestrator V2

New orchestrator that maintains 100% compatibility with V3 while adding
modularity and dynamic agent management. Provides automatic fallback to
legacy systems and comprehensive error handling.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from .base import BaseAgent, AgentExecutionContext, ThreatOutput
from .registry import AgentRegistry
from .compatibility import V3CompatibilityLayer

logger = logging.getLogger(__name__)


class ExecutionMode:
    """Execution modes for gradual migration"""
    LEGACY = "legacy"           # Use old V3 system entirely
    SHADOW = "shadow"           # Run both, return legacy results
    MODULAR = "modular"         # Use new system with fallback
    COMPARISON = "comparison"   # Run both and return comparison


class ModularOrchestrator:
    """
    New orchestrator that maintains 100% compatibility with V3
    while adding modularity and zero-downtime agent management
    """
    
    def __init__(
        self, 
        registry: AgentRegistry, 
        legacy_orchestrator=None,
        execution_mode: str = ExecutionMode.SHADOW
    ):
        self.registry = registry
        self.legacy = legacy_orchestrator  # Fallback to old system
        self.execution_mode = execution_mode
        self.compatibility = V3CompatibilityLayer(registry, legacy_orchestrator)
        
        # Execution statistics
        self.stats = {
            "total_executions": 0,
            "modular_successes": 0,
            "legacy_fallbacks": 0,
            "shadow_comparisons": 0,
            "last_execution": None
        }
    
    async def execute_analysis(
        self,
        context: Union[AgentExecutionContext, Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
        llm_provider: Any = None,
        db_session: Any = None,
        settings_service: Any = None
    ) -> Dict[str, Any]:
        """
        Execute agents with automatic fallback to legacy if needed
        Maintains V3 API compatibility while adding new capabilities
        """
        
        start_time = time.time()
        self.stats["total_executions"] += 1
        self.stats["last_execution"] = datetime.now()
        
        # Convert legacy parameters to new context if needed
        if isinstance(context, dict):
            # Legacy V3 call pattern
            context = AgentExecutionContext(
                document_text=context.get('document_text'),
                components=context.get('components'),
                existing_threats=context.get('existing_threats'),
                pipeline_id=context.get('pipeline_id'),
                user_config=config
            )
        
        # Determine execution mode from config or instance setting
        mode = (config or {}).get("agent_system", self.execution_mode)
        
        logger.info(f"🔄 Executing analysis in {mode} mode")
        
        try:
            if mode == ExecutionMode.LEGACY:
                # Use old system entirely
                return await self._execute_legacy_only(context, db_session)
            
            elif mode == ExecutionMode.SHADOW:
                # Run both systems and compare (return legacy results for safety)
                return await self._execute_shadow_mode(
                    context, config, llm_provider, db_session, settings_service
                )
            
            elif mode == ExecutionMode.COMPARISON:
                # Run both and return detailed comparison
                return await self._execute_comparison_mode(
                    context, config, llm_provider, db_session, settings_service
                )
            
            else:  # MODULAR mode
                # Run new system with fallback
                return await self._execute_modular_with_fallback(
                    context, config, llm_provider, db_session, settings_service
                )
                
        except Exception as e:
            logger.error(f"Orchestrator failed completely: {e}")
            # Ultimate fallback
            if self.legacy:
                logger.warning("Using ultimate legacy fallback")
                self.stats["legacy_fallbacks"] += 1
                return await self._execute_legacy_only(context, db_session)
            else:
                raise RuntimeError(f"All execution paths failed: {e}")
        finally:
            execution_time = time.time() - start_time
            logger.info(f"⏱️ Total execution time: {execution_time:.2f}s")
    
    async def _execute_legacy_only(
        self,
        context: AgentExecutionContext,
        db_session: Any
    ) -> Dict[str, Any]:
        """Execute legacy V3 system only"""
        
        if not self.legacy:
            raise RuntimeError("Legacy execution requested but no legacy orchestrator available")
        
        logger.info("🔄 Executing legacy V3 system only")
        
        # Convert context back to legacy format
        result = await self.legacy.analyze_system(
            document_text=context.document_text or "",
            dfd_components=context.components or {},
            existing_threats=context.existing_threats or [],
            db_session=db_session
        )
        
        # Add execution metadata
        result["execution_mode"] = "legacy"
        result["modular_agents_used"] = False
        
        return result
    
    async def _execute_shadow_mode(
        self,
        context: AgentExecutionContext,
        config: Optional[Dict],
        llm_provider: Any,
        db_session: Any,
        settings_service: Any
    ) -> Dict[str, Any]:
        """
        Run both systems in parallel and compare results
        Returns legacy results for safety while logging differences
        """
        
        logger.info("👥 Executing shadow mode (both systems)")
        self.stats["shadow_comparisons"] += 1
        
        # Run both systems concurrently
        tasks = []
        
        # Legacy execution
        if self.legacy:
            legacy_task = self._execute_legacy_only(context, db_session)
            tasks.append(("legacy", legacy_task))
        
        # Modular execution
        modular_task = self._execute_modular_agents(
            context, config, llm_provider, db_session, settings_service
        )
        tasks.append(("modular", modular_task))
        
        # Execute both
        results = await asyncio.gather(
            *[task for _, task in tasks], 
            return_exceptions=True
        )
        
        legacy_result = None
        modular_result = None
        
        for (system_type, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error(f"{system_type} system failed: {result}")
                continue
                
            if system_type == "legacy":
                legacy_result = result
            else:
                modular_result = result
        
        # Compare results and log differences
        if legacy_result and modular_result:
            comparison = self._compare_results(legacy_result, modular_result)
            logger.info(f"Shadow comparison: {comparison}")
            
            # Store comparison for analysis (could save to database)
            await self._store_comparison(comparison)
        
        # Return legacy results for safety (zero risk approach)
        if legacy_result:
            legacy_result["execution_mode"] = "shadow"
            legacy_result["modular_comparison"] = modular_result is not None
            return legacy_result
        elif modular_result:
            # Fallback to modular if legacy failed
            logger.warning("Legacy failed in shadow mode, returning modular results")
            modular_result["execution_mode"] = "shadow_fallback"
            return modular_result
        else:
            raise RuntimeError("Both legacy and modular systems failed in shadow mode")
    
    async def _execute_comparison_mode(
        self,
        context: AgentExecutionContext,
        config: Optional[Dict],
        llm_provider: Any,
        db_session: Any,
        settings_service: Any
    ) -> Dict[str, Any]:
        """Execute both systems and return detailed comparison"""
        
        logger.info("🔍 Executing comparison mode")
        
        # Same as shadow mode but returns comparison results
        shadow_result = await self._execute_shadow_mode(
            context, config, llm_provider, db_session, settings_service
        )
        
        # Return comparison data instead of just legacy results
        comparison_data = shadow_result.get("comparison", {})
        comparison_data["execution_mode"] = "comparison"
        comparison_data["legacy_result"] = shadow_result
        
        return comparison_data
    
    async def _execute_modular_with_fallback(
        self,
        context: AgentExecutionContext,
        config: Optional[Dict],
        llm_provider: Any,
        db_session: Any,
        settings_service: Any
    ) -> Dict[str, Any]:
        """Run new modular system with automatic fallback to legacy"""
        
        logger.info("🔧 Executing modular system with fallback")
        
        try:
            # Execute modular agents
            result = await self._execute_modular_agents(
                context, config, llm_provider, db_session, settings_service
            )
            
            # Validate result has all expected V3 fields
            if self._validate_v3_compatibility(result):
                self.stats["modular_successes"] += 1
                result["execution_mode"] = "modular"
                result["fallback_used"] = False
                return result
            else:
                logger.warning("Modular result failed V3 validation, using legacy fallback")
                raise ValueError("Modular result format validation failed")
                
        except Exception as e:
            logger.error(f"Modular execution failed: {e}")
            
            # Automatic fallback to legacy
            if self.legacy:
                logger.warning("Falling back to legacy V3 system")
                self.stats["legacy_fallbacks"] += 1
                
                result = await self._execute_legacy_only(context, db_session)
                result["execution_mode"] = "modular_fallback"
                result["fallback_reason"] = str(e)
                result["fallback_used"] = True
                return result
            else:
                raise RuntimeError(f"Modular execution failed and no fallback available: {e}")
    
    async def _execute_modular_agents(
        self,
        context: AgentExecutionContext,
        config: Optional[Dict],
        llm_provider: Any,
        db_session: Any,
        settings_service: Any
    ) -> Dict[str, Any]:
        """Execute modular agents and return V3-compatible results"""
        
        # Get enabled agents (defaults to V3 agents for compatibility)
        agents = self.registry.get_enabled_agents(config or {})
        
        if not agents:
            logger.warning("No agents available for execution")
            raise RuntimeError("No agents registered or enabled")
        
        logger.info(f"🤖 Executing {len(agents)} modular agents")
        
        # Validate agents can execute with current context
        valid_agents = [agent for agent in agents if agent.validate_context(context)]
        
        if not valid_agents:
            logger.warning("No agents can execute with current context")
            raise RuntimeError("No agents meet context requirements")
        
        logger.info(f"✅ {len(valid_agents)} agents validated for execution")
        
        # Execute agents (parallel execution like V3)
        execution_config = config or {}
        parallel = execution_config.get("parallel_execution", True)
        
        if parallel:
            results = await self._execute_agents_parallel(
                valid_agents, context, llm_provider, db_session, settings_service
            )
        else:
            results = await self._execute_agents_sequential(
                valid_agents, context, llm_provider, db_session, settings_service
            )
        
        # Convert to V3-compatible format
        return self._format_for_v3_compatibility(valid_agents, results)
    
    async def _execute_agents_parallel(
        self,
        agents: List[BaseAgent],
        context: AgentExecutionContext,
        llm_provider: Any,
        db_session: Any,
        settings_service: Any
    ) -> List[Union[List[ThreatOutput], Exception]]:
        """Execute agents in parallel"""
        
        logger.info("🚀 Executing agents in parallel")
        
        tasks = [
            agent.analyze(context, llm_provider, db_session, settings_service)
            for agent in agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any failures
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agent.get_metadata().name} failed: {result}")
            else:
                logger.info(f"✅ Agent {agent.get_metadata().name}: {len(result)} threats")
        
        return results
    
    async def _execute_agents_sequential(
        self,
        agents: List[BaseAgent],
        context: AgentExecutionContext,
        llm_provider: Any,
        db_session: Any,
        settings_service: Any
    ) -> List[Union[List[ThreatOutput], Exception]]:
        """Execute agents sequentially"""
        
        logger.info("⚡ Executing agents sequentially")
        
        results = []
        for agent in agents:
            try:
                result = await agent.analyze(
                    context, llm_provider, db_session, settings_service
                )
                results.append(result)
                logger.info(f"✅ Agent {agent.get_metadata().name}: {len(result)} threats")
                
            except Exception as e:
                logger.error(f"Agent {agent.get_metadata().name} failed: {e}")
                results.append(e)
        
        return results
    
    def _format_for_v3_compatibility(
        self,
        agents: List[BaseAgent],
        results: List[Union[List[ThreatOutput], Exception]]
    ) -> Dict[str, Any]:
        """Format modular results to match V3 output exactly"""
        
        # Initialize V3-compatible structure
        v3_output = {
            "architectural_risks": [],
            "business_risks": [],
            "compliance_risks": [],
            "total_threats": 0,
            "summary": {},
            "agents_executed": [],
            "execution_metadata": {
                "execution_time": time.time(),
                "agents_count": len(agents),
                "successful_agents": 0,
                "failed_agents": 0
            }
        }
        
        # Process each agent's results
        for agent, threats_result in zip(agents, results):
            agent_name = agent.get_metadata().name
            v3_output["agents_executed"].append(agent_name)
            
            if isinstance(threats_result, Exception):
                v3_output["execution_metadata"]["failed_agents"] += 1
                continue
            
            v3_output["execution_metadata"]["successful_agents"] += 1
            
            # Convert ThreatOutput objects to V3 format
            v3_threats = [threat.to_v3_format() for threat in threats_result]
            
            # Map to correct V3 category based on agent name
            if "architectural" in agent_name:
                v3_output["architectural_risks"] = v3_threats
            elif "business" in agent_name:
                v3_output["business_risks"] = v3_threats  
            elif "compliance" in agent_name:
                v3_output["compliance_risks"] = v3_threats
            else:
                # Custom agents go to architectural by default
                v3_output["architectural_risks"].extend(v3_threats)
            
            v3_output["total_threats"] += len(v3_threats)
        
        # Generate V3-compatible summary
        v3_output["summary"] = self._generate_v3_summary(v3_output)
        
        logger.info(f"✅ Formatted {v3_output['total_threats']} threats for V3 compatibility")
        return v3_output
    
    def _generate_v3_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate V3-compatible summary"""
        
        total_threats = results["total_threats"]
        arch_count = len(results["architectural_risks"])
        biz_count = len(results["business_risks"])
        comp_count = len(results["compliance_risks"])
        
        # Calculate severity distribution
        all_threats = (
            results["architectural_risks"] +
            results["business_risks"] + 
            results["compliance_risks"]
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
            "execution_time": time.time(),
            "agents_executed": results["agents_executed"],
            "modular_system": True,
            "successful_agents": results["execution_metadata"]["successful_agents"],
            "failed_agents": results["execution_metadata"]["failed_agents"]
        }
    
    def _validate_v3_compatibility(self, result: Dict[str, Any]) -> bool:
        """Validate that result has all required V3 fields"""
        
        required_fields = [
            "architectural_risks",
            "business_risks", 
            "compliance_risks",
            "total_threats"
        ]
        
        for field in required_fields:
            if field not in result:
                logger.warning(f"Missing required V3 field: {field}")
                return False
        
        # Validate structure
        if not isinstance(result["total_threats"], int):
            logger.warning("total_threats is not an integer")
            return False
        
        return True
    
    def _compare_results(self, legacy: Dict, modular: Dict) -> Dict[str, Any]:
        """Compare legacy and modular results"""
        
        return {
            "timestamp": time.time(),
            "legacy_threats": legacy.get("total_threats", 0),
            "modular_threats": modular.get("total_threats", 0),
            "threat_difference": abs(
                legacy.get("total_threats", 0) - modular.get("total_threats", 0)
            ),
            "severity_match": self._compare_severity_distribution(legacy, modular),
            "agent_coverage": {
                "legacy_agents": legacy.get("agents_executed", []),
                "modular_agents": modular.get("agents_executed", [])
            }
        }
    
    def _compare_severity_distribution(self, legacy: Dict, modular: Dict) -> float:
        """Compare severity distributions between results"""
        try:
            legacy_sev = legacy.get("summary", {}).get("severity_distribution", {})
            modular_sev = modular.get("summary", {}).get("severity_distribution", {})
            
            # Calculate similarity score
            total_diff = 0
            for severity in ["Critical", "High", "Medium", "Low"]:
                legacy_count = legacy_sev.get(severity, 0)
                modular_count = modular_sev.get(severity, 0)
                total_diff += abs(legacy_count - modular_count)
            
            total_threats = max(1, legacy.get("total_threats", 0) + modular.get("total_threats", 0))
            similarity = max(0, 1 - (total_diff / total_threats))
            
            return round(similarity, 3)
            
        except Exception as e:
            logger.warning(f"Error comparing severity distributions: {e}")
            return 0.0
    
    async def _store_comparison(self, comparison: Dict[str, Any]) -> None:
        """Store comparison data for analysis (could save to database)"""
        # For now, just log. In production, save to database for analysis
        logger.info(f"Comparison stored: {comparison}")
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get orchestrator execution statistics"""
        return {
            **self.stats,
            "success_rate": (
                self.stats["modular_successes"] / max(1, self.stats["total_executions"])
            ),
            "fallback_rate": (
                self.stats["legacy_fallbacks"] / max(1, self.stats["total_executions"])
            )
        }