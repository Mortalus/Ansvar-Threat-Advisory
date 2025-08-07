"""
Threat Generator V3: Integrated Multi-Agent System with Context-Aware Risk Scoring

This is the complete implementation combining:
- Part 1: Context-aware risk scoring with controls library
- Part 2: Multi-agent architecture for holistic analysis

This version provides the most comprehensive threat analysis by combining
traditional STRIDE analysis with architectural, business, and compliance perspectives.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline import PipelineStepResult
from app.services.prompt_service import PromptService
from app.core.llm import get_llm_provider
from app.config import settings

# Import V2 components
from .threat_generator_v2 import ThreatGeneratorV2, ControlsLibrary

# Import multi-agent components
from .analyzer_agents import MultiAgentOrchestrator

# Import CWE retrieval service
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)


class ThreatGeneratorV3:
    """
    Advanced threat generator combining context-aware risk scoring with multi-agent analysis.
    
    This represents the full implementation of the three-stage improvement plan:
    1. Context-aware risk scoring (from V2)
    2. Multi-agent architecture (architectural, business, compliance)
    3. Integrated holistic analysis
    """
    
    def __init__(self):
        # Initialize V2 generator for context-aware analysis
        self.v2_generator = ThreatGeneratorV2()
        
        # Initialize multi-agent orchestrator
        self.agent_orchestrator = MultiAgentOrchestrator()
        
        # Initialize CWE retrieval service
        self.cwe_service = IngestionService()
        
        logger.info("Threat Generator V3 initialized with multi-agent system and CWE integration")
    
    async def execute(
        self,
        db_session: AsyncSession,
        pipeline_step_result: Optional[PipelineStepResult],
        component_data: Dict[str, Any],
        document_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute comprehensive threat generation with both context-aware and multi-agent analysis.
        
        Args:
            db_session: Database session
            pipeline_step_result: Current pipeline step result
            component_data: DFD component data
            document_text: Original document text for analysis
            
        Returns:
            Comprehensive threat analysis from multiple perspectives
        """
        try:
            logger.info("Starting Threat Generator V3 with integrated multi-agent analysis")
            
            # Step 0: Retrieve relevant CWE entries for context enhancement
            logger.info("Phase 0: CWE knowledge base retrieval")
            cwe_context = await self._retrieve_cwe_context(component_data)
            
            # Step 1: Run V2 context-aware threat generation (with CWE context)
            logger.info("Phase 1: Context-aware threat generation with CWE knowledge")
            # Enhance component_data with CWE context
            enhanced_component_data = self._enhance_components_with_cwe(component_data, cwe_context)
            
            v2_results = await self.v2_generator.execute(
                db_session=db_session,
                pipeline_step_result=None,  # We'll handle this ourselves
                component_data=enhanced_component_data,
                document_text=document_text
            )
            
            context_aware_threats = v2_results.get('threats', [])
            security_controls = v2_results.get('security_controls_detected', [])
            
            logger.info(f"Generated {len(context_aware_threats)} context-aware threats")
            
            # Step 2: Run multi-agent analysis
            logger.info("Phase 2: Multi-agent specialized analysis")
            logger.info(f"📄 Document text available: {document_text is not None}")
            if document_text:
                logger.info(f"📝 Document text length: {len(document_text)} characters")
            
            if document_text and len(document_text.strip()) > 50:
                logger.info("🤖 Starting multi-agent analysis with 3 specialized agents and CWE context...")
                agent_results = await self.agent_orchestrator.analyze_system(
                    document_text=document_text,
                    dfd_components=enhanced_component_data,  # Use CWE-enhanced components
                    existing_threats=context_aware_threats,
                    db_session=db_session
                )
                
                architectural_risks = agent_results.get('architectural_risks', [])
                business_risks = agent_results.get('business_risks', [])
                compliance_risks = agent_results.get('compliance_risks', [])
                
                logger.info(f"🏗️ Architectural agent found: {len(architectural_risks)} risks")
                logger.info(f"💼 Business agent found: {len(business_risks)} risks") 
                logger.info(f"⚖️ Compliance agent found: {len(compliance_risks)} risks")
            else:
                logger.warning("⚠️ No sufficient document text provided, skipping multi-agent analysis")
                logger.warning("💡 Multi-agent analysis requires document text for comprehensive threat modeling")
                architectural_risks = []
                business_risks = []
                compliance_risks = []
            
            # Step 3: Consolidate and prioritize all threats
            logger.info("Phase 3: Consolidating and prioritizing threats")
            
            all_threats = self._consolidate_threats(
                context_aware_threats,
                architectural_risks,
                business_risks,
                compliance_risks
            )
            
            # Step 4: Apply advanced prioritization
            prioritized_threats = self._apply_advanced_prioritization(all_threats)
            
            # Step 5: Generate executive summary
            executive_summary = self._generate_executive_summary(
                prioritized_threats,
                security_controls,
                v2_results
            )
            
            # Prepare comprehensive result
            result = {
                "threats": prioritized_threats,  # All threats
                "total_count": len(prioritized_threats),
                "analysis_summary": executive_summary,
                
                # Threat breakdown by type
                "threat_breakdown": {
                    "technical_stride": len(context_aware_threats),
                    "architectural": len(architectural_risks),
                    "business": len(business_risks),
                    "compliance": len(compliance_risks)
                },
                
                # Security posture assessment
                "security_posture": {
                    "controls_detected": security_controls,
                    "control_coverage": v2_results.get('control_coverage', {}),
                    "risk_metrics": v2_results.get('risk_metrics', {}),
                    "critical_gaps": self._identify_critical_gaps(prioritized_threats)
                },
                
                # Multi-agent insights
                "specialized_insights": {
                    "architectural": self._summarize_architectural_insights(architectural_risks),
                    "business": self._summarize_business_insights(business_risks),
                    "compliance": self._summarize_compliance_insights(compliance_risks)
                },
                
                # Metadata
                "components_analyzed": v2_results.get('components_analyzed', 0),
                "knowledge_sources_used": v2_results.get('knowledge_sources_used', []) + ["CWE"],
                "analysis_version": "3.0",
                "analysis_methods": ["context_aware", "multi_agent", "holistic", "cwe_enhanced"],
                
                # CWE integration metadata
                "cwe_integration": {
                    "total_cwe_entries_used": enhanced_component_data.get('cwe_metadata', {}).get('total_cwe_entries_used', 0),
                    "components_with_cwe": enhanced_component_data.get('cwe_metadata', {}).get('components_with_cwe', 0),
                    "cwe_enabled": enhanced_component_data.get('cwe_metadata', {}).get('cwe_integration_enabled', False)
                }
            }
            
            # Update pipeline step result if provided
            if pipeline_step_result:
                pipeline_step_result.result_data = result
                pipeline_step_result.status = "completed"
                
                # Get prompt info if available
                prompt_service = PromptService(db_session)
                prompt_template = await prompt_service.get_active_prompt("threat_generation")
                if prompt_template:
                    pipeline_step_result.prompt_id = prompt_template.id
            
            await db_session.commit()
            
            logger.info(f"Threat Generator V3 completed: {len(prioritized_threats)} total threats identified")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Threat Generator V3: {str(e)}")
            if pipeline_step_result:
                pipeline_step_result.status = "failed"
                pipeline_step_result.error = str(e)
            await db_session.commit()
            raise
    
    def _consolidate_threats(
        self,
        context_aware: List[Dict],
        architectural: List[Dict],
        business: List[Dict],
        compliance: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Consolidate threats from all sources, removing duplicates."""
        all_threats = []
        
        # Add source tags
        for threat in context_aware:
            threat['analysis_source'] = 'context_aware'
            threat['threat_class'] = 'technical'
            all_threats.append(threat)
        
        for threat in architectural:
            threat['analysis_source'] = 'architectural_agent'
            threat['threat_class'] = 'architectural'
            all_threats.append(threat)
        
        for threat in business:
            threat['analysis_source'] = 'business_agent'
            threat['threat_class'] = 'business'
            all_threats.append(threat)
        
        for threat in compliance:
            threat['analysis_source'] = 'compliance_agent'
            threat['threat_class'] = 'compliance'
            all_threats.append(threat)
        
        # Remove obvious duplicates (same name and component)
        seen = set()
        unique_threats = []
        
        for threat in all_threats:
            key = (
                threat.get('Threat Name', '').lower(),
                threat.get('component_name', '').lower()
            )
            
            if key not in seen:
                seen.add(key)
                unique_threats.append(threat)
        
        return unique_threats
    
    def _apply_advanced_prioritization(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply sophisticated multi-factor prioritization."""
        
        # Scoring weights for different factors
        weights = {
            'severity': 0.3,
            'likelihood': 0.2,
            'business_impact': 0.25,
            'compliance_impact': 0.15,
            'architectural_impact': 0.1
        }
        
        severity_scores = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        likelihood_scores = {'High': 3, 'Medium': 2, 'Low': 1}
        
        for threat in threats:
            # Base scores
            severity = severity_scores.get(threat.get('Potential Impact', 'Medium'), 2)
            likelihood = likelihood_scores.get(threat.get('Likelihood', 'Medium'), 2)
            
            # Bonus scores based on threat class
            business_bonus = 1.5 if threat.get('threat_class') == 'business' else 1.0
            compliance_bonus = 1.3 if threat.get('threat_class') == 'compliance' else 1.0
            architectural_bonus = 1.2 if threat.get('threat_class') == 'architectural' else 1.0
            
            # Check for financial exposure
            financial_bonus = 1.5 if threat.get('financial_exposure') else 1.0
            
            # Calculate composite score
            composite_score = (
                severity * weights['severity'] +
                likelihood * weights['likelihood'] +
                business_bonus * weights['business_impact'] +
                compliance_bonus * weights['compliance_impact'] +
                architectural_bonus * weights['architectural_impact']
            ) * financial_bonus
            
            # Adjust for residual risk if available
            if threat.get('residual_risk'):
                residual_multiplier = severity_scores.get(threat['residual_risk'], 2) / 4
                composite_score *= residual_multiplier
            
            threat['priority_score'] = round(composite_score, 2)
        
        # Sort by priority score
        threats.sort(key=lambda t: t['priority_score'], reverse=True)
        
        # Add priority rankings
        for idx, threat in enumerate(threats):
            threat['overall_priority'] = idx + 1
            
            # Assign priority category
            if idx < len(threats) * 0.1:  # Top 10%
                threat['priority_category'] = 'Critical'
            elif idx < len(threats) * 0.3:  # Top 30%
                threat['priority_category'] = 'High'
            elif idx < len(threats) * 0.6:  # Top 60%
                threat['priority_category'] = 'Medium'
            else:
                threat['priority_category'] = 'Low'
        
        return threats
    
    def _identify_critical_gaps(self, threats: List[Dict[str, Any]]) -> List[str]:
        """Identify critical security gaps from threat analysis."""
        gaps = []
        
        # Check for critical architectural issues
        arch_threats = [t for t in threats if t.get('threat_class') == 'architectural']
        if any('single point of failure' in t.get('Description', '').lower() for t in arch_threats):
            gaps.append("Single points of failure in critical components")
        
        # Check for compliance gaps
        compliance_threats = [t for t in threats if t.get('threat_class') == 'compliance']
        if len(compliance_threats) > 5:
            gaps.append("Multiple compliance requirements not met")
        
        # Check for high residual risks
        high_residual = [t for t in threats if t.get('residual_risk') in ['Critical', 'High']]
        if len(high_residual) > 10:
            gaps.append("Insufficient security controls for high-risk threats")
        
        # Check for business continuity
        if any('disaster recovery' in t.get('Description', '').lower() for t in threats):
            gaps.append("Business continuity planning gaps")
        
        return gaps[:5]  # Top 5 gaps
    
    def _generate_executive_summary(
        self,
        threats: List[Dict[str, Any]],
        controls: List[str],
        v2_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive summary of findings."""
        
        critical_count = len([t for t in threats if t.get('priority_category') == 'Critical'])
        high_count = len([t for t in threats if t.get('priority_category') == 'High'])
        
        # Risk assessment
        if critical_count > 10:
            overall_risk = "Critical"
            risk_statement = "System has critical vulnerabilities requiring immediate attention"
        elif critical_count > 5 or high_count > 15:
            overall_risk = "High"
            risk_statement = "System has significant security risks that should be addressed urgently"
        elif high_count > 10:
            overall_risk = "Medium"
            risk_statement = "System has moderate security risks requiring planned remediation"
        else:
            overall_risk = "Low"
            risk_statement = "System security posture is generally acceptable with minor improvements needed"
        
        return {
            "overall_risk_level": overall_risk,
            "risk_statement": risk_statement,
            "critical_threats": critical_count,
            "high_threats": high_count,
            "total_threats": len(threats),
            "security_controls_present": len(controls),
            "control_effectiveness": v2_results.get('risk_metrics', {}).get('controls_effectiveness', '0%'),
            "top_concerns": self._get_top_concerns(threats),
            "recommended_actions": self._get_recommended_actions(threats)
        }
    
    def _get_top_concerns(self, threats: List[Dict[str, Any]]) -> List[str]:
        """Identify top security concerns."""
        concerns = []
        
        # Group threats by class
        by_class = {}
        for threat in threats[:20]:  # Look at top 20
            threat_class = threat.get('threat_class', 'unknown')
            if threat_class not in by_class:
                by_class[threat_class] = 0
            by_class[threat_class] += 1
        
        # Generate concerns based on distribution
        if by_class.get('architectural', 0) > 5:
            concerns.append("Significant architectural vulnerabilities detected")
        if by_class.get('business', 0) > 5:
            concerns.append("High business impact risks identified")
        if by_class.get('compliance', 0) > 3:
            concerns.append("Compliance violations requiring immediate attention")
        if by_class.get('technical', 0) > 10:
            concerns.append("Multiple technical security vulnerabilities")
        
        return concerns[:3]
    
    def _get_recommended_actions(self, threats: List[Dict[str, Any]]) -> List[str]:
        """Generate prioritized recommendations."""
        actions = []
        
        # Check for common patterns in top threats
        top_threats = threats[:10]
        
        if any('authentication' in t.get('Description', '').lower() for t in top_threats):
            actions.append("Strengthen authentication mechanisms (MFA, OAuth2)")
        
        if any('encryption' in t.get('Suggested Mitigation', '').lower() for t in top_threats):
            actions.append("Implement end-to-end encryption for sensitive data")
        
        if any('single point' in t.get('Description', '').lower() for t in top_threats):
            actions.append("Add redundancy to critical components")
        
        if any('compliance' in t.get('threat_class', '') for t in top_threats):
            actions.append("Conduct compliance audit and implement required controls")
        
        if any('monitoring' in t.get('Suggested Mitigation', '').lower() for t in top_threats):
            actions.append("Enhance monitoring and alerting capabilities")
        
        return actions[:5]
    
    def _summarize_architectural_insights(self, threats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize architectural findings."""
        if not threats:
            return {"status": "No architectural issues detected"}
        
        patterns = []
        for threat in threats[:5]:
            if pattern := threat.get('pattern_detected'):
                patterns.append(pattern)
        
        return {
            "issues_found": len(threats),
            "top_patterns": list(set(patterns)),
            "most_critical": threats[0].get('Description', '') if threats else None
        }
    
    def _summarize_business_insights(self, threats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize business impact findings."""
        if not threats:
            return {"status": "No business risks identified"}
        
        # Look for financial exposure
        financial_risks = [
            t.get('financial_exposure', 'Unknown')
            for t in threats
            if t.get('financial_exposure') and t.get('financial_exposure') != 'Unknown'
        ]
        
        return {
            "risks_identified": len(threats),
            "financial_exposure": financial_risks[:3] if financial_risks else ["Not quantified"],
            "top_business_risk": threats[0].get('Description', '') if threats else None
        }
    
    def _summarize_compliance_insights(self, threats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize compliance findings."""
        if not threats:
            return {"status": "No compliance issues detected"}
        
        # Extract frameworks
        frameworks = set()
        for threat in threats:
            if threat.get('applicable_frameworks'):
                frameworks.update(threat['applicable_frameworks'])
        
        return {
            "issues_found": len(threats),
            "frameworks_affected": list(frameworks),
            "most_critical": threats[0].get('Description', '') if threats else None
        }
    
    async def _retrieve_cwe_context(self, component_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve relevant CWE entries for each component using hybrid approach.
        
        Args:
            component_data: DFD component data
            
        Returns:
            Dict mapping component names to relevant CWE entries
        """
        cwe_context = {}
        
        try:
            components = component_data.get('components', [])
            logger.info(f"🔍 Retrieving CWE context for {len(components)} components")
            
            for component in components:
                component_name = component.get('name', 'unknown')
                component_type = component.get('type', 'default').lower()
                
                # Map component type to our CWE mapping keys
                cwe_component_type = self._map_to_cwe_component_type(component_type)
                
                # Create search query from component description
                description = component.get('description', '')
                technologies = component.get('technologies', [])
                search_query = f"{component_name} {description} {' '.join(technologies)}"
                
                # Get relevant CWE entries
                cwe_entries = await self.cwe_service.get_relevant_cwe_entries(
                    component_type=cwe_component_type,
                    query=search_query,
                    limit=3  # Top 3 most relevant CWE entries per component
                )
                
                if cwe_entries:
                    cwe_context[component_name] = cwe_entries
                    logger.info(f"🎯 Found {len(cwe_entries)} relevant CWE entries for {component_name}")
                else:
                    logger.info(f"⚠️ No CWE entries found for {component_name} (type: {cwe_component_type})")
            
            total_cwe_entries = sum(len(entries) for entries in cwe_context.values())
            logger.info(f"📚 Retrieved {total_cwe_entries} total CWE entries across all components")
            
            return cwe_context
            
        except Exception as e:
            logger.warning(f"Error retrieving CWE context: {e}")
            return {}
    
    def _map_to_cwe_component_type(self, component_type: str) -> str:
        """Map DFD component types to CWE component mapping keys."""
        type_mapping = {
            'web_application': 'web_service',
            'web_server': 'web_service', 
            'application_server': 'web_service',
            'api': 'api_gateway',
            'api_endpoint': 'api_gateway',
            'rest_api': 'api_gateway',
            'database': 'database',
            'data_store': 'data_store',
            'cache': 'data_store',
            'file_system': 'data_store',
            'authentication_service': 'authentication',
            'auth_server': 'authentication',
            'identity_provider': 'authentication',
            'external_service': 'external_entity',
            'third_party': 'external_entity',
            'process': 'process',
            'service': 'process',
            'boundary': 'trust_boundary',
            'network': 'trust_boundary'
        }
        
        return type_mapping.get(component_type.lower(), 'default')
    
    def _enhance_components_with_cwe(
        self, 
        component_data: Dict[str, Any], 
        cwe_context: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Enhance component data with relevant CWE information for threat generation.
        
        Args:
            component_data: Original component data
            cwe_context: CWE entries per component
            
        Returns:
            Enhanced component data with CWE context
        """
        enhanced_data = component_data.copy()
        
        if not cwe_context:
            logger.info("No CWE context available for enhancement")
            return enhanced_data
        
        # Add CWE context to each component
        for component in enhanced_data.get('components', []):
            component_name = component.get('name', '')
            
            if component_name in cwe_context:
                cwe_entries = cwe_context[component_name]
                
                # Create CWE context summary
                cwe_summary = self._create_cwe_summary(cwe_entries)
                
                # Add to component data
                component['cwe_context'] = {
                    'relevant_weaknesses': cwe_entries,
                    'context_summary': cwe_summary,
                    'cwe_count': len(cwe_entries)
                }
                
                logger.info(f"🔗 Enhanced {component_name} with {len(cwe_entries)} CWE entries")
        
        # Add global CWE metadata
        total_cwe_entries = sum(len(entries) for entries in cwe_context.values())
        enhanced_data['cwe_metadata'] = {
            'total_cwe_entries_used': total_cwe_entries,
            'components_with_cwe': len(cwe_context),
            'cwe_integration_enabled': True
        }
        
        logger.info(f"📋 Component data enhanced with CWE context ({total_cwe_entries} total entries)")
        
        return enhanced_data
    
    def _create_cwe_summary(self, cwe_entries: List[Dict[str, Any]]) -> str:
        """Create a concise summary of CWE entries for prompt context."""
        if not cwe_entries:
            return "No relevant CWE weaknesses identified."
        
        summary_parts = []
        
        for entry in cwe_entries:
            cwe_id = entry.get('cwe_id', 'Unknown')
            name = entry.get('name', 'Unknown')
            likelihood = entry.get('likelihood_of_exploit', 'Unknown')
            
            # Create concise entry
            summary_parts.append(f"• {cwe_id}: {name} (Exploit likelihood: {likelihood})")
        
        summary = "Relevant CWE weaknesses to consider:\n" + "\n".join(summary_parts)
        
        # Add general guidance
        summary += "\n\nConsider these weaknesses when identifying threats and designing mitigations."
        
        return summary