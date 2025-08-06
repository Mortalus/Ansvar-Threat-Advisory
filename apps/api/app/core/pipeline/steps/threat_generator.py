"""
Enhanced threat generation step: LLM prompts as primary, RAG as quality enhancement.
Integrates sophisticated risk assessment, quality control, and realistic threat generation.
"""
import json
import logging
import difflib
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline import PipelineStepResult
from app.services.ingestion_service import IngestionService
from app.services.prompt_service import PromptService
from app.core.llm import get_llm_provider
from app.config import settings

logger = logging.getLogger(__name__)

# Component-Specific STRIDE Mappings for focused analysis
COMPONENT_STRIDE_MAPPING = {
    'process': ['S', 'T', 'R', 'I', 'D', 'E'],  # All STRIDE categories
    'data_store': ['T', 'R', 'I', 'D'],  # No Spoofing or Elevation typically
    'external_entity': ['S'],  # Primarily Spoofing concerns
    'data_flow': ['T', 'I', 'D'],  # Tampering, Info Disclosure, DoS
}

# Risk-based threat limits per component type
MAX_THREATS_PER_COMPONENT = {
    'process': 3,
    'data_store': 3, 
    'external_entity': 2,
    'data_flow': 2
}

# Risk assessment keywords for component prioritization
HIGH_RISK_KEYWORDS = [
    'database', 'db', 'store', 'repository', 'cache',
    'authentication', 'auth', 'login', 'user',
    'payment', 'financial', 'money', 'transaction',
    'admin', 'management', 'control',
    'api', 'service', 'server',
    'external', 'third-party', 'internet'
]

TRUST_BOUNDARY_KEYWORDS = [
    'external', 'internet', 'public', 'client',
    'browser', 'mobile', 'api', 'web'
]


class ThreatGenerator:
    """
    Enhanced threat generator: LLM prompts as primary, RAG as quality enhancement.
    Includes risk assessment, quality control, and sophisticated deduplication.
    """
    
    def __init__(self):
        try:
            self.ingestion_service = IngestionService()
        except Exception as e:
            logger.warning(f"Failed to initialize IngestionService: {e}")
            logger.info("RAG functionality will be disabled, using LLM-only threat generation")
            self.ingestion_service = None
        
    def _calculate_component_risk_score(self, component: Dict[str, Any]) -> int:
        """Calculate risk score for component prioritization."""
        score = 1  # Base score
        
        name = component.get('name', '').lower()
        comp_type = component.get('type', '').lower()
        details = str(component.get('details', {})).lower()
        
        # High-risk component types
        if 'data' in comp_type or 'store' in comp_type:
            score += 3
        elif 'external' in comp_type or 'entity' in comp_type:
            score += 2
        elif 'process' in comp_type:
            score += 1
        
        # Check for high-risk keywords
        text_to_check = f"{name} {comp_type} {details}"
        for keyword in HIGH_RISK_KEYWORDS:
            if keyword in text_to_check:
                score += 2
                break
        
        # Trust boundary crossing
        for keyword in TRUST_BOUNDARY_KEYWORDS:
            if keyword in text_to_check:
                score += 2
                break
        
        return min(score, 10)  # Cap at 10
    
    def _get_applicable_stride_categories(self, component_type: str) -> List[str]:
        """Get only the applicable STRIDE categories for a component type."""
        normalized_type = component_type.lower().replace(' ', '_')
        return COMPONENT_STRIDE_MAPPING.get(normalized_type, ['S', 'T', 'I'])  # Safe default
    
    def _normalize_text_for_comparison(self, text: str) -> str:
        """Normalize text for threat similarity comparison."""
        import re
        text = re.sub(r'\s+', ' ', text.lower().strip())
        text = re.sub(r'\b(an?|the)\b', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        return text
    
    def _are_similar_threats(self, threat1: Dict, threat2: Dict, threshold: float = 0.7) -> bool:
        """Check if two threats are semantically similar."""
        desc1 = self._normalize_text_for_comparison(threat1.get('Description', ''))
        desc2 = self._normalize_text_for_comparison(threat2.get('Description', ''))
        
        # Same component and STRIDE category
        if (threat1.get('component_name') == threat2.get('component_name') and 
            threat1.get('Threat Category') == threat2.get('Threat Category')):
            
            similarity = difflib.SequenceMatcher(None, desc1, desc2).ratio()
            return similarity > threshold
        
        return False
    
    def _advanced_threat_deduplication(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Advanced deduplication based on semantic similarity."""
        unique_threats = []
        processed_indices: Set[int] = set()
        
        for i, threat in enumerate(threats):
            if i in processed_indices:
                continue
            
            # Find similar threats
            similar_threats = [threat]
            for j, other_threat in enumerate(threats[i+1:], i+1):
                if j not in processed_indices and self._are_similar_threats(threat, other_threat):
                    similar_threats.append(other_threat)
                    processed_indices.add(j)
            
            # Keep the threat with highest impact
            impact_order = {'High': 3, 'Medium': 2, 'Low': 1}
            best_threat = max(similar_threats, 
                             key=lambda t: impact_order.get(t.get('Potential Impact', 'Low'), 0))
            
            unique_threats.append(best_threat)
            processed_indices.add(i)
        
        return unique_threats
    
    def _filter_quality_threats(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out low-quality or generic threats using RAG validation."""
        GENERIC_PHRASES = [
            'an attacker could',
            'unauthorized access', 
            'malicious user might',
            'potential security risk',
            'vulnerability may exist'
        ]
        
        MIN_DESCRIPTION_LENGTH = 50
        quality_threats = []
        
        for threat in threats:
            description = threat.get('Description', '').lower()
            
            # Skip if too short
            if len(description) < MIN_DESCRIPTION_LENGTH:
                continue
            
            # Skip if too generic (more than 2 generic phrases)
            generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase in description)
            if generic_count > 2:
                continue
            
            # Skip if mitigation is too vague
            mitigation = threat.get('Suggested Mitigation', '')
            if len(mitigation) < 30 or 'implement security measures' in mitigation.lower():
                continue
            
            quality_threats.append(threat)
        
        return quality_threats
    
    def _enhance_threats_with_rag_context(self, threats: List[Dict[str, Any]], rag_context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use RAG context to enhance threat quality and add specific intelligence."""
        if not rag_context:
            return threats
        
        # Create a knowledge base of relevant threats from RAG
        rag_techniques = {}
        for ctx in rag_context:
            technique_id = ctx.get('technique_id', 'Unknown')
            if technique_id != 'Unknown':
                rag_techniques[technique_id] = ctx
        
        # Enhance threats with RAG intelligence
        enhanced_threats = []
        for threat in threats:
            enhanced_threat = threat.copy()
            
            # Try to match threat to RAG context for enhancement
            description = threat.get('Description', '').lower()
            for technique_id, rag_data in rag_techniques.items():
                rag_content = rag_data.get('content', '').lower()
                
                # Simple keyword matching - could be made more sophisticated
                if any(word in rag_content for word in description.split()[:5]):
                    # Add RAG-sourced enhancements
                    enhanced_threat['rag_technique_id'] = technique_id
                    enhanced_threat['rag_source'] = rag_data.get('source', 'Unknown')
                    
                    # Enhance mitigation with specific intelligence
                    current_mitigation = enhanced_threat.get('Suggested Mitigation', '')
                    if 'requiredAction' in rag_data:
                        enhanced_mitigation = f"{current_mitigation} Additionally, based on {rag_data.get('source', 'threat intelligence')}: {rag_data.get('requiredAction', '')}"
                        enhanced_threat['Suggested Mitigation'] = enhanced_mitigation
                    break
            
            enhanced_threats.append(enhanced_threat)
        
        return enhanced_threats
    
    async def _generate_component_threats_with_llm(
        self, 
        component: Dict[str, Any], 
        applicable_stride: List[str],
        max_threats: int,
        prompt_template
    ) -> List[Dict[str, Any]]:
        """Generate primary threats for a component using LLM with enhanced prompts."""
        
        # Build enhanced component information
        component_info = f"""- Type: {component.get('type', 'Unknown')}
- Name: {component.get('name', 'Unknown')}
- Description: {component.get('description', 'No description provided')}
- Risk Score: {component.get('_risk_score', 1)}/10
- Applicable STRIDE Categories: {', '.join(applicable_stride)}"""
        
        # Create focused prompt for this component
        enhanced_prompt = f"""
Analyze this component for security threats:

{component_info}

Focus specifically on these STRIDE categories: {', '.join(applicable_stride)}

Generate up to {max_threats} realistic, specific threats. For each threat, provide:
1. Threat Category (from applicable STRIDE categories)
2. Threat Name (specific and descriptive)
3. Description (detailed attack scenario)
4. Potential Impact (High/Medium/Low)
5. Likelihood (High/Medium/Low)
6. Suggested Mitigation (specific and actionable)

Return as JSON array with each threat as an object using these exact field names:
"Threat Category", "Threat Name", "Description", "Potential Impact", "Likelihood", "Suggested Mitigation"
"""
        
        # Generate threats using LLM
        llm_provider = await get_llm_provider("threat_generation")
        
        system_prompt = """You are a cybersecurity expert specializing in threat modeling using the STRIDE methodology. 
Generate realistic, specific, and actionable security threats. Focus on practical attack scenarios that could realistically occur.
Avoid generic threats - be specific to the component type and context provided."""
        
        response = await llm_provider.generate(
            prompt=enhanced_prompt,
            system_prompt=system_prompt
        )
        
        # Log the actual LLM response for debugging
        logger.info(f"LLM Response for component {component.get('name', 'Unknown')}: {response.content[:500]}...")
        
        # Parse and validate threats
        threats = self._parse_threats(response.content, component)
        
        # Filter to only include applicable STRIDE categories
        filtered_threats = []
        for threat in threats:
            threat_category = threat.get('Threat Category', '').upper()
            if any(stride_cat in threat_category for stride_cat in applicable_stride):
                filtered_threats.append(threat)
        
        # Limit to max_threats
        return filtered_threats[:max_threats]
        
    async def execute(
        self, 
        db_session: AsyncSession,
        pipeline_step_result: Optional[PipelineStepResult],
        component_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute enhanced threat generation: LLM prompts as primary, RAG as quality enhancement.
        
        Args:
            db_session: Database session
            pipeline_step_result: The current pipeline step result to update
            component_data: DFD component data to analyze
            
        Returns:
            Generated threats with sophisticated quality control and RAG enhancement
        """
        try:
            logger.info("Starting enhanced threat generation with quality control")
            
            # Get the active prompt template
            prompt_service = PromptService(db_session)
            prompt_template = await prompt_service.get_active_prompt("threat_generation")
            
            if not prompt_template:
                # Initialize default prompts if not found
                await prompt_service.initialize_default_prompts()
                prompt_template = await prompt_service.get_active_prompt("threat_generation")
            
            # Extract and prioritize components by risk
            components = self._extract_components(component_data)
            
            # Calculate risk scores and prioritize
            for component in components:
                component['_risk_score'] = self._calculate_component_risk_score(component)
            
            # Sort by risk score (highest first) and filter high-risk components
            components.sort(key=lambda x: x.get('_risk_score', 0), reverse=True)
            high_risk_components = [c for c in components if c.get('_risk_score', 0) >= 3]
            
            # Limit to top components for quality over quantity
            max_components = 20  # Configurable limit
            if len(high_risk_components) > max_components:
                high_risk_components = high_risk_components[:max_components]
            
            logger.info(f"Analyzing {len(high_risk_components)} high-risk components (filtered from {len(components)} total)")
            
            all_threats = []
            all_rag_context = []
            
            for component in high_risk_components:
                # Get applicable STRIDE categories for this component type
                applicable_stride = self._get_applicable_stride_categories(component.get('type', ''))
                max_threats = MAX_THREATS_PER_COMPONENT.get(component.get('type', ''), 3)
                
                # Step 1: Generate primary threats using LLM with enhanced prompts
                component_threats = await self._generate_component_threats_with_llm(
                    component, applicable_stride, max_threats, prompt_template
                )
                
                # Step 2: Search RAG for enhancement context (secondary role)
                query = self._formulate_query(component)
                logger.info(f"Searching knowledge base for enhancement context: {query}")
                
                try:
                    if self.ingestion_service:
                        relevant_context = await self.ingestion_service.search_similar(
                            query=query,
                            limit=3  # Reduced limit since RAG is for enhancement, not primary generation
                        )
                        all_rag_context.extend(relevant_context)
                    else:
                        logger.info("RAG search skipped - service not available")
                        relevant_context = []
                except Exception as e:
                    logger.warning(f"RAG search failed for component {component.get('name', 'Unknown')}: {e}")
                    logger.info("Continuing with LLM-only threat generation")
                    relevant_context = []
                
                # Step 3: Enhance threats with RAG intelligence (quality enhancement)
                if relevant_context:
                    component_threats = self._enhance_threats_with_rag_context(
                        component_threats, relevant_context
                    )
                
                all_threats.extend(component_threats)
                logger.info(f"Generated {len(component_threats)} threats for component: {component.get('name', 'Unknown')}")
            
            logger.info(f"Pre-quality control: {len(all_threats)} threats generated")
            
            # Step 4: Apply sophisticated quality control and deduplication
            # Filter out low-quality threats
            quality_threats = self._filter_quality_threats(all_threats)
            logger.info(f"After quality filtering: {len(quality_threats)} threats remaining")
            
            # Apply advanced deduplication
            final_threats = self._advanced_threat_deduplication(quality_threats)
            logger.info(f"After deduplication: {len(final_threats)} unique threats")
            
            # Store results in pipeline step
            result = {
                "threats": final_threats,
                "total_count": len(final_threats),
                "components_analyzed": len(high_risk_components),
                "total_components": len(components),
                "knowledge_sources_used": list(set([
                    ctx.get("source", "Unknown") 
                    for ctx in all_rag_context
                ])),
                "quality_metrics": {
                    "pre_quality_filter": len(all_threats),
                    "post_quality_filter": len(quality_threats),
                    "post_deduplication": len(final_threats),
                    "quality_improvement": f"{((len(quality_threats) / len(all_threats)) * 100):.1f}%" if all_threats else "0%"
                }
            }
            
            # Update pipeline step result with versioning information (if provided)
            if pipeline_step_result:
                pipeline_step_result.result_data = result
                pipeline_step_result.status = "completed"
                pipeline_step_result.prompt_id = prompt_template.id
                pipeline_step_result.llm_model = getattr(settings, 'default_llm_provider', 'mock')
            
            await db_session.commit()
            
            logger.info(f"Generated {len(final_threats)} final threats for {len(high_risk_components)} components using prompt version {prompt_template.version}")
            return result
            
        except Exception as e:
            logger.error(f"Error in threat generation: {str(e)}")
            if pipeline_step_result:
                pipeline_step_result.status = "failed"
                pipeline_step_result.error = str(e)
            await db_session.commit()
            raise
    
    def _extract_components(self, component_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract individual components from DFD data."""
        components = []
        
        # Extract different types of components
        for comp_type in ["processes", "external_entities", "data_stores", "data_flows"]:
            if comp_type in component_data:
                for comp in component_data[comp_type]:
                    # Ensure comp is a dictionary
                    if isinstance(comp, str):
                        # Convert string to dictionary
                        comp = {
                            "name": comp,
                            "description": f"Component: {comp}",
                            "id": f"{comp_type}_{len(components)}"
                        }
                    elif not isinstance(comp, dict):
                        logger.warning(f"Unexpected component type {type(comp)}: {comp}")
                        continue
                    
                    # Make a copy to avoid modifying the original data
                    comp = comp.copy()
                    comp["type"] = comp_type.rstrip("s")  # Remove plural 's'
                    components.append(comp)
        
        return components
    
    def _formulate_query(self, component: Dict[str, Any]) -> str:
        """
        Formulate a search query for finding relevant threat intelligence.
        
        Args:
            component: DFD component to analyze
            
        Returns:
            Search query string
        """
        comp_type = component.get("type", "component")
        name = component.get("name", "Unknown")
        description = component.get("description", "")
        
        # Build query based on component attributes
        query_parts = []
        
        # Add component type-specific keywords
        if comp_type == "process":
            query_parts.append("process vulnerability attack")
        elif comp_type == "external_entity":
            query_parts.append("external entity threat actor")
        elif comp_type == "data_store":
            query_parts.append("data storage database vulnerability")
        elif comp_type == "data_flow":
            query_parts.append("data transmission communication vulnerability")
        
        # Add component name and description
        query_parts.append(name)
        if description:
            # Take first 50 characters of description
            query_parts.append(description[:50])
        
        # Add STRIDE categories for comprehensive search
        query_parts.append("spoofing tampering repudiation information disclosure denial of service elevation of privilege")
        
        return " ".join(query_parts)
    
    
    def _parse_threats(self, llm_response: str, component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse threats from LLM response.
        
        Args:
            llm_response: Raw LLM response
            component: Component the threats are for
            
        Returns:
            List of structured threat dictionaries
        """
        threats = []
        
        try:
            # Try to parse as JSON
            if "```json" in llm_response:
                # Extract JSON from markdown code block
                json_start = llm_response.find("```json") + 7
                json_end = llm_response.find("```", json_start)
                json_str = llm_response[json_start:json_end].strip()
            else:
                # Assume entire response is JSON
                json_str = llm_response.strip()
            
            logger.debug(f"Parsing JSON string: {json_str[:200]}...")
            parsed_threats = json.loads(json_str)
            logger.debug(f"Parsed threats type: {type(parsed_threats)}, content: {parsed_threats}")
            
            # Ensure it's a list
            if isinstance(parsed_threats, dict):
                parsed_threats = [parsed_threats]
            
            # Add component reference to each threat
            for threat in parsed_threats:
                # Ensure threat is a dictionary
                if not isinstance(threat, dict):
                    logger.warning(f"Expected dict but got {type(threat)}: {threat}")
                    continue
                    
                threat["component_id"] = component.get("id", "")
                threat["component_name"] = component.get("name", "Unknown")
                threat["component_type"] = component.get("type", "Unknown")
                threats.append(threat)
                
        except json.JSONDecodeError:
            # Fallback: Create a simple threat from the text
            logger.warning("Failed to parse JSON from LLM response, using fallback")
            threat = {
                "threat_category": "Unknown",
                "threat_name": "Potential Security Risk",
                "description": llm_response[:500],
                "potential_impact": "Medium",
                "likelihood": "Medium",
                "suggested_mitigation": "Review and assess this component for security risks",
                "component_id": component.get("id", ""),
                "component_name": component.get("name", "Unknown"),
                "component_type": component.get("type", "Unknown")
            }
            threats.append(threat)
        
        return threats