"""
Optimized AI-First Threat Refinement Step

High-performance version that reduces LLM calls and processing time while maintaining quality:
- Batched LLM processing to reduce API calls
- Focus on highest-risk threats for detailed analysis
- Simplified processing pipeline
- Better error handling and fallbacks
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

RISK_PRIORITY_SCORES = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1
}

class ThreatRefiner:
    """
    High-performance threat refinement using batched LLM processing.
    """
    
    def __init__(self):
        # Services will be initialized only when needed
        self.ingestion_service = None
        self.prompt_service = None
    
    async def execute(
        self,
        db_session: AsyncSession,
        pipeline_step_result: Optional[PipelineStepResult],
        threat_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute optimized threat refinement.
        
        Args:
            db_session: Database session
            pipeline_step_result: Previous step result (not used)
            threat_data: Input threat data from threat generation
            
        Returns:
            Refined threat data with enhanced analysis
        """
        threats = threat_data.get("threats", [])
        components = threat_data.get("components_analyzed", 0)
        
        if not threats:
            return {
                "refined_threats": [],
                "total_count": 0,
                "refinement_stats": {
                    "original_count": 0,
                    "deduplicated_count": 0,
                    "final_count": 0,
                    "risk_distribution": {},
                    "refinement_timestamp": datetime.utcnow().isoformat()
                }
            }
        
        logger.info(f"Starting optimized threat refinement for {len(threats)} threats")
        
        try:
            # Phase 1: Quick semantic deduplication using string similarity
            deduplicated_threats = self._quick_deduplication(threats)
            
            # Phase 2: Batch risk assessment for top threats
            risk_assessed_threats = await self._batch_risk_assessment(deduplicated_threats)
            
            # Phase 3: Business context for critical threats only
            business_enhanced_threats = await self._selective_business_enhancement(risk_assessed_threats)
            
            # Phase 4: Simple prioritization
            final_threats = self._prioritize_and_rank(business_enhanced_threats)
            
            # Generate statistics
            stats = self._generate_stats(threats, deduplicated_threats, final_threats)
            
            logger.info(f"Optimized refinement complete: {len(final_threats)} refined threats")
            
            return {
                "refined_threats": final_threats,
                "total_count": len(final_threats),
                "refinement_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Threat refinement failed: {e}")
            # Return original threats with minimal enhancement
            fallback_threats = self._apply_fallback_enhancements(threats)
            
            return {
                "refined_threats": fallback_threats,
                "total_count": len(fallback_threats),
                "refinement_stats": {
                    "original_count": len(threats),
                    "deduplicated_count": 0,
                    "final_count": len(fallback_threats),
                    "risk_distribution": self._count_risk_distribution(fallback_threats),
                    "refinement_timestamp": datetime.utcnow().isoformat(),
                    "refinement_method": "fallback"
                }
            }
    
    def _quick_deduplication(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fast deduplication using string similarity."""
        logger.info(f"Quick deduplication of {len(threats)} threats")
        
        unique_threats = []
        seen_signatures = set()
        
        for threat in threats:
            # Create signature from key fields
            name = threat.get("Threat Name", "").lower().strip()
            description = threat.get("Description", "").lower().strip()[:100]
            component = threat.get("component_name", "").lower().strip()
            
            signature = f"{name}|{component}|{description}"
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_threats.append(threat)
            else:
                logger.debug(f"Deduplicated threat: {name} on {component}")
        
        logger.info(f"Deduplication reduced {len(threats)} to {len(unique_threats)} threats")
        return unique_threats
    
    async def _batch_risk_assessment(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform batch risk assessment on threats."""
        logger.info(f"Batch risk assessment for {len(threats)} threats")
        
        # Process all threats in one batch to minimize LLM calls
        try:
            # Build threat summary for batch processing
            threat_summaries = []
            for idx, threat in enumerate(threats[:15]):  # Limit to 15 threats for performance
                summary = f"Threat {idx+1}: {threat.get('Threat Name', 'Unknown')} - {threat.get('component_name', 'Unknown')} - {threat.get('Potential Impact', 'Medium')}/{threat.get('Likelihood', 'Medium')}"
                threat_summaries.append(summary)
            
            if not threat_summaries:
                return threats
            
            batch_prompt = f"""
Assess risk levels for these cybersecurity threats. Return a JSON array with risk scores:

{chr(10).join(threat_summaries)}

For each threat, provide:
[
    {{"risk_score": "Critical|High|Medium|Low", "priority_rank": 1-5, "exploitability": "High|Medium|Low"}}
]
"""
            
            llm_provider = await get_llm_provider("threat_refinement")
            logger.debug(f"Risk assessment prompt length: {len(batch_prompt)} characters")
            llm_response = await llm_provider.generate(batch_prompt)
            response = llm_response.content
            
            # Parse response and apply to threats
            enhanced_threats = []
            
            try:
                response_text = response.strip()
                
                # Clean up common LLM response issues
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                # Log the response for debugging
                logger.debug(f"LLM risk assessment response: {response_text[:200]}...")
                
                if not response_text:
                    logger.warning("LLM returned empty response for risk assessment")
                    raise json.JSONDecodeError("Empty response", "", 0)
                
                risk_assessments = json.loads(response_text)
                
                for idx, threat in enumerate(threats):
                    enhanced_threat = threat.copy()
                    
                    if idx < len(risk_assessments) and idx < 15:
                        assessment = risk_assessments[idx]
                        enhanced_threat.update({
                            "risk_score": assessment.get("risk_score", "Medium"),
                            "priority_rank": assessment.get("priority_rank", 3),
                            "exploitability": assessment.get("exploitability", "Medium"),
                            "risk_assessment_method": "batch_llm"
                        })
                    else:
                        # Fallback for remaining threats
                        enhanced_threat.update({
                            "risk_score": self._calculate_fallback_risk_score(
                                threat.get("Potential Impact", "Medium"),
                                threat.get("Likelihood", "Medium")
                            ),
                            "priority_rank": 3,
                            "risk_assessment_method": "fallback"
                        })
                    
                    enhanced_threats.append(enhanced_threat)
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse batch risk assessment: {e}")
                # Apply fallback to all threats
                enhanced_threats = []
                for threat in threats:
                    enhanced_threat = threat.copy()
                    enhanced_threat.update({
                        "risk_score": self._calculate_fallback_risk_score(
                            threat.get("Potential Impact", "Medium"),
                            threat.get("Likelihood", "Medium")
                        ),
                        "risk_assessment_method": "fallback"
                    })
                    enhanced_threats.append(enhanced_threat)
            
            return enhanced_threats
            
        except Exception as e:
            logger.warning(f"Batch risk assessment failed: {e}")
            # Return threats with fallback scoring
            for threat in threats:
                threat["risk_score"] = self._calculate_fallback_risk_score(
                    threat.get("Potential Impact", "Medium"),
                    threat.get("Likelihood", "Medium")
                )
                threat["risk_assessment_method"] = "fallback"
            return threats
    
    async def _selective_business_enhancement(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add business context to top 5 critical/high threats only."""
        logger.info("Adding business context to top threats")
        
        # Identify top critical/high threats
        critical_threats = [t for t in threats if t.get("risk_score") in ["Critical", "High"]][:5]
        
        if not critical_threats:
            # No critical threats, just add minimal business context
            for threat in threats:
                threat["business_risk_statement"] = f"Technical threat affecting {threat.get('component_name', 'system component')}"
                threat["business_enhancement_method"] = "minimal"
            return threats
        
        try:
            # Build summary for top threats
            threat_summaries = []
            for idx, threat in enumerate(critical_threats):
                summary = f"Threat {idx+1}: {threat.get('Threat Name', 'Unknown')} on {threat.get('component_name', 'Unknown')} - Risk: {threat.get('risk_score', 'Medium')}"
                threat_summaries.append(summary)
            
            business_prompt = f"""
Translate these top cybersecurity threats into business risk language:

{chr(10).join(threat_summaries)}

Return JSON array with business statements:
[
    {{"business_risk_statement": "Clear business risk in 1-2 sentences"}}
]
"""
            
            llm_provider = await get_llm_provider("threat_refinement")
            logger.debug(f"Business statements prompt length: {len(business_prompt)} characters")
            llm_response = await llm_provider.generate(business_prompt)
            response = llm_response.content
            
            try:
                response_text = response.strip()
                
                # Clean up common LLM response issues
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                # Log the response for debugging
                logger.debug(f"LLM business statements response: {response_text[:200]}...")
                
                if not response_text:
                    logger.warning("LLM returned empty response for business statements")
                    raise json.JSONDecodeError("Empty response", "", 0)
                
                business_statements = json.loads(response_text)
                
                # Apply business statements to critical threats
                enhanced_threats = []
                critical_idx = 0
                
                for threat in threats:
                    enhanced_threat = threat.copy()
                    
                    if threat in critical_threats and critical_idx < len(business_statements):
                        statement = business_statements[critical_idx]
                        enhanced_threat.update({
                            "business_risk_statement": statement.get("business_risk_statement", ""),
                            "business_enhancement_method": "llm_enhanced"
                        })
                        critical_idx += 1
                    else:
                        enhanced_threat.update({
                            "business_risk_statement": f"Technical threat affecting {threat.get('component_name', 'system component')}",
                            "business_enhancement_method": "standard"
                        })
                    
                    enhanced_threats.append(enhanced_threat)
                
                return enhanced_threats
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse business statements: {e}")
                # Apply standard business context
                for threat in threats:
                    threat["business_risk_statement"] = f"Technical threat affecting {threat.get('component_name', 'system component')}"
                    threat["business_enhancement_method"] = "fallback"
                return threats
                
        except Exception as e:
            logger.warning(f"Business enhancement failed: {e}")
            # Apply minimal business context
            for threat in threats:
                threat["business_risk_statement"] = f"Technical threat affecting {threat.get('component_name', 'system component')}"
                threat["business_enhancement_method"] = "fallback"
            return threats
    
    def _prioritize_and_rank(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple prioritization based on risk scores."""
        logger.info("Prioritizing and ranking threats")
        
        # Sort by risk score
        sorted_threats = sorted(
            threats,
            key=lambda t: RISK_PRIORITY_SCORES.get(t.get("risk_score", "Medium"), 2),
            reverse=True
        )
        
        # Add priority rankings
        for idx, threat in enumerate(sorted_threats):
            threat["priority_rank"] = idx + 1
            threat["priority_ranking"] = f"#{idx + 1}"
            
            # Add simple mitigation priority
            risk_score = threat.get("risk_score", "Medium")
            if risk_score == "Critical":
                threat["implementation_priority"] = "Immediate"
            elif risk_score == "High":
                threat["implementation_priority"] = "High"
            elif risk_score == "Medium":
                threat["implementation_priority"] = "Medium"
            else:
                threat["implementation_priority"] = "Low"
        
        return sorted_threats
    
    def _calculate_fallback_risk_score(self, impact: str, likelihood: str) -> str:
        """Calculate fallback risk score using matrix."""
        return RISK_MATRIX.get((impact, likelihood), "Medium")
    
    def _apply_fallback_enhancements(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply minimal enhancements when LLM processing fails."""
        enhanced_threats = []
        
        for idx, threat in enumerate(threats):
            enhanced_threat = threat.copy()
            enhanced_threat.update({
                "risk_score": self._calculate_fallback_risk_score(
                    threat.get("Potential Impact", "Medium"),
                    threat.get("Likelihood", "Medium")
                ),
                "priority_rank": idx + 1,
                "business_risk_statement": f"Technical threat affecting {threat.get('component_name', 'system component')}",
                "refinement_method": "fallback"
            })
            enhanced_threats.append(enhanced_threat)
        
        return enhanced_threats
    
    def _count_risk_distribution(self, threats: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count threats by risk level."""
        distribution = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        
        for threat in threats:
            risk_level = threat.get("risk_score", "Medium")
            if risk_level in distribution:
                distribution[risk_level] += 1
        
        return distribution
    
    def _generate_stats(self, original: List, deduplicated: List, final: List) -> Dict[str, Any]:
        """Generate refinement statistics."""
        return {
            "original_count": len(original),
            "deduplicated_count": len(original) - len(deduplicated),
            "final_count": len(final),
            "risk_distribution": self._count_risk_distribution(final),
            "refinement_timestamp": datetime.utcnow().isoformat(),
            "refinement_method": "optimized_batch"
        }