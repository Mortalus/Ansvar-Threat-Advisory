"""
DFD Quality Enhancement System
Advanced two-stage DFD extraction with STRIDE Expert validation, confidence scoring, and security checklist.

This system significantly improves DFD extraction accuracy by:
1. STRIDE Expert Agent - Reviews initial DFD for missing security components
2. Confidence Scoring - Quantifies extraction certainty for each component
3. Security Validation Checklist - Systematic review of security architecture gaps
4. Pattern Recognition - Identifies common missing patterns
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from app.core.llm import get_llm_provider
from app.models.dfd import DFDComponents, DataFlow

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    PROCESS = "process"
    DATA_STORE = "data_store"  
    EXTERNAL_ENTITY = "external_entity"
    DATA_FLOW = "data_flow"
    TRUST_BOUNDARY = "trust_boundary"


@dataclass
class ConfidenceScore:
    component_name: str
    component_type: ComponentType
    confidence: float  # 0.0 to 1.0
    evidence: List[str]  # Text evidence supporting this component
    concerns: List[str]  # Reasons for low confidence


@dataclass
class SecurityGap:
    gap_type: str
    severity: str  # Critical, High, Medium, Low
    description: str
    missing_components: List[str]
    recommendation: str


@dataclass
class EnhancedDFDResult:
    enhanced_dfd: DFDComponents
    confidence_scores: List[ConfidenceScore]
    security_gaps: List[SecurityGap]
    expert_additions: Dict[str, List[str]]  # What the expert added
    validation_report: Dict[str, Any]


# Security-focused validation checklist
SECURITY_VALIDATION_CHECKLIST = [
    {
        "check_id": "authentication_service",
        "name": "Authentication Service",
        "question": "Is there an authentication/authorization service identified?",
        "required_for": ["web application", "api", "mobile app", "user interface"],
        "security_critical": True,
        "common_names": ["auth service", "identity provider", "oauth", "authentication", "login service", "sso"],
        "stride_categories": ["Spoofing", "Elevation of Privilege"]
    },
    {
        "check_id": "session_management",
        "name": "Session Management",
        "question": "Where are user sessions stored and managed?",
        "required_for": ["web application", "user session"],
        "security_critical": True,
        "common_names": ["session store", "redis", "session cache", "session management", "session database"],
        "stride_categories": ["Spoofing", "Tampering"]
    },
    {
        "check_id": "audit_logging",
        "name": "Audit Logging",
        "question": "Where are security events and audit trails logged?",
        "required_for": ["all"],
        "security_critical": True,
        "common_names": ["audit log", "security log", "event log", "activity log", "access log"],
        "stride_categories": ["Repudiation"]
    },
    {
        "check_id": "api_gateway",
        "name": "API Gateway/Proxy",
        "question": "Is there a gateway or proxy protecting backend services?",
        "required_for": ["api", "microservices", "external access"],
        "security_critical": True,
        "common_names": ["api gateway", "reverse proxy", "load balancer", "ingress controller"],
        "stride_categories": ["Spoofing", "Tampering", "Denial of Service"]
    },
    {
        "check_id": "encryption_key_management",
        "name": "Key Management",
        "question": "How are encryption keys and secrets managed?",
        "required_for": ["encryption", "certificates", "passwords"],
        "security_critical": True,
        "common_names": ["key management", "secret store", "vault", "hsm", "certificate store"],
        "stride_categories": ["Information Disclosure", "Tampering"]
    },
    {
        "check_id": "monitoring_alerting",
        "name": "Monitoring & Alerting",
        "question": "What monitors system health and security events?",
        "required_for": ["all"],
        "security_critical": False,
        "common_names": ["monitoring", "alerting", "metrics", "observability", "siem"],
        "stride_categories": ["Denial of Service", "Repudiation"]
    },
    {
        "check_id": "backup_recovery",
        "name": "Backup & Recovery",
        "question": "How is data backed up and disaster recovery handled?",
        "required_for": ["databases", "critical data"],
        "security_critical": False,
        "common_names": ["backup", "disaster recovery", "dr", "replication", "snapshot"],
        "stride_categories": ["Denial of Service", "Tampering"]
    },
    {
        "check_id": "network_security",
        "name": "Network Security Controls",
        "question": "What network security controls are in place?",
        "required_for": ["network boundaries"],
        "security_critical": True,
        "common_names": ["firewall", "waf", "network security", "security groups", "nacl"],
        "stride_categories": ["Spoofing", "Tampering", "Information Disclosure", "Denial of Service"]
    }
]


class STRIDEExpertAgent:
    """
    Expert Cybersecurity Architect specializing in STRIDE threat modeling.
    Reviews initial DFD extractions and identifies missing security-critical components.
    """
    
    def __init__(self):
        self.expert_prompt_template = """
You are a Senior Cybersecurity Architect with 15+ years of experience in STRIDE threat modeling and secure system design.

Your task: Review the initial DFD extraction and identify missing components that are CRITICAL for comprehensive security analysis.

EXPERTISE AREAS:
- STRIDE threat modeling methodology
- Security architecture patterns  
- Enterprise security controls
- Common attack vectors and mitigations

ORIGINAL DOCUMENT:
{document_text}

INITIAL DFD EXTRACTION:
{initial_dfd_json}

SECURITY REVIEW INSTRUCTIONS:

1. MISSING SECURITY ASSETS (Data Stores):
   - Are authentication stores (user DB, identity provider) identified?
   - Where are sessions stored? (Redis, session cache, memory)
   - Are audit logs and security logs represented?
   - What about key stores, certificate stores, secret management?
   - Are backup systems and DR storage identified?

2. MISSING SECURITY PROCESSES (Services/Functions):
   - Is there an authentication/authorization service?
   - What about API gateways, reverse proxies, load balancers?
   - Are security services like SIEM, monitoring, alerting included?
   - What about key management services, certificate authorities?
   - Are batch processes for security tasks (log rotation, cleanup) present?

3. MISSING SECURITY DATA FLOWS:
   - Authentication flows (login, token validation, session creation)
   - Logging flows (all services → audit logs)
   - Monitoring flows (metrics, health checks, alerts)
   - Key exchange and certificate validation flows
   - Backup and replication flows

4. MISSING TRUST BOUNDARIES:
   - Network segments (DMZ, internal, management networks)
   - Process boundaries (containerization, isolation)
   - Data classification boundaries (public, internal, confidential)
   - Administrative boundaries (different privilege levels)

5. STRIDE-SPECIFIC GAPS:
   - Spoofing: Identity verification points missing?
   - Tampering: Data integrity controls absent?
   - Repudiation: Non-repudiation mechanisms missing?
   - Information Disclosure: Data protection boundaries unclear?
   - Denial of Service: Availability controls missing?
   - Elevation of Privilege: Privilege boundaries undefined?

CRITICAL: Focus on components that would be TARGET for attacks but are missing from the DFD.

Output your findings as a JSON object with this structure:
{{
    "missing_assets": [
        {{
            "name": "Component name",
            "type": "data_store",
            "justification": "Why this is security-critical",
            "evidence": "Document evidence supporting this",
            "stride_relevance": ["Spoofing", "Tampering"]
        }}
    ],
    "missing_processes": [
        {{
            "name": "Service name", 
            "type": "process",
            "justification": "Security purpose",
            "evidence": "Document evidence",
            "stride_relevance": ["Elevation"]
        }}
    ],
    "missing_data_flows": [
        {{
            "source": "Source component",
            "destination": "Target component", 
            "data_description": "What flows",
            "justification": "Why security-critical",
            "protocol": "Expected protocol",
            "authentication_mechanism": "Auth method"
        }}
    ],
    "missing_trust_boundaries": [
        {{
            "name": "Boundary name",
            "components_inside": ["comp1", "comp2"],
            "security_purpose": "What it protects"
        }}
    ],
    "security_concerns": [
        {{
            "concern": "High-level security concern",
            "affected_components": ["comp1", "comp2"],
            "stride_categories": ["Spoofing", "Denial of Service"],
            "recommendation": "How to address"
        }}
    ]
}}

Be specific and justify each addition with evidence from the document.
"""
    
    async def review_dfd(
        self, 
        document_text: str, 
        initial_dfd: DFDComponents
    ) -> Dict[str, Any]:
        """Review initial DFD and identify missing security components."""
        
        # Prepare the prompt with context
        initial_dfd_json = initial_dfd.json(indent=2)
        
        prompt = self.expert_prompt_template.format(
            document_text=document_text,  # No character limit
            initial_dfd_json=initial_dfd_json
        )
        
        logger.info("STRIDE Expert Agent reviewing DFD for security gaps")
        
        try:
            # Get LLM provider for expert review
            llm_provider = await get_llm_provider("dfd_extraction")
            
            response = await llm_provider.generate(
                prompt=prompt,
                system_prompt="You are an expert security architect. Provide detailed JSON analysis of missing security components."
            )
            
            # Parse expert findings
            expert_findings = self._parse_expert_response(response.content)
            logger.info(f"STRIDE Expert identified {len(expert_findings.get('missing_assets', []))} missing assets, {len(expert_findings.get('missing_processes', []))} missing processes")
            
            return expert_findings
            
        except Exception as e:
            logger.error(f"STRIDE Expert review failed: {e}")
            return {
                "missing_assets": [],
                "missing_processes": [],
                "missing_data_flows": [],
                "missing_trust_boundaries": [],
                "security_concerns": [],
                "error": str(e)
            }
    
    def _parse_expert_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the STRIDE expert's JSON response."""
        try:
            # Clean response text
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks
            if "```json" in cleaned_text:
                start = cleaned_text.find("```json") + 7
                end = cleaned_text.rfind("```")
                cleaned_text = cleaned_text[start:end]
            elif "```" in cleaned_text:
                start = cleaned_text.find("```") + 3
                end = cleaned_text.rfind("```")
                cleaned_text = cleaned_text[start:end]
            
            # Find JSON object
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = cleaned_text[json_start:json_end]
                return json.loads(json_text)
            else:
                logger.warning("Could not find JSON in expert response")
                return self._create_empty_expert_response()
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse expert JSON response: {e}")
            return self._create_empty_expert_response()
    
    def _create_empty_expert_response(self) -> Dict[str, Any]:
        """Create empty expert response structure."""
        return {
            "missing_assets": [],
            "missing_processes": [],
            "missing_data_flows": [],
            "missing_trust_boundaries": [],
            "security_concerns": []
        }


class ConfidenceScorer:
    """Calculates confidence scores for extracted DFD components."""
    
    def __init__(self):
        self.explicit_mention_patterns = [
            r'\b{}\b',  # Exact word match
            r'\b{}\s+(?:service|server|system|component|application)\b',  # Component + type
            r'(?:using|with|via|through)\s+{}\b'  # Usage context
        ]
    
    def calculate_scores(
        self, 
        dfd: DFDComponents, 
        document_text: str
    ) -> List[ConfidenceScore]:
        """Calculate confidence scores for all DFD components."""
        
        scores = []
        doc_lower = document_text.lower()
        
        # Score external entities
        for entity in dfd.external_entities:
            score = self._score_component(entity, ComponentType.EXTERNAL_ENTITY, doc_lower)
            scores.append(score)
        
        # Score processes  
        for process in dfd.processes:
            score = self._score_component(process, ComponentType.PROCESS, doc_lower)
            scores.append(score)
        
        # Score assets (data stores)
        for asset in dfd.assets:
            score = self._score_component(asset, ComponentType.DATA_STORE, doc_lower)
            scores.append(score)
        
        # Score data flows
        for flow in dfd.data_flows:
            score = self._score_data_flow(flow, doc_lower)
            scores.append(score)
        
        # Score trust boundaries
        for boundary in dfd.trust_boundaries:
            score = self._score_component(boundary, ComponentType.TRUST_BOUNDARY, doc_lower)
            scores.append(score)
        
        return scores
    
    def _score_component(
        self, 
        component_name: str, 
        comp_type: ComponentType, 
        document_text: str
    ) -> ConfidenceScore:
        """Score an individual component."""
        
        evidence = []
        concerns = []
        base_confidence = 0.1
        
        comp_lower = component_name.lower()
        
        # Check for explicit mentions
        explicit_mentions = 0
        for pattern in self.explicit_mention_patterns:
            regex = pattern.format(re.escape(comp_lower))
            matches = re.findall(regex, document_text, re.IGNORECASE)
            explicit_mentions += len(matches)
            if matches:
                evidence.append(f"Explicitly mentioned {len(matches)} times")
        
        # Base confidence from explicit mentions
        confidence = min(0.9, base_confidence + explicit_mentions * 0.2)
        
        # Bonus for descriptive context
        context_patterns = [
            rf'{re.escape(comp_lower)}\s+(?:handles|manages|processes|stores|contains)',
            rf'(?:connect|access|query|call)\s+{re.escape(comp_lower)}',
            rf'{re.escape(comp_lower)}\s+(?:database|service|server|api|application)'
        ]
        
        for pattern in context_patterns:
            if re.search(pattern, document_text, re.IGNORECASE):
                confidence += 0.1
                evidence.append("Found in descriptive context")
        
        # Component type specific adjustments
        if comp_type == ComponentType.EXTERNAL_ENTITY:
            # External entities should be clearly mentioned
            if explicit_mentions == 0:
                confidence *= 0.5
                concerns.append("External entity not explicitly mentioned")
        
        elif comp_type == ComponentType.DATA_STORE:
            # Look for storage-related keywords
            storage_keywords = ['database', 'store', 'storage', 'repository', 'cache']
            if any(keyword in comp_lower for keyword in storage_keywords):
                confidence += 0.1
                evidence.append("Contains storage-related keywords")
        
        elif comp_type == ComponentType.PROCESS:
            # Look for process-related keywords
            process_keywords = ['service', 'server', 'application', 'api', 'engine']
            if any(keyword in comp_lower for keyword in process_keywords):
                confidence += 0.1
                evidence.append("Contains process-related keywords")
        
        # Penalize very generic names
        generic_names = ['system', 'component', 'service', 'application']
        if comp_lower in generic_names:
            confidence *= 0.6
            concerns.append("Very generic component name")
        
        # Cap confidence
        confidence = min(0.95, max(0.05, confidence))
        
        return ConfidenceScore(
            component_name=component_name,
            component_type=comp_type,
            confidence=confidence,
            evidence=evidence,
            concerns=concerns
        )
    
    def _score_data_flow(self, flow: DataFlow, document_text: str) -> ConfidenceScore:
        """Score a data flow."""
        evidence = []
        concerns = []
        base_confidence = 0.3  # Data flows are often inferred
        
        # Look for explicit flow descriptions
        flow_patterns = [
            rf'{re.escape(flow.source.lower())}.*(?:send|transmit|flow|pass).*{re.escape(flow.destination.lower())}',
            rf'{re.escape(flow.destination.lower())}.*(?:receive|get|fetch|pull).*{re.escape(flow.source.lower())}',
            rf'(?:from|via)\s+{re.escape(flow.source.lower())}\s+(?:to|into)\s+{re.escape(flow.destination.lower())}'
        ]
        
        confidence = base_confidence
        
        for pattern in flow_patterns:
            if re.search(pattern, document_text, re.IGNORECASE):
                confidence += 0.2
                evidence.append("Flow explicitly described in document")
                break
        
        # Check if both endpoints exist in document
        source_mentioned = flow.source.lower() in document_text.lower()
        dest_mentioned = flow.destination.lower() in document_text.lower()
        
        if source_mentioned and dest_mentioned:
            confidence += 0.2
            evidence.append("Both flow endpoints mentioned in document")
        elif source_mentioned or dest_mentioned:
            confidence += 0.1
            evidence.append("One flow endpoint mentioned in document")
        else:
            confidence *= 0.5
            concerns.append("Flow endpoints not clearly mentioned")
        
        # Check for protocol/authentication details
        if flow.protocol and flow.protocol != "Unknown":
            confidence += 0.1
            evidence.append(f"Protocol specified: {flow.protocol}")
        
        if flow.authentication_mechanism and flow.authentication_mechanism != "Unknown":
            confidence += 0.1
            evidence.append(f"Authentication specified: {flow.authentication_mechanism}")
        
        confidence = min(0.9, max(0.1, confidence))
        
        return ConfidenceScore(
            component_name=f"{flow.source} → {flow.destination}",
            component_type=ComponentType.DATA_FLOW,
            confidence=confidence,
            evidence=evidence,
            concerns=concerns
        )


class SecurityValidator:
    """Validates DFD against security architecture checklist."""
    
    def __init__(self):
        self.checklist = SECURITY_VALIDATION_CHECKLIST
    
    def validate(
        self, 
        dfd: DFDComponents, 
        document_text: str
    ) -> List[SecurityGap]:
        """Run security validation checklist against DFD."""
        
        gaps = []
        doc_lower = document_text.lower()
        
        # Get all components for searching
        all_components = (
            dfd.external_entities + 
            dfd.processes + 
            dfd.assets
        )
        all_components_lower = [comp.lower() for comp in all_components]
        
        for check in self.checklist:
            gap = self._validate_check(check, all_components_lower, doc_lower)
            if gap:
                gaps.append(gap)
        
        return gaps
    
    def _validate_check(
        self, 
        check: Dict[str, Any], 
        components: List[str], 
        document_text: str
    ) -> Optional[SecurityGap]:
        """Validate a single security check."""
        
        # Check if any component matches this security function
        found_components = []
        
        for common_name in check['common_names']:
            for component in components:
                if common_name in component or component in common_name:
                    found_components.append(component)
        
        # Also check document text for mentions
        doc_mentions = []
        for common_name in check['common_names']:
            if common_name in document_text:
                doc_mentions.append(common_name)
        
        # Determine if this is a gap
        is_gap = len(found_components) == 0 and len(doc_mentions) == 0
        
        # Check if required based on system type
        is_required = False
        if "all" in check['required_for']:
            is_required = True
        else:
            for req_type in check['required_for']:
                if req_type in document_text:
                    is_required = True
                    break
        
        if is_gap and is_required:
            severity = "Critical" if check['security_critical'] else "Medium"
            
            return SecurityGap(
                gap_type=check['check_id'],
                severity=severity,
                description=f"Missing {check['name']}: {check['question']}",
                missing_components=check['common_names'][:3],  # Top 3 expected names
                recommendation=f"Consider adding {check['name']} component to address {', '.join(check['stride_categories'])} threats"
            )
        
        return None


class DFDQualityEnhancer:
    """
    Main orchestrator for DFD quality enhancement.
    Coordinates STRIDE expert review, confidence scoring, and security validation.
    """
    
    def __init__(self):
        self.stride_expert = STRIDEExpertAgent()
        self.confidence_scorer = ConfidenceScorer()
        self.security_validator = SecurityValidator()
    
    async def enhance_dfd(
        self,
        document_text: str,
        initial_dfd: DFDComponents
    ) -> EnhancedDFDResult:
        """
        Enhance DFD extraction with expert review and validation.
        
        Args:
            document_text: Original document text
            initial_dfd: Initial DFD extraction result
            
        Returns:
            Enhanced DFD with confidence scores and security validation
        """
        
        logger.info("Starting DFD quality enhancement process")
        
        # Stage 1: STRIDE Expert Review
        expert_findings = await self.stride_expert.review_dfd(document_text, initial_dfd)
        
        # Stage 2: Apply Expert Recommendations
        enhanced_dfd = self._apply_expert_recommendations(initial_dfd, expert_findings)
        
        # Stage 3: Calculate Confidence Scores
        confidence_scores = self.confidence_scorer.calculate_scores(enhanced_dfd, document_text)
        
        # Stage 4: Security Validation
        security_gaps = self.security_validator.validate(enhanced_dfd, document_text)
        
        # Stage 5: Generate Validation Report
        validation_report = self._generate_validation_report(
            initial_dfd, enhanced_dfd, expert_findings, confidence_scores, security_gaps
        )
        
        logger.info(f"DFD enhancement complete: added {len(enhanced_dfd.processes) - len(initial_dfd.processes)} processes, "
                   f"{len(enhanced_dfd.assets) - len(initial_dfd.assets)} assets, "
                   f"identified {len(security_gaps)} security gaps")
        
        return EnhancedDFDResult(
            enhanced_dfd=enhanced_dfd,
            confidence_scores=confidence_scores,
            security_gaps=security_gaps,
            expert_additions={
                'processes': [item['name'] for item in expert_findings.get('missing_processes', [])],
                'assets': [item['name'] for item in expert_findings.get('missing_assets', [])],
                'data_flows': [f"{item['source']} → {item['destination']}" for item in expert_findings.get('missing_data_flows', [])],
                'trust_boundaries': [item['name'] for item in expert_findings.get('missing_trust_boundaries', [])]
            },
            validation_report=validation_report
        )
    
    def _apply_expert_recommendations(
        self, 
        initial_dfd: DFDComponents, 
        expert_findings: Dict[str, Any]
    ) -> DFDComponents:
        """Apply STRIDE expert recommendations to enhance the DFD."""
        
        # Create enhanced copy
        enhanced_data = initial_dfd.dict()
        
        # Add missing processes
        for process in expert_findings.get('missing_processes', []):
            if process['name'] not in enhanced_data['processes']:
                enhanced_data['processes'].append(process['name'])
        
        # Add missing assets
        for asset in expert_findings.get('missing_assets', []):
            if asset['name'] not in enhanced_data['assets']:
                enhanced_data['assets'].append(asset['name'])
        
        # Add missing data flows
        existing_flows = {f"{flow.source}→{flow.destination}" for flow in initial_dfd.data_flows}
        
        for flow_data in expert_findings.get('missing_data_flows', []):
            flow_key = f"{flow_data['source']}→{flow_data['destination']}"
            if flow_key not in existing_flows:
                new_flow = DataFlow(
                    source=flow_data['source'],
                    destination=flow_data['destination'],
                    data_description=flow_data.get('data_description', 'Security-related data'),
                    data_classification=flow_data.get('data_classification', 'Internal'),
                    protocol=flow_data.get('protocol', 'HTTPS'),
                    authentication_mechanism=flow_data.get('authentication_mechanism', 'Unknown')
                )
                enhanced_data['data_flows'].append(new_flow.dict())
        
        # Add missing trust boundaries
        for boundary in expert_findings.get('missing_trust_boundaries', []):
            if boundary['name'] not in enhanced_data['trust_boundaries']:
                enhanced_data['trust_boundaries'].append(boundary['name'])
        
        return DFDComponents(**enhanced_data)
    
    def _generate_validation_report(
        self,
        initial_dfd: DFDComponents,
        enhanced_dfd: DFDComponents,
        expert_findings: Dict[str, Any],
        confidence_scores: List[ConfidenceScore],
        security_gaps: List[SecurityGap]
    ) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        
        # Calculate improvements
        improvements = {
            'processes_added': len(enhanced_dfd.processes) - len(initial_dfd.processes),
            'assets_added': len(enhanced_dfd.assets) - len(initial_dfd.assets),
            'data_flows_added': len(enhanced_dfd.data_flows) - len(initial_dfd.data_flows),
            'trust_boundaries_added': len(enhanced_dfd.trust_boundaries) - len(initial_dfd.trust_boundaries)
        }
        
        # Calculate confidence statistics
        confidences = [score.confidence for score in confidence_scores]
        confidence_stats = {
            'average_confidence': sum(confidences) / len(confidences) if confidences else 0,
            'low_confidence_count': len([c for c in confidences if c < 0.5]),
            'high_confidence_count': len([c for c in confidences if c >= 0.8])
        }
        
        # Categorize security gaps
        critical_gaps = [gap for gap in security_gaps if gap.severity == "Critical"]
        high_gaps = [gap for gap in security_gaps if gap.severity == "High"]
        
        return {
            'enhancement_summary': improvements,
            'confidence_analysis': confidence_stats,
            'security_assessment': {
                'critical_gaps': len(critical_gaps),
                'high_priority_gaps': len(high_gaps),
                'total_gaps': len(security_gaps)
            },
            'expert_contributions': {
                'security_concerns_raised': len(expert_findings.get('security_concerns', [])),
                'recommendations_applied': sum(improvements.values())
            },
            'quality_score': self._calculate_quality_score(confidence_stats, len(security_gaps))
        }
    
    def _calculate_quality_score(self, confidence_stats: Dict[str, Any], gap_count: int) -> float:
        """Calculate overall DFD quality score (0-100)."""
        
        # Base score from confidence
        confidence_score = confidence_stats['average_confidence'] * 60
        
        # Bonus for high confidence components
        high_conf_bonus = min(20, confidence_stats['high_confidence_count'] * 2)
        
        # Penalty for security gaps
        gap_penalty = min(30, gap_count * 3)
        
        quality_score = confidence_score + high_conf_bonus - gap_penalty
        
        return max(0, min(100, quality_score))