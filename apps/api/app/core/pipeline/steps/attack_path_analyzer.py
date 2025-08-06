"""
Modern Attack Path Analyzer for Threat Modeling Pipeline
Analyzes refined threats to identify and score potential attack chains

Integrated with the pipeline, uses existing LLM providers, and stores results in database.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.llm.base import BaseLLMProvider
from app.core.llm import get_llm_provider

logger = logging.getLogger(__name__)

# Data Models
@dataclass
class AttackStep:
    """Represents a single step in an attack path."""
    step_number: int
    component: str
    threat_id: str
    threat_description: str
    stride_category: str
    technique_id: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)
    enables: List[str] = field(default_factory=list)
    required_access: Optional[str] = None
    detection_difficulty: Optional[str] = None

@dataclass
class AttackPath:
    """Represents a complete attack path from entry to target."""
    path_id: str
    scenario_name: str
    entry_point: str
    target_asset: str
    path_steps: List[AttackStep]
    total_steps: int
    combined_likelihood: str
    combined_impact: str
    path_feasibility: str = "Realistic"
    attacker_profile: str = "Cybercriminal"
    time_to_compromise: str = "Days"
    key_chokepoints: List[str] = field(default_factory=list)
    detection_opportunities: List[str] = field(default_factory=list)
    required_resources: List[str] = field(default_factory=list)
    path_complexity: str = "Medium"

@dataclass
class DefensePriority:
    """Represents a prioritized defensive recommendation."""
    type: str
    recommendation: str
    impact: str
    priority: str
    effort: str
    category: str
    affected_paths: int = 0

class ComponentGraph:
    """Lightweight graph for component relationships."""
    
    def __init__(self):
        self.nodes: Dict[str, Dict] = {}
        self.edges: Dict[str, List[Tuple[str, Dict]]] = defaultdict(list)
        self.reverse_edges: Dict[str, List[Tuple[str, Dict]]] = defaultdict(list)
    
    def add_node(self, node: str, **attrs):
        """Add a node with attributes."""
        self.nodes[node] = attrs
    
    def add_edge(self, source: str, dest: str, **attrs):
        """Add an edge with attributes."""
        self.edges[source].append((dest, attrs))
        self.reverse_edges[dest].append((source, attrs))
    
    def has_node(self, node: str) -> bool:
        """Check if node exists."""
        return node in self.nodes
    
    def predecessors(self, node: str) -> List[str]:
        """Get predecessors of a node."""
        return [src for src, _ in self.reverse_edges[node]]
    
    def successors(self, node: str) -> List[str]:
        """Get successors of a node."""
        return [dest for dest, _ in self.edges[node]]
    
    def degree(self, node: str) -> int:
        """Get degree of a node."""
        return len(self.edges[node]) + len(self.reverse_edges[node])
    
    def find_paths(self, start: str, end: str, max_length: int = 5) -> List[List[str]]:
        """Find all simple paths between start and end."""
        if start not in self.nodes or end not in self.nodes:
            return []
        
        paths = []
        queue = deque([(start, [start])])
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) > max_length:
                continue
            
            if current == end and len(path) > 1:
                paths.append(path)
                continue
            
            for neighbor, _ in self.edges[current]:
                if neighbor not in path:  # Avoid cycles
                    new_path = path + [neighbor]
                    queue.append((neighbor, new_path))
        
        return paths
    
    def shortest_path(self, start: str, end: str) -> Optional[List[str]]:
        """Find shortest path using BFS."""
        if start not in self.nodes or end not in self.nodes:
            return None
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            if current == end:
                return path
            
            for neighbor, _ in self.edges[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None

class AttackPathAnalyzer:
    """Modern attack path analyzer integrated with the pipeline."""
    
    def __init__(self, max_path_length: int = 5, max_paths_to_analyze: int = 20):
        self.max_path_length = max_path_length
        self.max_paths_to_analyze = max_paths_to_analyze
        self.logger = logging.getLogger(f"{__name__}.AttackPathAnalyzer")
        self.llm_provider: Optional[BaseLLMProvider] = None
        
    async def execute(
        self,
        db_session: AsyncSession,
        pipeline_step_result: Optional[Dict[str, Any]],
        refined_threats: List[Dict[str, Any]],
        dfd_components: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main execution method for attack path analysis.
        
        Args:
            db_session: Database session
            pipeline_step_result: Previous pipeline step results (unused)
            refined_threats: List of refined threats from threat refinement step
            dfd_components: DFD components from DFD extraction step
            
        Returns:
            Attack path analysis results
        """
        self.logger.info("Starting attack path analysis")
        
        try:
            # Initialize LLM provider
            self.llm_provider = await get_llm_provider(step="attack_path_analysis")
            
            # Build component graph from DFD
            graph = self._build_component_graph(dfd_components)
            
            # Map threats to components
            component_threats = self._map_threats_to_components(refined_threats, graph)
            
            # Identify entry points and critical assets
            entry_points = self._identify_entry_points(graph, dfd_components)
            critical_assets = self._identify_critical_assets(graph, dfd_components)
            
            self.logger.info(f"Found {len(entry_points)} entry points and {len(critical_assets)} critical assets")
            
            # Find attack paths
            raw_paths = self._find_attack_paths(graph, entry_points, critical_assets)
            
            # Build detailed attack paths
            attack_paths = await self._build_detailed_attack_paths(
                raw_paths, component_threats, refined_threats
            )
            
            # Enrich with LLM analysis if available
            if self.llm_provider:
                attack_paths = await self._enrich_attack_paths(attack_paths, dfd_components)
            
            # Sort by criticality
            attack_paths = self._prioritize_attack_paths(attack_paths)
            
            # Generate defense priorities
            defense_priorities = self._generate_defense_priorities(attack_paths)
            
            # Calculate threat coverage
            threat_coverage = self._calculate_threat_coverage(attack_paths, refined_threats)
            
            # Identify critical scenarios
            critical_scenarios = self._identify_critical_scenarios(attack_paths)
            
            self.logger.info(f"Analysis complete: {len(attack_paths)} attack paths, "
                           f"{len(critical_scenarios)} critical scenarios")
            
            return {
                "attack_paths": [self._serialize_attack_path(path) for path in attack_paths[:self.max_paths_to_analyze]],
                "critical_scenarios": critical_scenarios,
                "defense_priorities": [self._serialize_defense_priority(dp) for dp in defense_priorities],
                "threat_coverage": threat_coverage,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_paths_found": len(raw_paths),
                    "detailed_paths_built": len(attack_paths),
                    "total_threats": len(refined_threats),
                    "entry_points": entry_points[:10],
                    "critical_assets": critical_assets[:10],
                    "max_path_length": self.max_path_length,
                    "llm_enrichment_enabled": self.llm_provider is not None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Attack path analysis failed: {e}")
            raise
    
    def _build_component_graph(self, dfd_components: Dict[str, Any]) -> ComponentGraph:
        """Build a directed graph of system components from DFD."""
        graph = ComponentGraph()
        
        # Add external entities
        for entity in dfd_components.get('external_entities', []):
            graph.add_node(entity, type='external_entity', 
                          criticality='high' if 'user' in entity.lower() else 'medium',
                          trust_level='untrusted')
            
        # Add processes
        for process in dfd_components.get('processes', []):
            graph.add_node(process, type='process', criticality='medium',
                          trust_level='semi-trusted')
            
        # Add assets/data stores
        for asset in dfd_components.get('assets', []):
            graph.add_node(asset, type='asset', criticality='critical',
                          trust_level='trusted')
            
        # Add edges from data flows
        for flow in dfd_components.get('data_flows', []):
            if isinstance(flow, dict) and 'source' in flow and 'destination' in flow:
                source = flow['source']
                dest = flow['destination']
                
                if graph.has_node(source) and graph.has_node(dest):
                    graph.add_edge(
                        source, dest,
                        data_classification=flow.get('data_classification', 'Unknown'),
                        protocol=flow.get('protocol', 'Unknown'),
                        authentication=flow.get('authentication_mechanism', 'Unknown')
                    )
                    
                    # Add reverse edge for bidirectional communication
                    graph.add_edge(dest, source,
                                 data_classification=flow.get('data_classification', 'Unknown'),
                                 protocol=flow.get('protocol', 'Unknown'))
                    
        self.logger.info(f"Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        return graph
    
    def _map_threats_to_components(
        self, 
        refined_threats: List[Dict[str, Any]], 
        graph: ComponentGraph
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Map threats to their components."""
        component_threats = defaultdict(list)
        
        for threat in refined_threats:
            components = self._extract_components_from_threat(threat, graph)
            for component in components:
                component_threats[component].append(threat)
                
        self.logger.info(f"Mapped threats to {len(component_threats)} components")
        return dict(component_threats)
    
    def _extract_components_from_threat(
        self, 
        threat: Dict[str, Any], 
        graph: ComponentGraph
    ) -> List[str]:
        """Extract components mentioned in a threat."""
        components = []
        
        # Primary component
        component_name = threat.get('component_name', '')
        if component_name and graph.has_node(component_name):
            components.append(component_name)
        
        # Handle data flow format "A to B"
        if ' to ' in component_name:
            parts = [p.strip() for p in component_name.split(' to ')]
            for part in parts:
                if graph.has_node(part):
                    components.append(part)
        
        # Check threat description for component mentions
        description = threat.get('threat_description', '').lower()
        for node in graph.nodes:
            if node.lower() in description and node not in components:
                components.append(node)
                
        return components
    
    def _identify_entry_points(
        self, 
        graph: ComponentGraph, 
        dfd_components: Dict[str, Any]
    ) -> List[str]:
        """Identify potential entry points."""
        entry_points = []
        
        for node in graph.nodes:
            node_data = graph.nodes[node]
            score = 0
            
            # External entities are primary entry points
            if node_data.get('type') == 'external_entity':
                score += 10
                
            # Untrusted components
            if node_data.get('trust_level') == 'untrusted':
                score += 5
                
            # Internet-facing components (has external entities as predecessors)
            for pred in graph.predecessors(node):
                pred_data = graph.nodes.get(pred, {})
                if pred_data.get('type') == 'external_entity':
                    score += 3
                    
            # Components with many connections (attack surface)
            if graph.degree(node) > 3:
                score += 2
                
            if score > 0:
                entry_points.append((node, score))
                
        # Sort by score and return component names
        entry_points.sort(key=lambda x: x[1], reverse=True)
        return [ep[0] for ep in entry_points]
    
    def _identify_critical_assets(
        self, 
        graph: ComponentGraph, 
        dfd_components: Dict[str, Any]
    ) -> List[str]:
        """Identify high-value targets."""
        asset_scores = defaultdict(int)
        
        # All data stores are critical
        for asset in dfd_components.get('assets', []):
            asset_scores[asset] += 10
        
        # Components handling sensitive data
        for flow in dfd_components.get('data_flows', []):
            if isinstance(flow, dict):
                classification = flow.get('data_classification', '')
                score_map = {
                    'PII': 8, 'PHI': 9, 'PCI': 8, 'Confidential': 7, 
                    'Internal': 5, 'Public': 1
                }
                score = score_map.get(classification, 3)
                
                if 'destination' in flow and graph.has_node(flow['destination']):
                    asset_scores[flow['destination']] += score
                if 'source' in flow and graph.has_node(flow['source']):
                    asset_scores[flow['source']] += score // 2
                    
        # Sort by score and return top assets
        sorted_assets = sorted(asset_scores.items(), key=lambda x: x[1], reverse=True)
        return [asset[0] for asset in sorted_assets if asset[1] > 5]
    
    def _find_attack_paths(
        self, 
        graph: ComponentGraph, 
        entry_points: List[str], 
        targets: List[str]
    ) -> List[List[str]]:
        """Find potential attack paths."""
        all_paths = []
        path_set = set()  # To avoid duplicates
        
        for entry in entry_points[:5]:  # Limit for performance
            for target in targets[:5]:
                if entry != target:
                    # Find shortest path first
                    shortest = graph.shortest_path(entry, target)
                    if shortest and len(shortest) <= self.max_path_length:
                        path_tuple = tuple(shortest)
                        if path_tuple not in path_set:
                            all_paths.append(shortest)
                            path_set.add(path_tuple)
                    
                    # Find alternative paths
                    paths = graph.find_paths(entry, target, self.max_path_length)
                    for path in paths[:3]:  # Max 3 paths per pair
                        path_tuple = tuple(path)
                        if path_tuple not in path_set:
                            all_paths.append(path)
                            path_set.add(path_tuple)
                            
        self.logger.info(f"Found {len(all_paths)} unique attack paths")
        return all_paths
    
    async def _build_detailed_attack_paths(
        self,
        raw_paths: List[List[str]],
        component_threats: Dict[str, List[Dict[str, Any]]],
        all_threats: List[Dict[str, Any]]
    ) -> List[AttackPath]:
        """Build detailed attack paths with threat mapping."""
        attack_paths = []
        
        for path in raw_paths:
            detailed_path = await self._build_single_attack_path(
                path, component_threats, all_threats
            )
            if detailed_path:
                attack_paths.append(detailed_path)
                
        return attack_paths
    
    async def _build_single_attack_path(
        self,
        path: List[str],
        component_threats: Dict[str, List[Dict[str, Any]]],
        all_threats: List[Dict[str, Any]]
    ) -> Optional[AttackPath]:
        """Build a single detailed attack path."""
        path_steps = []
        used_threat_ids = set()
        
        for i, component in enumerate(path):
            # Get threats for this component
            threats = [t for t in component_threats.get(component, [])
                      if t.get('threat_id') not in used_threat_ids]
            
            if threats:
                # Select most relevant threat for this step
                relevant_threat = self._select_relevant_threat(
                    threats, step_position=i, total_steps=len(path)
                )
                
                if relevant_threat:
                    step = AttackStep(
                        step_number=i + 1,
                        component=component,
                        threat_id=relevant_threat.get('threat_id', f"T{i:03d}"),
                        threat_description=relevant_threat.get('threat_description', ''),
                        stride_category=relevant_threat.get('stride_category', 'Unknown'),
                        required_access=self._determine_required_access(i, len(path)),
                        detection_difficulty=self._assess_detection_difficulty(relevant_threat)
                    )
                    path_steps.append(step)
                    used_threat_ids.add(relevant_threat.get('threat_id'))
        
        if len(path_steps) < 2:
            return None  # Path too short
        
        # Generate path ID
        path_string = "->".join(path)
        path_hash = hashlib.md5(path_string.encode()).hexdigest()[:8]
        
        # Calculate combined metrics
        threats_in_path = [component_threats.get(comp, []) for comp in path]
        flat_threats = [t for sublist in threats_in_path for t in sublist]
        
        return AttackPath(
            path_id=f"AP_{path_hash}",
            scenario_name=f"{path[0]} to {path[-1]} Attack Chain",
            entry_point=path[0],
            target_asset=path[-1],
            path_steps=path_steps,
            total_steps=len(path_steps),
            combined_likelihood=self._calculate_combined_likelihood(flat_threats),
            combined_impact=self._calculate_combined_impact(flat_threats)
        )
    
    def _select_relevant_threat(
        self, 
        threats: List[Dict[str, Any]], 
        step_position: int, 
        total_steps: int
    ) -> Optional[Dict[str, Any]]:
        """Select most relevant threat for attack step."""
        if not threats:
            return None
        
        # Score threats based on position and characteristics
        scored_threats = []
        
        for threat in threats:
            score = 0
            
            # Position-based scoring
            stride_category = threat.get('stride_category', '')
            if step_position == 0:
                # First step - prefer authentication/access threats
                if stride_category in ['S']:  # Spoofing
                    score += 10
            elif step_position == total_steps - 1:
                # Last step - prefer data access/disclosure
                if stride_category in ['T', 'I', 'D']:  # Tampering, Info Disclosure, DoS
                    score += 10
            else:
                # Middle steps - prefer elevation/lateral movement
                if stride_category in ['E', 'T']:  # Elevation, Tampering
                    score += 5
            
            # Impact and likelihood scoring
            impact_scores = {'Critical': 8, 'High': 6, 'Medium': 4, 'Low': 2}
            score += impact_scores.get(threat.get('impact', 'Medium'), 3)
            
            likelihood_scores = {'High': 5, 'Medium': 3, 'Low': 1}
            score += likelihood_scores.get(threat.get('likelihood', 'Medium'), 2)
            
            scored_threats.append((threat, score))
        
        # Return highest scoring threat
        scored_threats.sort(key=lambda x: x[1], reverse=True)
        return scored_threats[0][0]
    
    def _determine_required_access(self, step: int, total_steps: int) -> str:
        """Determine required access level for attack step."""
        if step == 0:
            return "External/Unauthenticated"
        elif step < total_steps // 2:
            return "User-level"
        elif step < total_steps - 1:
            return "Privileged"
        else:
            return "Administrative"
    
    def _assess_detection_difficulty(self, threat: Dict[str, Any]) -> str:
        """Assess detection difficulty for a threat."""
        description = threat.get('threat_description', '').lower()
        
        # Keywords indicating easy detection
        if any(word in description for word in ['brute force', 'dos', 'flood', 'scan']):
            return "Easy"
        # Keywords indicating hard detection
        elif any(word in description for word in ['stealth', 'encrypted', 'legitimate', 'insider']):
            return "Hard"
        else:
            return "Medium"
    
    def _calculate_combined_impact(self, threats: List[Dict[str, Any]]) -> str:
        """Calculate combined impact of threat chain."""
        if not threats:
            return "Low"
        
        impact_values = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        max_impact = max((impact_values.get(t.get('impact', 'Low'), 1) for t in threats), default=1)
        
        impact_map = {4: "Critical", 3: "High", 2: "Medium", 1: "Low"}
        return impact_map[max_impact]
    
    def _calculate_combined_likelihood(self, threats: List[Dict[str, Any]]) -> str:
        """Calculate combined likelihood of threat chain."""
        if not threats:
            return "Low"
        
        likelihood_values = {"High": 3, "Medium": 2, "Low": 1}
        min_likelihood = min((likelihood_values.get(t.get('likelihood', 'Medium'), 2) for t in threats), default=2)
        
        likelihood_map = {3: "High", 2: "Medium", 1: "Low"}
        return likelihood_map[min_likelihood]
    
    async def _enrich_attack_paths(
        self, 
        paths: List[AttackPath], 
        dfd_components: Dict[str, Any]
    ) -> List[AttackPath]:
        """Enrich attack paths with LLM analysis."""
        if not self.llm_provider:
            return paths
        
        enriched_paths = []
        
        for i, path in enumerate(paths[:self.max_paths_to_analyze]):
            try:
                # Prepare path summary for LLM
                path_summary = [
                    {
                        "step": step.step_number,
                        "component": step.component,
                        "threat": step.threat_description,
                        "category": step.stride_category,
                        "access_required": step.required_access
                    }
                    for step in path.path_steps
                ]
                
                # Get LLM analysis
                analysis = await self._analyze_attack_scenario_with_llm(
                    path_summary, dfd_components
                )
                
                if analysis:
                    # Update path with LLM insights
                    path.scenario_name = analysis.get('scenario_name', path.scenario_name)
                    path.attacker_profile = analysis.get('attacker_profile', 'Cybercriminal')
                    path.path_feasibility = analysis.get('path_feasibility', 'Realistic')
                    path.time_to_compromise = analysis.get('time_to_compromise', 'Days')
                    path.combined_likelihood = analysis.get('combined_likelihood', path.combined_likelihood)
                    path.key_chokepoints = analysis.get('key_chokepoints', [])[:5]
                    path.detection_opportunities = analysis.get('detection_opportunities', [])[:5]
                    path.required_resources = analysis.get('required_resources', [])[:5]
                    path.path_complexity = analysis.get('path_complexity', 'Medium')
                
                enriched_paths.append(path)
                
            except Exception as e:
                self.logger.warning(f"Failed to enrich path {path.path_id}: {e}")
                enriched_paths.append(path)  # Keep original
        
        # Add remaining paths without enrichment
        enriched_paths.extend(paths[self.max_paths_to_analyze:])
        return enriched_paths
    
    async def _analyze_attack_scenario_with_llm(
        self, 
        path_steps: List[Dict], 
        dfd_data: Dict
    ) -> Optional[Dict[str, Any]]:
        """Analyze attack scenario using LLM."""
        prompt = f"""You are a cybersecurity expert evaluating an attack path.

Attack Path Steps:
{json.dumps(path_steps, indent=2)}

System Context:
- Project: {dfd_data.get('project_name', 'Unknown')}
- Industry: {dfd_data.get('industry_context', 'General')}
- Key Assets: {', '.join(dfd_data.get('assets', []))}

Analyze this attack path and provide a realistic assessment in JSON format:
{{
    "scenario_name": "descriptive name for this attack",
    "attacker_profile": "Script Kiddie|Cybercriminal|APT|Insider",
    "path_feasibility": "Theoretical|Realistic|Highly Likely",
    "time_to_compromise": "Hours|Days|Weeks|Months",
    "combined_likelihood": "Low|Medium|High",
    "key_chokepoints": ["specific defensive controls that would stop this"],
    "detection_opportunities": ["specific detection points in the attack chain"],
    "required_resources": ["tools, skills, or resources the attacker needs"],
    "path_complexity": "Low|Medium|High",
    "expert_assessment": "brief explanation of why this attack path matters"
}}

Consider real-world factors like required attacker sophistication, common defensive controls, and detection capabilities."""

        try:
            response = await self.llm_provider.generate_response(
                messages=[{"role": "user", "content": prompt}],
                response_format="json",
                temperature=0.3
            )
            
            if response and response.get('content'):
                return json.loads(response['content'])
                
        except Exception as e:
            self.logger.warning(f"LLM analysis failed: {e}")
            
        return None
    
    def _prioritize_attack_paths(self, paths: List[AttackPath]) -> List[AttackPath]:
        """Sort attack paths by criticality."""
        def path_score(p: AttackPath) -> int:
            feasibility_score = {"Highly Likely": 3, "Realistic": 2, "Theoretical": 1}
            impact_score = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
            return (feasibility_score.get(p.path_feasibility, 1) * 
                   impact_score.get(p.combined_impact, 1))
        
        return sorted(paths, key=path_score, reverse=True)
    
    def _generate_defense_priorities(self, paths: List[AttackPath]) -> List[DefensePriority]:
        """Generate prioritized defensive recommendations."""
        component_criticality = defaultdict(int)
        chokepoint_effectiveness = defaultdict(int)
        detection_gaps = defaultdict(int)
        
        # Analyze paths for patterns
        for path in paths:
            weight_map = {"Highly Likely": 3, "Realistic": 2, "Theoretical": 1}
            weight = weight_map.get(path.path_feasibility, 1)
            
            impact_weight = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
            weight *= impact_weight.get(path.combined_impact, 1)
            
            # Count component occurrences
            for step in path.path_steps:
                component_criticality[step.component] += weight
                
                if step.detection_difficulty == "Hard":
                    detection_gaps[step.component] += weight
            
            # Count chokepoint effectiveness
            for chokepoint in path.key_chokepoints:
                chokepoint_effectiveness[chokepoint] += weight
        
        priorities = []
        
        # Top chokepoints (most effective controls)
        top_chokepoints = sorted(chokepoint_effectiveness.items(), 
                               key=lambda x: x[1], reverse=True)[:5]
        for control, effectiveness in top_chokepoints:
            priorities.append(DefensePriority(
                type="preventive_control",
                recommendation=f"Implement {control}",
                impact=f"Would mitigate {effectiveness} weighted attack paths",
                priority="Critical" if effectiveness > 20 else "High",
                effort="Variable",
                category="Prevention",
                affected_paths=effectiveness
            ))
        
        # Critical components needing hardening
        critical_components = sorted(component_criticality.items(), 
                                   key=lambda x: x[1], reverse=True)[:5]
        for component, criticality in critical_components:
            priorities.append(DefensePriority(
                type="component_hardening",
                recommendation=f"Harden {component}",
                impact=f"Component appears in {criticality} weighted attack paths",
                priority="High" if criticality > 10 else "Medium",
                effort="Medium",
                category="Defense in Depth",
                affected_paths=criticality
            ))
        
        # Detection improvements
        detection_improvements = sorted(detection_gaps.items(), 
                                      key=lambda x: x[1], reverse=True)[:3]
        for component, gap_score in detection_improvements:
            priorities.append(DefensePriority(
                type="detection_enhancement",
                recommendation=f"Improve monitoring for {component}",
                impact=f"Would detect {gap_score} hard-to-detect attack steps",
                priority="High",
                effort="Low to Medium",
                category="Detection",
                affected_paths=gap_score
            ))
        
        return priorities
    
    def _calculate_threat_coverage(
        self, 
        paths: List[AttackPath], 
        all_threats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate threat coverage statistics."""
        covered_threats = set()
        total_threats = len(all_threats)
        
        for path in paths:
            for step in path.path_steps:
                covered_threats.add(step.threat_id)
        
        coverage_percentage = (len(covered_threats) / total_threats * 100) if total_threats > 0 else 0
        
        return {
            "total_threats": total_threats,
            "covered_threats": len(covered_threats),
            "coverage_percentage": round(coverage_percentage, 2),
            "uncovered_threats": total_threats - len(covered_threats)
        }
    
    def _identify_critical_scenarios(self, paths: List[AttackPath]) -> List[str]:
        """Identify the most critical attack scenarios."""
        critical_scenarios = []
        
        for path in paths:
            if (path.path_feasibility != "Theoretical" and 
                path.combined_impact in ["Critical", "High"]):
                critical_scenarios.append(path.scenario_name)
                if len(critical_scenarios) >= 5:
                    break
        
        return critical_scenarios
    
    def _serialize_attack_path(self, path: AttackPath) -> Dict[str, Any]:
        """Serialize attack path for JSON output."""
        return {
            "path_id": path.path_id,
            "scenario_name": path.scenario_name,
            "entry_point": path.entry_point,
            "target_asset": path.target_asset,
            "total_steps": path.total_steps,
            "combined_likelihood": path.combined_likelihood,
            "combined_impact": path.combined_impact,
            "path_feasibility": path.path_feasibility,
            "attacker_profile": path.attacker_profile,
            "time_to_compromise": path.time_to_compromise,
            "path_complexity": path.path_complexity,
            "key_chokepoints": path.key_chokepoints,
            "detection_opportunities": path.detection_opportunities,
            "required_resources": path.required_resources,
            "path_steps": [
                {
                    "step_number": step.step_number,
                    "component": step.component,
                    "threat_id": step.threat_id,
                    "threat_description": step.threat_description,
                    "stride_category": step.stride_category,
                    "required_access": step.required_access,
                    "detection_difficulty": step.detection_difficulty
                }
                for step in path.path_steps
            ]
        }
    
    def _serialize_defense_priority(self, dp: DefensePriority) -> Dict[str, Any]:
        """Serialize defense priority for JSON output."""
        return {
            "type": dp.type,
            "recommendation": dp.recommendation,
            "impact": dp.impact,
            "priority": dp.priority,
            "effort": dp.effort,
            "category": dp.category,
            "affected_paths": dp.affected_paths
        }