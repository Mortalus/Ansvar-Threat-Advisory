"""
AI-First Threat Refinement Step

Intelligently refines and enhances threat model data using LLM capabilities:
- LLM-powered semantic deduplication
- Contextual risk assessment and scoring
- Business risk translation
- Control-aware threat suppression
- Enhanced mitigation suggestions

Integrates seamlessly with the existing pipeline architecture.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.pipeline import PipelineStepResult
from app.core.llm import get_llm_provider
from app.services.ingestion_service import IngestionService
from app.services.prompt_service import PromptService
from app.config import settings

logger = logging.getLogger(__name__)

# Risk scoring matrix for consistent assessment
RISK_MATRIX = {
    ("Critical", "High"): "Critical",
    ("Critical", "Medium"): "Critical", 
    ("Critical", "Low"): "High",
    ("High", "High"): "Critical",
    ("High", "Medium"): "High",
    ("High", "Low"): "Medium",
    ("Medium", "High"): "High",
    ("Medium", "Medium"): "Medium",
    ("Medium", "Low"): "Medium",
    ("Low", "High"): "Medium",
    ("Low", "Medium"): "Low",
    ("Low", "Low"): "Low"
}

# Industry-specific risk contexts
INDUSTRY_CONTEXTS = {
    "Healthcare": {
        "high_value_data": ["PHI", "PII", "Medical Records"],
        "compliance_frameworks": ["HIPAA", "HITECH"],
        "critical_assets": ["Patient Database", "EMR System", "Medical Devices"]
    },
    "Finance": {
        "high_value_data": ["PCI", "Financial Records", "Account Information"],
        "compliance_frameworks": ["PCI-DSS", "SOX", "GDPR"],
        "critical_assets": ["Payment System", "Customer Database", "Trading Platform"]
    },
    "Government": {
        "high_value_data": ["Classified", "Sensitive", "PII"],
        "compliance_frameworks": ["FedRAMP", "FISMA", "NIST"],
        "critical_assets": ["Citizen Database", "Critical Infrastructure", "Communication Systems"]
    },
    "Generic": {
        "high_value_data": ["PII", "Confidential", "Business Critical"],
        "compliance_frameworks": ["GDPR", "ISO 27001"],
        "critical_assets": ["Customer Database", "Business Systems", "Intellectual Property"]
    }
}

class ThreatRefiner:
    """
    AI-powered threat refinement using LLM capabilities for intelligent analysis.
    Integrates with existing RAG infrastructure for enhanced context.
    """
    
    def __init__(self):
        try:
            self.ingestion_service = IngestionService()
        except Exception as e:
            logger.warning(f"RAG service unavailable: {e}. Using LLM-only refinement.")
            self.ingestion_service = None
    
    async def execute(
        self,
        db_session: AsyncSession,
        pipeline_step_result: Optional[PipelineStepResult],
        threat_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute AI-powered threat refinement.
        
        Args:
            db_session: Database session
            pipeline_step_result: Pipeline step result to update
            threat_data: Generated threats and metadata from previous step
            
        Returns:
            Refined threat data with enhanced context and prioritization
        """
        try:
            logger.info("Starting AI-powered threat refinement")
            
            # Extract threats and metadata from previous step
            threats = threat_data.get("threats", [])
            if not threats:
                logger.warning("No threats found in threat_data")
                return {"refined_threats": [], "total_count": 0, "refinement_stats": {}}
            
            # Get prompt templates for refinement
            prompt_service = PromptService(db_session)
            refinement_prompt = await prompt_service.get_active_prompt("threat_refinement")
            
            if not refinement_prompt:
                await prompt_service.initialize_default_prompts()
                refinement_prompt = await prompt_service.get_active_prompt("threat_refinement")
            
            logger.info(f"Starting refinement of {len(threats)} threats")
            
            # Step 1: LLM-powered semantic deduplication
            deduplicated_threats = await self._semantic_deduplication(threats)
            
            # Step 2: Contextual risk assessment
            risk_assessed_threats = await self._contextual_risk_assessment(deduplicated_threats)
            
            # Step 3: Business risk translation
            business_threats = await self._business_risk_translation(risk_assessed_threats)
            
            # Step 4: Enhanced mitigation generation
            enhanced_threats = await self._enhance_mitigations(business_threats)
            
            # Step 5: Control-aware suppression
            final_threats = await self._control_aware_suppression(enhanced_threats, threat_data)
            
            # Step 6: Prioritization and final scoring
            prioritized_threats = await self._prioritize_threats(final_threats)
            
            # Calculate refinement statistics
            refinement_stats = {
                "original_count": len(threats),
                "deduplicated_count": len(threats) - len(deduplicated_threats),
                "final_count": len(prioritized_threats),
                "risk_distribution": self._calculate_risk_distribution(prioritized_threats),
                "refinement_timestamp": datetime.utcnow().isoformat()
            }
            
            result = {
                "refined_threats": prioritized_threats,
                "total_count": len(prioritized_threats),
                "refinement_stats": refinement_stats,
                "original_threats": threats  # Keep for comparison
            }
            
            # Update pipeline step result
            if pipeline_step_result:
                pipeline_step_result.result_data = result
                pipeline_step_result.status = "completed"
                pipeline_step_result.prompt_id = refinement_prompt.id
                pipeline_step_result.llm_model = getattr(settings, 'default_llm_provider', 'mock')
            
            await db_session.commit()
            
            logger.info(f"Threat refinement completed: {len(prioritized_threats)} final threats")
            return result
            
        except Exception as e:
            logger.error(f"Error in threat refinement: {str(e)}")
            if pipeline_step_result:
                pipeline_step_result.status = "failed"
                pipeline_step_result.error = str(e)
            await db_session.commit()
            raise
    
    async def _semantic_deduplication(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use LLM to identify and merge semantically similar threats."""
        if len(threats) <= 1:
            return threats
            
        logger.info(f"Performing semantic deduplication on {len(threats)} threats")
        
        llm_provider = await get_llm_provider("threat_refinement")
        
        # Group threats by component for more efficient processing
        component_groups = {}
        for threat in threats:
            component = threat.get("component_name", "unknown")
            if component not in component_groups:
                component_groups[component] = []
            component_groups[component].append(threat)
        
        deduplicated_threats = []
        
        for component, component_threats in component_groups.items():
            if len(component_threats) <= 1:
                deduplicated_threats.extend(component_threats)
                continue
            
            # Create prompt for LLM to identify similar threats
            threats_text = ""
            for i, threat in enumerate(component_threats):
                threats_text += f"Threat {i+1}:\n"
                threats_text += f"- Category: {threat.get('Threat Category', 'Unknown')}\n"
                threats_text += f"- Name: {threat.get('Threat Name', 'Unknown')}\n"
                threats_text += f"- Description: {threat.get('Description', 'Unknown')}\n"
                threats_text += f"- Mitigation: {threat.get('Suggested Mitigation', 'Unknown')}\n\n"
            
            dedup_prompt = f"""
Analyze these {len(component_threats)} threats for component '{component}' and identify which ones are semantically similar or duplicates.

{threats_text}

For each group of similar threats, identify:
1. Which threats are essentially the same (same attack vector, same impact)
2. Which threat has the most comprehensive description
3. Which mitigation is most detailed

Return a JSON array where each element represents a group of similar threats:
[
    {{
        "similar_threat_indices": [1, 3],  // 0-based indices of similar threats
        "primary_threat_index": 1,         // Index of the best threat to keep
        "merge_reason": "Both describe SQL injection with similar impact"
    }}
]

Only include groups with 2+ similar threats. Return empty array [] if no duplicates found.
"""
            
            try:
                response = await llm_provider.generate(
                    prompt=dedup_prompt,
                    system_prompt="You are an expert in cybersecurity threat analysis. Identify semantically similar threats with precision."
                )
                
                # Parse LLM response
                similarity_groups = self._parse_similarity_groups(response.content)
                
                # Merge similar threats
                component_deduplicated = self._merge_similar_threats(
                    component_threats, similarity_groups
                )
                
                deduplicated_threats.extend(component_deduplicated)
                
            except Exception as e:
                logger.warning(f"LLM deduplication failed for component {component}: {e}")
                # Fallback to basic deduplication
                deduplicated_threats.extend(self._basic_deduplication(component_threats))
        
        logger.info(f"Deduplication reduced {len(threats)} threats to {len(deduplicated_threats)}")
        return deduplicated_threats
    
    async def _contextual_risk_assessment(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use LLM to perform contextual risk assessment."""
        logger.info("Performing contextual risk assessment")
        
        llm_provider = await get_llm_provider("threat_refinement")
        enhanced_threats = []
        
        for threat in threats:
            try:
                # Build context for risk assessment
                component_name = threat.get("component_name", "Unknown")
                threat_description = threat.get("Description", "")
                current_impact = threat.get("Potential Impact", "Medium")
                current_likelihood = threat.get("Likelihood", "Medium")
                
                risk_prompt = f"""
Assess the risk for this cybersecurity threat:

Component: {component_name}
Threat Description: {threat_description}
Current Impact Rating: {current_impact}
Current Likelihood Rating: {current_likelihood}

Consider these factors:
1. Component exposure (internal vs external-facing)
2. Data sensitivity (if data flows are involved)
3. Attack complexity and prerequisites
4. Business impact potential
5. Current security landscape

Provide a refined risk assessment in JSON format:
{{
    "impact": "Critical|High|Medium|Low",
    "likelihood": "High|Medium|Low", 
    "risk_score": "Critical|High|Medium|Low",
    "assessment_reasoning": "Detailed explanation of risk rating",
    "exploitability": "High|Medium|Low",
    "business_impact_description": "Description of potential business impact"
}}
"""
                
                response = await llm_provider.generate(
                    prompt=risk_prompt,
                    system_prompt="You are a senior cybersecurity risk analyst. Provide accurate, contextual risk assessments."
                )
                
                # Parse and apply risk assessment
                risk_data = self._parse_risk_assessment(response.content)
                
                # Update threat with enhanced risk data
                enhanced_threat = threat.copy()
                enhanced_threat.update(risk_data)
                enhanced_threat["risk_assessment_method"] = "llm_contextual"
                
                enhanced_threats.append(enhanced_threat)
                
            except Exception as e:
                logger.warning(f"Risk assessment failed for threat: {e}")
                # Keep original threat with fallback risk scoring
                fallback_threat = threat.copy()
                fallback_threat["risk_score"] = self._calculate_fallback_risk_score(
                    threat.get("Potential Impact", "Medium"),
                    threat.get("Likelihood", "Medium")
                )
                enhanced_threats.append(fallback_threat)
        
        return enhanced_threats
    
    async def _business_risk_translation(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Translate technical threats into business risk language."""
        logger.info("Translating threats to business risk language")
        
        llm_provider = await get_llm_provider("threat_refinement")
        business_threats = []
        
        # Determine industry context (could be configured or detected)
        industry = getattr(settings, 'client_industry', 'Generic')
        industry_context = INDUSTRY_CONTEXTS.get(industry, INDUSTRY_CONTEXTS['Generic'])
        
        for threat in threats:
            try:
                technical_description = threat.get("Description", "")
                impact = threat.get("impact", threat.get("Potential Impact", "Medium"))
                component = threat.get("component_name", "Unknown")
                
                business_prompt = f"""
Translate this technical cybersecurity threat into business risk language:

Technical Threat: {technical_description}
Affected Component: {component}
Impact Level: {impact}

Industry Context: {industry}
High-Value Data Types: {', '.join(industry_context['high_value_data'])}
Compliance Frameworks: {', '.join(industry_context['compliance_frameworks'])}

Create a business-focused risk statement that:
1. Uses business language (avoid technical jargon)
2. Quantifies potential business impact
3. References relevant compliance/regulatory concerns
4. Explains the threat in terms executives understand

Return JSON format:
{{
    "business_risk_statement": "Clear business impact description",
    "financial_impact_range": "Low ($<10K)|Medium ($10K-100K)|High ($100K-1M)|Critical ($>1M)",
    "regulatory_implications": "List of applicable regulations/standards",
    "stakeholder_impact": "Which business stakeholders are affected",
    "business_continuity_impact": "How this affects business operations"
}}
"""
                
                response = await llm_provider.generate(
                    prompt=business_prompt,
                    system_prompt="You are a business risk consultant who translates technical risks into executive language."
                )
                
                business_data = self._parse_business_risk(response.content)
                
                # Update threat with business context
                enhanced_threat = threat.copy()
                enhanced_threat.update(business_data)
                enhanced_threat["business_translation_method"] = "llm_generated"
                
                business_threats.append(enhanced_threat)
                
            except Exception as e:
                logger.warning(f"Business translation failed for threat: {e}")
                business_threats.append(threat)  # Keep original threat
        
        return business_threats
    
    async def _enhance_mitigations(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate enhanced, specific mitigation recommendations."""
        logger.info("Enhancing mitigation recommendations")
        
        llm_provider = await get_llm_provider("threat_refinement")
        enhanced_threats = []
        
        for threat in threats:
            try:
                current_mitigation = threat.get("Suggested Mitigation", "")
                threat_description = threat.get("Description", "")
                component = threat.get("component_name", "Unknown")
                risk_score = threat.get("risk_score", "Medium")
                
                mitigation_prompt = f"""
Enhance this cybersecurity mitigation with specific, actionable recommendations:

Threat: {threat_description}
Component: {component}
Risk Level: {risk_score}
Current Mitigation: {current_mitigation}

Provide enhanced mitigation recommendations that include:
1. Specific technical controls (not generic advice)
2. Implementation priority based on risk level
3. Estimated effort/complexity
4. Measurable security outcomes
5. Defense-in-depth layered approach

Return JSON format:
{{
    "primary_mitigation": "Most important mitigation control",
    "secondary_mitigations": ["Additional supporting controls"],
    "implementation_priority": "Critical|High|Medium|Low",
    "estimated_effort": "Low (days)|Medium (weeks)|High (months)",
    "success_metrics": "How to measure if mitigation is effective",
    "compliance_alignment": "Which standards/frameworks this supports"
}}
"""
                
                response = await llm_provider.generate(
                    prompt=mitigation_prompt,
                    system_prompt="You are a cybersecurity architect specializing in practical, implementable security controls."
                )
                
                mitigation_data = self._parse_mitigation_enhancement(response.content)
                
                # Update threat with enhanced mitigations
                enhanced_threat = threat.copy()
                enhanced_threat.update(mitigation_data)
                enhanced_threat["mitigation_enhancement_method"] = "llm_generated"
                
                enhanced_threats.append(enhanced_threat)
                
            except Exception as e:
                logger.warning(f"Mitigation enhancement failed for threat: {e}")
                enhanced_threats.append(threat)  # Keep original threat
        
        return enhanced_threats
    
    async def _control_aware_suppression(self, threats: List[Dict[str, Any]], threat_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suppress threats that are already mitigated by existing controls."""
        logger.info("Performing control-aware threat suppression")
        
        # This would integrate with a security controls database or configuration
        # For now, implement basic suppression logic
        
        active_threats = []
        suppressed_count = 0
        
        for threat in threats:
            suppress = False
            suppression_reason = ""
            
            # Example suppression logic (would be more sophisticated in practice)
            description_lower = threat.get("Description", "").lower()
            mitigation_lower = threat.get("Suggested Mitigation", "").lower()
            
            # Suppress if mitigation indicates control is already in place
            if any(phrase in mitigation_lower for phrase in [
                "already implemented", "current control", "existing measure"
            ]):
                suppress = True
                suppression_reason = "Existing control already addresses this threat"
            
            # Suppress very low risk threats in non-critical components
            if (threat.get("risk_score", "Medium") == "Low" and 
                threat.get("component_name", "").lower() not in ["database", "auth", "payment"]):
                suppress = True
                suppression_reason = "Low risk in non-critical component"
            
            if suppress:
                threat["suppressed"] = True
                threat["suppression_reason"] = suppression_reason
                suppressed_count += 1
                logger.debug(f"Suppressed threat: {suppression_reason}")
            else:
                active_threats.append(threat)
        
        logger.info(f"Suppressed {suppressed_count} threats based on control analysis")
        return active_threats
    
    async def _prioritize_threats(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Final threat prioritization and sorting."""
        logger.info("Performing final threat prioritization")
        
        # Add priority scoring
        for threat in threats:
            priority_score = self._calculate_priority_score(threat)
            threat["priority_score"] = priority_score
            threat["priority_ranking"] = self._get_priority_ranking(priority_score)
        
        # Sort by priority score (highest first)
        prioritized_threats = sorted(threats, key=lambda t: t.get("priority_score", 0), reverse=True)
        
        # Add ranking positions
        for i, threat in enumerate(prioritized_threats):
            threat["priority_rank"] = i + 1
        
        return prioritized_threats
    
    def _parse_similarity_groups(self, llm_response: str) -> List[Dict]:
        """Parse LLM response for similarity groups."""
        try:
            # Extract JSON from response
            if "```json" in llm_response:
                json_start = llm_response.find("```json") + 7
                json_end = llm_response.find("```", json_start)
                json_str = llm_response[json_start:json_end].strip()
            else:
                json_str = llm_response.strip()
            
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse similarity groups: {e}")
            return []
    
    def _parse_risk_assessment(self, llm_response: str) -> Dict:
        """Parse LLM risk assessment response."""
        try:
            if "```json" in llm_response:
                json_start = llm_response.find("```json") + 7
                json_end = llm_response.find("```", json_start)
                json_str = llm_response[json_start:json_end].strip()
            else:
                json_str = llm_response.strip()
            
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse risk assessment: {e}")
            return {}
    
    def _parse_business_risk(self, llm_response: str) -> Dict:
        """Parse LLM business risk translation response."""
        try:
            if "```json" in llm_response:
                json_start = llm_response.find("```json") + 7
                json_end = llm_response.find("```", json_start)
                json_str = llm_response[json_start:json_end].strip()
            else:
                json_str = llm_response.strip()
            
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse business risk: {e}")
            return {}
    
    def _parse_mitigation_enhancement(self, llm_response: str) -> Dict:
        """Parse LLM mitigation enhancement response."""
        try:
            if "```json" in llm_response:
                json_start = llm_response.find("```json") + 7
                json_end = llm_response.find("```", json_start)
                json_str = llm_response[json_start:json_end].strip()
            else:
                json_str = llm_response.strip()
            
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse mitigation enhancement: {e}")
            return {}
    
    def _merge_similar_threats(self, threats: List[Dict], similarity_groups: List[Dict]) -> List[Dict]:
        """Merge similar threats based on LLM analysis."""
        merged_threats = []
        merged_indices = set()
        
        # Process similarity groups
        for group in similarity_groups:
            try:
                indices = group.get("similar_threat_indices", [])
                primary_idx = group.get("primary_threat_index", indices[0] if indices else 0)
                
                if primary_idx < len(threats):
                    primary_threat = threats[primary_idx].copy()
                    
                    # Merge information from other threats in the group
                    for idx in indices:
                        if idx != primary_idx and idx < len(threats):
                            other_threat = threats[idx]
                            
                            # Combine references
                            primary_refs = set(primary_threat.get("references", []))
                            other_refs = set(other_threat.get("references", []))
                            primary_threat["references"] = list(primary_refs.union(other_refs))
                            
                            merged_indices.add(idx)
                    
                    primary_threat["merged_from"] = [threats[i].get("Threat Name", f"Threat {i}") 
                                                   for i in indices if i != primary_idx]
                    merged_threats.append(primary_threat)
                    merged_indices.add(primary_idx)
                    
            except Exception as e:
                logger.warning(f"Failed to merge similarity group: {e}")
        
        # Add non-merged threats
        for i, threat in enumerate(threats):
            if i not in merged_indices:
                merged_threats.append(threat)
        
        return merged_threats
    
    def _basic_deduplication(self, threats: List[Dict]) -> List[Dict]:
        """Fallback basic deduplication."""
        seen_descriptions = set()
        deduplicated = []
        
        for threat in threats:
            desc = threat.get("Description", "").strip().lower()
            if desc not in seen_descriptions:
                seen_descriptions.add(desc)
                deduplicated.append(threat)
        
        return deduplicated
    
    def _calculate_fallback_risk_score(self, impact: str, likelihood: str) -> str:
        """Calculate risk score using basic matrix."""
        return RISK_MATRIX.get((impact, likelihood), "Medium")
    
    def _calculate_priority_score(self, threat: Dict) -> float:
        """Calculate priority score for threat ranking."""
        # Base scores for risk levels
        risk_scores = {"Critical": 10, "High": 7, "Medium": 4, "Low": 1}
        base_score = risk_scores.get(threat.get("risk_score", "Medium"), 4)
        
        # Adjust based on additional factors
        if threat.get("exploitability") == "High":
            base_score += 2
        elif threat.get("exploitability") == "Low":
            base_score -= 1
        
        # Component criticality bonus
        component_name = threat.get("component_name", "").lower()
        if any(critical in component_name for critical in ["database", "auth", "payment", "admin"]):
            base_score += 1
        
        return base_score
    
    def _get_priority_ranking(self, score: float) -> str:
        """Convert priority score to ranking category."""
        if score >= 10:
            return "Critical"
        elif score >= 7:
            return "High" 
        elif score >= 4:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_risk_distribution(self, threats: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of threats by risk level."""
        distribution = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        
        for threat in threats:
            risk_score = threat.get("risk_score", "Medium")
            if risk_score in distribution:
                distribution[risk_score] += 1
        
        return distribution