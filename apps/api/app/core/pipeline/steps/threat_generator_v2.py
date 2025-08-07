"""
Enhanced Threat Generator V2: Context-Aware Risk Scoring with Controls Library

This improved version implements:
1. Controls Library - Parses document for existing security controls
2. Residual Risk Algorithm - Adjusts risk based on mitigating controls
3. Enhanced Threat Specificity - Component-bound threats with semantic deduplication
4. Threat Chains - Links threats to specific data flows and components

Part 1 of the three-stage threat modeling improvement plan.
"""

import json
import logging
import re
import difflib
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline import PipelineStepResult
from app.services.ingestion_service import IngestionService
from app.services.prompt_service import PromptService
from app.core.llm import get_llm_provider
from app.config import settings

logger = logging.getLogger(__name__)

# Enhanced STRIDE mapping with more specific threat patterns
COMPONENT_STRIDE_MAPPING = {
    'process': {
        'categories': ['S', 'T', 'R', 'I', 'D', 'E'],
        'specific_threats': [
            'input validation bypass',
            'authentication bypass', 
            'authorization failure',
            'code injection',
            'resource exhaustion'
        ]
    },
    'data_store': {
        'categories': ['T', 'R', 'I', 'D'],
        'specific_threats': [
            'data tampering',
            'unauthorized data access',
            'data exfiltration',
            'database injection',
            'backup exposure'
        ]
    },
    'external_entity': {
        'categories': ['S', 'R'],
        'specific_threats': [
            'identity spoofing',
            'session hijacking',
            'man-in-the-middle',
            'credential theft'
        ]
    },
    'data_flow': {
        'categories': ['T', 'I', 'D'],
        'specific_threats': [
            'data interception',
            'packet injection',
            'replay attacks',
            'eavesdropping',
            'protocol downgrade'
        ]
    }
}

# Security controls keywords for parsing documents
SECURITY_CONTROLS = {
    'authentication': {
        'keywords': ['oauth', 'jwt', 'mfa', '2fa', 'multi-factor', 'authentication', 'sso', 'ldap', 'saml', 'auth0'],
        'mitigates': ['Spoofing', 'Elevation'],
        'risk_reduction': 0.4
    },
    'encryption': {
        'keywords': ['tls', 'ssl', 'https', 'encrypted', 'encryption', 'aes', 'rsa', 'crypto', 'certificate'],
        'mitigates': ['Information Disclosure', 'Tampering'],
        'risk_reduction': 0.5
    },
    'access_control': {
        'keywords': ['rbac', 'acl', 'permission', 'authorization', 'access control', 'role-based', 'policy'],
        'mitigates': ['Elevation', 'Information Disclosure'],
        'risk_reduction': 0.4
    },
    'monitoring': {
        'keywords': ['audit', 'logging', 'monitoring', 'siem', 'detection', 'alert', 'alarm', 'log'],
        'mitigates': ['Repudiation', 'Tampering'],
        'risk_reduction': 0.3
    },
    'validation': {
        'keywords': ['validation', 'sanitization', 'whitelist', 'blacklist', 'input validation', 'parameterized', 'escape'],
        'mitigates': ['Tampering', 'Denial of Service'],
        'risk_reduction': 0.4
    },
    'rate_limiting': {
        'keywords': ['rate limit', 'throttling', 'quota', 'api limit', 'ddos protection', 'flood'],
        'mitigates': ['Denial of Service'],
        'risk_reduction': 0.5
    },
    'network_security': {
        'keywords': ['firewall', 'waf', 'ids', 'ips', 'vpn', 'bastion', 'dmz', 'segmentation', 'vlan'],
        'mitigates': ['Spoofing', 'Tampering', 'Information Disclosure'],
        'risk_reduction': 0.4
    },
    'backup': {
        'keywords': ['backup', 'disaster recovery', 'dr', 'replication', 'failover', 'redundancy'],
        'mitigates': ['Denial of Service', 'Tampering'],
        'risk_reduction': 0.3
    },
    'compliance': {
        'keywords': ['gdpr', 'pci', 'hipaa', 'sox', 'compliance', 'regulation', 'standard', 'iso27001'],
        'mitigates': ['Information Disclosure', 'Repudiation'],
        'risk_reduction': 0.2
    }
}

# Risk scoring matrix for residual risk calculation
RISK_SCORING = {
    'impact_scores': {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1},
    'likelihood_scores': {'High': 3, 'Medium': 2, 'Low': 1},
    'risk_levels': {
        12: 'Critical',  # 4x3
        9: 'Critical',   # 3x3
        8: 'High',       # 4x2
        6: 'High',       # 3x2, 2x3
        4: 'Medium',     # 4x1, 2x2
        3: 'Medium',     # 3x1
        2: 'Low',        # 2x1
        1: 'Low'         # 1x1
    }
}


class ControlsLibrary:
    """Parses and manages security controls found in documentation."""
    
    def __init__(self):
        self.detected_controls = {}
        self.control_effectiveness = {}
        
    def parse_document_for_controls(self, document_text: str) -> Dict[str, List[str]]:
        """Parse document to identify security controls mentioned."""
        document_lower = document_text.lower()
        detected = {}
        
        for control_type, control_info in SECURITY_CONTROLS.items():
            found_keywords = []
            for keyword in control_info['keywords']:
                if keyword in document_lower:
                    # Find context around keyword
                    pattern = r'.{0,50}' + re.escape(keyword) + r'.{0,50}'
                    matches = re.findall(pattern, document_lower, re.IGNORECASE)
                    if matches:
                        found_keywords.append({
                            'keyword': keyword,
                            'context': matches[0].strip(),
                            'control_type': control_type
                        })
            
            if found_keywords:
                detected[control_type] = found_keywords
                logger.info(f"Detected {control_type} controls: {[k['keyword'] for k in found_keywords]}")
        
        self.detected_controls = detected
        return detected
    
    def get_control_effectiveness(self, threat_category: str, component_type: str) -> float:
        """Calculate effectiveness of controls against specific threat."""
        total_reduction = 0.0
        applicable_controls = []
        
        for control_type, keywords in self.detected_controls.items():
            control_info = SECURITY_CONTROLS[control_type]
            # Check if this control mitigates this threat type
            if any(threat_category.lower() in mitigation.lower() for mitigation in control_info['mitigates']):
                reduction = control_info['risk_reduction']
                # Adjust based on component type
                if component_type == 'data_flow' and control_type in ['encryption', 'network_security']:
                    reduction *= 1.2  # More effective for data flows
                elif component_type == 'data_store' and control_type in ['access_control', 'encryption']:
                    reduction *= 1.2  # More effective for data stores
                
                total_reduction += reduction
                applicable_controls.append(control_type)
        
        # Cap total reduction at 0.7 (30% minimum residual risk)
        total_reduction = min(total_reduction, 0.7)
        
        if applicable_controls:
            logger.debug(f"Controls {applicable_controls} provide {total_reduction:.1%} reduction for {threat_category}")
        
        return total_reduction


class ResidualRiskCalculator:
    """Calculates residual risk after considering controls."""
    
    def __init__(self, controls_library: ControlsLibrary):
        self.controls = controls_library
    
    def calculate_residual_risk(
        self, 
        threat: Dict[str, Any],
        component_type: str
    ) -> Dict[str, Any]:
        """Calculate residual risk considering controls."""
        
        # Get inherent risk scores
        impact = threat.get('Potential Impact', 'Medium')
        likelihood = threat.get('Likelihood', 'Medium')
        threat_category = threat.get('Threat Category', 'Unknown')
        
        # Calculate control effectiveness
        control_reduction = self.controls.get_control_effectiveness(threat_category, component_type)
        
        # Calculate inherent risk score
        impact_score = RISK_SCORING['impact_scores'].get(impact, 2)
        likelihood_score = RISK_SCORING['likelihood_scores'].get(likelihood, 2)
        inherent_risk_score = impact_score * likelihood_score
        
        # Apply control reduction to likelihood (controls reduce probability)
        adjusted_likelihood_score = max(1, likelihood_score * (1 - control_reduction))
        residual_risk_score = impact_score * adjusted_likelihood_score
        
        # Determine residual risk level
        residual_risk_level = 'Medium'
        for score_threshold in sorted(RISK_SCORING['risk_levels'].keys(), reverse=True):
            if residual_risk_score >= score_threshold:
                residual_risk_level = RISK_SCORING['risk_levels'][score_threshold]
                break
        
        # Build enhanced threat with residual risk
        enhanced_threat = threat.copy()
        enhanced_threat.update({
            'inherent_risk': self._get_risk_level(inherent_risk_score),
            'residual_risk': residual_risk_level,
            'risk_reduction': f"{control_reduction:.0%}",
            'applicable_controls': list(self.controls.detected_controls.keys()) if control_reduction > 0 else [],
            'residual_likelihood': self._get_likelihood_from_score(adjusted_likelihood_score)
        })
        
        return enhanced_threat
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level."""
        for score_threshold in sorted(RISK_SCORING['risk_levels'].keys(), reverse=True):
            if score >= score_threshold:
                return RISK_SCORING['risk_levels'][score_threshold]
        return 'Low'
    
    def _get_likelihood_from_score(self, score: float) -> str:
        """Convert likelihood score back to text."""
        if score >= 2.5:
            return 'High'
        elif score >= 1.5:
            return 'Medium'
        else:
            return 'Low'


class ThreatSpecificityEnhancer:
    """Ensures threats are specific and bound to components."""
    
    def __init__(self):
        self.threat_chains = []
    
    def create_threat_chain(
        self,
        threat: Dict[str, Any],
        component: Dict[str, Any],
        data_flows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create specific threat chain linking components and data flows."""
        
        component_name = component.get('name', 'Unknown')
        component_type = component.get('type', 'component')
        
        # Find related data flows
        related_flows = []
        for flow in data_flows:
            if component_name in str(flow.get('source', '')) or component_name in str(flow.get('destination', '')):
                related_flows.append(flow.get('name', flow.get('id', 'flow')))
        
        # Build specific threat description
        threat_chain = {
            'component': {
                'name': component_name,
                'type': component_type,
                'id': component.get('id', '')
            },
            'data_flows': related_flows[:3],  # Limit to 3 most relevant
            'attack_vector': self._identify_attack_vector(threat, component_type),
            'kill_chain_phase': self._map_to_kill_chain(threat.get('Threat Category', ''))
        }
        
        # Enhance threat with specificity
        enhanced_threat = threat.copy()
        enhanced_threat['threat_chain'] = threat_chain
        
        # Make description more specific
        if threat_chain['data_flows']:
            flow_context = f" through {', '.join(threat_chain['data_flows'][:2])}"
        else:
            flow_context = ""
        
        original_desc = threat.get('Description', '')
        if 'could' in original_desc.lower() or 'might' in original_desc.lower():
            # Replace vague language
            specific_desc = original_desc.replace('An attacker could', f'An attacker targeting {component_name} could')
            specific_desc = specific_desc.replace('might be able to', f'could exploit {component_name}{flow_context} to')
            enhanced_threat['Description'] = specific_desc
        
        return enhanced_threat
    
    def _identify_attack_vector(self, threat: Dict[str, Any], component_type: str) -> str:
        """Identify specific attack vector based on threat and component."""
        threat_name = threat.get('Threat Name', '').lower()
        
        if 'injection' in threat_name or 'sql' in threat_name:
            return 'Code/Command Injection'
        elif 'spoof' in threat_name or 'identity' in threat_name:
            return 'Identity Attack'
        elif 'dos' in threat_name or 'denial' in threat_name:
            return 'Resource Exhaustion'
        elif 'tamper' in threat_name:
            return 'Data Manipulation'
        elif 'disclosure' in threat_name or 'leak' in threat_name:
            return 'Information Leakage'
        elif 'elevation' in threat_name or 'privilege' in threat_name:
            return 'Privilege Escalation'
        else:
            return 'General Exploitation'
    
    def _map_to_kill_chain(self, threat_category: str) -> str:
        """Map STRIDE to cyber kill chain phase."""
        category_upper = threat_category.upper()
        
        if 'S' in category_upper:
            return 'Initial Access'
        elif 'E' in category_upper:
            return 'Privilege Escalation'
        elif 'T' in category_upper:
            return 'Execution'
        elif 'I' in category_upper:
            return 'Collection'
        elif 'D' in category_upper:
            return 'Impact'
        elif 'R' in category_upper:
            return 'Defense Evasion'
        else:
            return 'Unknown'


class SemanticDeduplicator:
    """Advanced deduplication using semantic similarity."""
    
    def __init__(self, similarity_threshold: float = 0.75):
        self.threshold = similarity_threshold
        self.duplicate_groups = []
    
    def deduplicate_threats(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate threats using semantic similarity."""
        if not threats:
            return []
        
        unique_threats = []
        processed_indices = set()
        
        for i, threat in enumerate(threats):
            if i in processed_indices:
                continue
            
            # Find similar threats
            similar_group = [threat]
            similar_indices = {i}
            
            for j, other in enumerate(threats[i+1:], i+1):
                if j in processed_indices:
                    continue
                
                if self._are_semantically_similar(threat, other):
                    similar_group.append(other)
                    similar_indices.add(j)
            
            # Merge similar threats into best one
            best_threat = self._merge_threat_group(similar_group)
            unique_threats.append(best_threat)
            processed_indices.update(similar_indices)
            
            if len(similar_group) > 1:
                logger.info(f"Merged {len(similar_group)} similar threats into: {best_threat.get('Threat Name', 'Unknown')}")
        
        return unique_threats
    
    def _are_semantically_similar(self, threat1: Dict, threat2: Dict) -> bool:
        """Check if two threats are semantically similar."""
        # Must be same component and category
        if (threat1.get('component_name') != threat2.get('component_name') or
            threat1.get('Threat Category') != threat2.get('Threat Category')):
            return False
        
        # Compare descriptions
        desc1 = self._normalize_text(threat1.get('Description', ''))
        desc2 = self._normalize_text(threat2.get('Description', ''))
        
        # Use sequence matcher for similarity
        similarity = difflib.SequenceMatcher(None, desc1, desc2).ratio()
        
        # Also check threat names
        name1 = self._normalize_text(threat1.get('Threat Name', ''))
        name2 = self._normalize_text(threat2.get('Threat Name', ''))
        name_similarity = difflib.SequenceMatcher(None, name1, name2).ratio()
        
        # Combined similarity check
        return similarity > self.threshold or name_similarity > 0.8
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Remove common words and normalize
        text = re.sub(r'\b(the|a|an|could|might|may|can)\b', '', text.lower())
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()
    
    def _merge_threat_group(self, threats: List[Dict]) -> Dict:
        """Merge similar threats, keeping best information."""
        if len(threats) == 1:
            return threats[0]
        
        # Start with threat that has most detail
        best_threat = max(threats, key=lambda t: len(t.get('Description', '')))
        
        # Merge mitigations from all threats
        all_mitigations = []
        for threat in threats:
            mitigation = threat.get('Suggested Mitigation', '')
            if mitigation and mitigation not in all_mitigations:
                all_mitigations.append(mitigation)
        
        if len(all_mitigations) > 1:
            best_threat['Suggested Mitigation'] = ' Additionally, '.join(all_mitigations[:2])
        
        # Take highest risk scores
        for threat in threats:
            if RISK_SCORING['impact_scores'].get(threat.get('Potential Impact', 'Low'), 1) > \
               RISK_SCORING['impact_scores'].get(best_threat.get('Potential Impact', 'Low'), 1):
                best_threat['Potential Impact'] = threat['Potential Impact']
        
        # Note the deduplication
        best_threat['deduplicated_count'] = len(threats)
        
        return best_threat


class ThreatGeneratorV2:
    """
    Enhanced threat generator with context-aware risk scoring.
    Implements Controls Library, Residual Risk, and Threat Specificity.
    """
    
    def __init__(self):
        self.controls_library = ControlsLibrary()
        self.deduplicator = SemanticDeduplicator()
        self.specificity_enhancer = ThreatSpecificityEnhancer()
        
        try:
            self.ingestion_service = IngestionService()
        except Exception as e:
            logger.warning(f"Failed to initialize IngestionService: {e}")
            self.ingestion_service = None
    
    async def execute(
        self,
        db_session: AsyncSession,
        pipeline_step_result: Optional[PipelineStepResult],
        component_data: Dict[str, Any],
        document_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute enhanced threat generation with context-aware risk scoring.
        
        Args:
            db_session: Database session
            pipeline_step_result: Current pipeline step result
            component_data: DFD component data
            document_text: Original document text for control parsing
            
        Returns:
            Enhanced threats with residual risk assessment
        """
        try:
            logger.info("Starting Threat Generator V2 with context-aware risk scoring")
            
            # Step 1: Parse document for security controls
            if document_text:
                detected_controls = self.controls_library.parse_document_for_controls(document_text)
                logger.info(f"Detected {len(detected_controls)} types of security controls")
            else:
                logger.warning("No document text provided, proceeding without control detection")
                detected_controls = {}
            
            # Initialize residual risk calculator
            risk_calculator = ResidualRiskCalculator(self.controls_library)
            
            # Get prompt template
            prompt_service = PromptService(db_session)
            prompt_template = await prompt_service.get_active_prompt("threat_generation")
            if not prompt_template:
                await prompt_service.initialize_default_prompts()
                prompt_template = await prompt_service.get_active_prompt("threat_generation")
            
            # Extract components and data flows
            components = self._extract_components(component_data)
            data_flows = component_data.get('data_flows', [])
            
            # Step 2: Generate threats for high-risk components
            all_threats = []
            components_analyzed = 0
            
            # Process components concurrently for better performance
            import asyncio
            
            selected_components = components[:15]  # Focus on top components
            logger.info(f"Processing {len(selected_components)} components concurrently...")
            
            async def process_component(component):
                """Process a single component for threats."""
                component_type = component.get('type', 'process')
                
                # Get applicable STRIDE categories
                stride_info = COMPONENT_STRIDE_MAPPING.get(
                    component_type,
                    {'categories': ['S', 'T', 'I'], 'specific_threats': []}
                )
                
                # Generate component-specific threats
                return await self._generate_specific_threats(
                    component,
                    stride_info,
                    prompt_template
                )
            
            # Create concurrent tasks for all components
            component_tasks = [process_component(comp) for comp in selected_components]
            
            # Execute all component analysis concurrently
            start_time = asyncio.get_event_loop().time()
            component_results = await asyncio.gather(*component_tasks, return_exceptions=True)
            execution_time = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"Completed {len(selected_components)} components in {execution_time:.1f}s (concurrent)")
            
            # Process results from concurrent execution
            for component, component_threats in zip(selected_components, component_results):
                if isinstance(component_threats, Exception):
                    logger.error(f"Component {component.get('name', 'unknown')} failed: {component_threats}")
                    continue
                    
                if not component_threats:
                    continue
                
                # Get component type for this component
                component_type = component.get('type', 'process')
                
                # Step 3: Calculate residual risk for each threat
                enhanced_threats = []
                for threat in component_threats:
                    # Calculate residual risk
                    threat_with_residual = risk_calculator.calculate_residual_risk(
                        threat,
                        component_type
                    )
                    
                    # Enhance threat specificity
                    specific_threat = self.specificity_enhancer.create_threat_chain(
                        threat_with_residual,
                        component,
                        data_flows
                    )
                    
                    enhanced_threats.append(specific_threat)
                
                all_threats.extend(enhanced_threats)
                components_analyzed += 1
            
            logger.info(f"Generated {len(all_threats)} threats for {components_analyzed} components")
            
            # Step 4: Semantic deduplication
            unique_threats = self.deduplicator.deduplicate_threats(all_threats)
            logger.info(f"After deduplication: {len(unique_threats)} unique threats")
            
            # Step 5: Filter to focus on high residual risk
            high_risk_threats = [
                t for t in unique_threats 
                if t.get('residual_risk') in ['Critical', 'High', 'Medium']
            ]
            
            # Sort by residual risk
            risk_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
            high_risk_threats.sort(
                key=lambda t: risk_order.get(t.get('residual_risk', 'Low'), 0),
                reverse=True
            )
            
            # Prepare result
            result = {
                "threats": high_risk_threats,
                "total_count": len(high_risk_threats),
                "components_analyzed": components_analyzed,
                "security_controls_detected": list(detected_controls.keys()),
                "control_coverage": {
                    "authentication": "authentication" in detected_controls,
                    "encryption": "encryption" in detected_controls,
                    "access_control": "access_control" in detected_controls,
                    "monitoring": "monitoring" in detected_controls,
                    "network_security": "network_security" in detected_controls
                },
                "risk_metrics": {
                    "total_threats_generated": len(all_threats),
                    "post_deduplication": len(unique_threats),
                    "high_residual_risk": len([t for t in high_risk_threats if t.get('residual_risk') in ['Critical', 'High']]),
                    "controls_effectiveness": self._calculate_overall_effectiveness(high_risk_threats)
                },
                "version": "2.0"
            }
            
            # Update pipeline step result
            if pipeline_step_result:
                pipeline_step_result.result_data = result
                pipeline_step_result.status = "completed"
                pipeline_step_result.prompt_id = prompt_template.id if prompt_template else None
            
            await db_session.commit()
            
            logger.info(f"Threat Generator V2 completed: {len(high_risk_threats)} context-aware threats")
            return result
            
        except Exception as e:
            logger.error(f"Error in Threat Generator V2: {str(e)}")
            if pipeline_step_result:
                pipeline_step_result.status = "failed"
                pipeline_step_result.error = str(e)
            await db_session.commit()
            raise
    
    async def _generate_specific_threats(
        self,
        component: Dict[str, Any],
        stride_info: Dict[str, Any],
        prompt_template
    ) -> List[Dict[str, Any]]:
        """Generate specific threats for a component."""
        
        component_name = component.get('name', 'Unknown')
        component_type = component.get('type', 'component')
        categories = stride_info['categories']
        specific_patterns = stride_info['specific_threats']
        
        # Build focused prompt with CWE context if available
        cwe_context_text = ""
        if 'cwe_context' in component:
            cwe_info = component['cwe_context']
            cwe_context_text = f"""

CWE Knowledge Base Context:
{cwe_info.get('context_summary', 'No CWE context available')}

When generating threats, consider these known vulnerability patterns and their exploit likelihoods.
"""
        
        prompt = f"""
Analyze this specific component for security threats:

Component: {component_name}
Type: {component_type}
Description: {component.get('description', 'No description')}

Focus on these STRIDE categories: {', '.join(categories)}
Consider these specific threat patterns: {', '.join(specific_patterns[:3])}{cwe_context_text}

Generate 3-5 highly specific, realistic threats. Avoid generic language.
For each threat, provide:
- Threat Category (from STRIDE)  
- Threat Name (specific attack name)
- Description (detailed attack scenario for THIS component)
- Potential Impact (Critical/High/Medium/Low)
- Likelihood (High/Medium/Low) 
- Suggested Mitigation (specific technical controls)

Return as JSON array. Be specific to the component - mention it by name.
"""
        
        try:
            llm_provider = await get_llm_provider("threat_generation")
            response = await llm_provider.generate(
                prompt=prompt,
                system_prompt="You are a security expert. Generate specific, technical threats. Avoid vague language."
            )
            
            threats = self._parse_threats(response.content, component)
            return threats  # Return all threats
            
        except Exception as e:
            logger.error(f"Failed to generate threats for {component_name}: {e}")
            return []
    
    def _parse_threats(self, llm_response: str, component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse threat response from LLM."""
        threats = []
        
        try:
            # Extract JSON from response
            if "```json" in llm_response:
                json_start = llm_response.find("```json") + 7
                json_end = llm_response.find("```", json_start)
                json_str = llm_response[json_start:json_end].strip()
            else:
                json_str = llm_response.strip()
            
            parsed = json.loads(json_str)
            
            if isinstance(parsed, dict):
                parsed = [parsed]
            
            for threat in parsed:
                if isinstance(threat, dict):
                    threat['component_id'] = component.get('id', '')
                    threat['component_name'] = component.get('name', 'Unknown')
                    threat['component_type'] = component.get('type', 'Unknown')
                    threats.append(threat)
                    
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse threats: {e}")
        
        return threats
    
    def _extract_components(self, component_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and prioritize components."""
        components = []
        
        for comp_type in ["processes", "external_entities", "data_stores", "data_flows"]:
            if comp_type in component_data:
                for comp in component_data[comp_type]:
                    if isinstance(comp, str):
                        comp = {"name": comp, "id": f"{comp_type}_{len(components)}"}
                    elif not isinstance(comp, dict):
                        continue
                    
                    comp = comp.copy()
                    comp["type"] = comp_type.rstrip("s")
                    components.append(comp)
        
        return components
    
    def _calculate_overall_effectiveness(self, threats: List[Dict[str, Any]]) -> str:
        """Calculate overall control effectiveness."""
        if not threats:
            return "0%"
        
        total_reduction = 0
        for threat in threats:
            reduction_str = threat.get('risk_reduction', '0%')
            try:
                reduction = float(reduction_str.rstrip('%')) / 100
                total_reduction += reduction
            except:
                pass
        
        avg_reduction = total_reduction / len(threats) if threats else 0
        return f"{avg_reduction:.0%}"