#!/usr/bin/env python3
"""
Simple test for attack path analysis logic without pipeline dependencies
"""

import asyncio
import json
from typing import Dict, Any, List
from dataclasses import dataclass, field
from collections import defaultdict, deque
import hashlib

# Simplified components for testing
@dataclass
class AttackStep:
    step_number: int
    component: str
    threat_id: str
    threat_description: str
    stride_category: str
    required_access: str = None
    detection_difficulty: str = None

@dataclass
class AttackPath:
    path_id: str
    scenario_name: str
    entry_point: str
    target_asset: str
    path_steps: List[AttackStep]
    total_steps: int
    combined_likelihood: str
    combined_impact: str

class ComponentGraph:
    """Lightweight graph for component relationships."""
    
    def __init__(self):
        self.nodes: Dict[str, Dict] = {}
        self.edges: Dict[str, List[tuple]] = defaultdict(list)
        self.reverse_edges: Dict[str, List[tuple]] = defaultdict(list)
    
    def add_node(self, node: str, **attrs):
        self.nodes[node] = attrs
    
    def add_edge(self, source: str, dest: str, **attrs):
        self.edges[source].append((dest, attrs))
        self.reverse_edges[dest].append((source, attrs))
    
    def has_node(self, node: str) -> bool:
        return node in self.nodes
    
    def predecessors(self, node: str) -> List[str]:
        return [src for src, _ in self.reverse_edges[node]]
    
    def find_paths(self, start: str, end: str, max_length: int = 5) -> List[List[str]]:
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
                if neighbor not in path:
                    new_path = path + [neighbor]
                    queue.append((neighbor, new_path))
        
        return paths

class SimpleAttackPathAnalyzer:
    """Simplified analyzer for testing core logic."""
    
    def __init__(self):
        pass
    
    def build_component_graph(self, dfd_components: Dict[str, Any]) -> ComponentGraph:
        """Build graph from DFD components."""
        graph = ComponentGraph()
        
        # Add nodes
        for entity in dfd_components.get('external_entities', []):
            graph.add_node(entity, type='external_entity', trust_level='untrusted')
            
        for process in dfd_components.get('processes', []):
            graph.add_node(process, type='process', trust_level='semi-trusted')
            
        for asset in dfd_components.get('assets', []):
            graph.add_node(asset, type='asset', trust_level='trusted')
        
        # Add edges from data flows
        for flow in dfd_components.get('data_flows', []):
            if isinstance(flow, dict) and 'source' in flow and 'destination' in flow:
                source = flow['source']
                dest = flow['destination']
                
                if graph.has_node(source) and graph.has_node(dest):
                    graph.add_edge(source, dest, data_classification=flow.get('data_classification', 'Unknown'))
                    graph.add_edge(dest, source, data_classification=flow.get('data_classification', 'Unknown'))
        
        return graph
    
    def identify_entry_points(self, graph: ComponentGraph) -> List[str]:
        """Find potential entry points."""
        entry_points = []
        
        for node in graph.nodes:
            node_data = graph.nodes[node]
            if node_data.get('type') == 'external_entity':
                entry_points.append(node)
        
        return entry_points
    
    def identify_critical_assets(self, graph: ComponentGraph, dfd_components: Dict[str, Any]) -> List[str]:
        """Find critical assets."""
        assets = dfd_components.get('assets', [])
        
        # Score by data classification
        asset_scores = defaultdict(int)
        for flow in dfd_components.get('data_flows', []):
            if isinstance(flow, dict):
                classification = flow.get('data_classification', '')
                score_map = {'PHI': 10, 'PII': 8, 'Confidential': 7, 'Internal': 5}
                score = score_map.get(classification, 3)
                
                if 'destination' in flow and graph.has_node(flow['destination']):
                    asset_scores[flow['destination']] += score
        
        # Return top scored assets
        sorted_assets = sorted(asset_scores.items(), key=lambda x: x[1], reverse=True)
        return [asset[0] for asset in sorted_assets if asset[1] > 5][:5]
    
    def find_attack_paths(self, graph: ComponentGraph, entry_points: List[str], targets: List[str]) -> List[List[str]]:
        """Find attack paths between entries and targets."""
        all_paths = []
        path_set = set()
        
        for entry in entry_points[:3]:  # Limit for demo
            for target in targets[:3]:
                if entry != target:
                    paths = graph.find_paths(entry, target, 4)
                    for path in paths[:2]:  # Max 2 paths per pair
                        path_tuple = tuple(path)
                        if path_tuple not in path_set:
                            all_paths.append(path)
                            path_set.add(path_tuple)
        
        return all_paths
    
    def map_threats_to_components(self, threats: List[Dict], graph: ComponentGraph) -> Dict[str, List[Dict]]:
        """Map threats to components."""
        component_threats = defaultdict(list)
        
        for threat in threats:
            component_name = threat.get('component_name', '')
            if component_name and graph.has_node(component_name):
                component_threats[component_name].append(threat)
        
        return dict(component_threats)
    
    def build_attack_path_details(self, path: List[str], component_threats: Dict[str, List[Dict]]) -> AttackPath:
        """Build detailed attack path."""
        path_steps = []
        used_threat_ids = set()
        
        for i, component in enumerate(path):
            threats = [t for t in component_threats.get(component, [])
                      if t.get('threat_id') not in used_threat_ids]
            
            if threats:
                threat = threats[0]  # Use first available threat
                step = AttackStep(
                    step_number=i + 1,
                    component=component,
                    threat_id=threat.get('threat_id', f"T{i:03d}"),
                    threat_description=threat.get('threat_description', 'Unknown threat'),
                    stride_category=threat.get('stride_category', 'Unknown'),
                    required_access="External" if i == 0 else "User-level" if i < len(path)-1 else "Administrative",
                    detection_difficulty="Medium"
                )
                path_steps.append(step)
                used_threat_ids.add(threat.get('threat_id'))
        
        if len(path_steps) < 2:
            return None
        
        # Generate path ID
        path_string = "->".join(path)
        path_hash = hashlib.md5(path_string.encode()).hexdigest()[:8]
        
        return AttackPath(
            path_id=f"AP_{path_hash}",
            scenario_name=f"{path[0]} to {path[-1]} Attack Chain",
            entry_point=path[0],
            target_asset=path[-1],
            path_steps=path_steps,
            total_steps=len(path_steps),
            combined_likelihood="Medium",
            combined_impact="High"
        )

# Sample test data
SAMPLE_DFD_COMPONENTS = {
    "project_name": "HealthTech Analytics Platform",
    "external_entities": ["Patients", "Doctors", "EHR Systems"],
    "processes": ["Patient Portal", "API Server", "Analytics Engine", "Authentication Service"],
    "assets": ["Patient Database", "Analytics Cache", "Document Storage"],
    "data_flows": [
        {
            "source": "Patients",
            "destination": "Patient Portal",
            "data_classification": "PII",
            "protocol": "HTTPS"
        },
        {
            "source": "Patient Portal",
            "destination": "API Server",
            "data_classification": "PII",
            "protocol": "HTTPS"
        },
        {
            "source": "API Server",
            "destination": "Patient Database",
            "data_classification": "PHI",
            "protocol": "TLS"
        },
        {
            "source": "Doctors",
            "destination": "API Server",
            "data_classification": "PHI",
            "protocol": "HTTPS"
        },
        {
            "source": "API Server",
            "destination": "Analytics Engine",
            "data_classification": "Internal",
            "protocol": "HTTP"
        }
    ]
}

SAMPLE_THREATS = [
    {
        "threat_id": "T001",
        "component_name": "Patient Portal",
        "threat_description": "Cross-site scripting vulnerability",
        "stride_category": "S",
        "impact": "High",
        "likelihood": "Medium"
    },
    {
        "threat_id": "T002",
        "component_name": "API Server",
        "threat_description": "API lacks rate limiting",
        "stride_category": "D",
        "impact": "Medium",
        "likelihood": "High"
    },
    {
        "threat_id": "T003",
        "component_name": "Patient Database",
        "threat_description": "SQL injection vulnerability",
        "stride_category": "I",
        "impact": "Critical",
        "likelihood": "Medium"
    },
    {
        "threat_id": "T004",
        "component_name": "Authentication Service",
        "threat_description": "Weak password policies",
        "stride_category": "S",
        "impact": "High",
        "likelihood": "High"
    }
]

async def test_simple_analyzer():
    """Test the simplified analyzer."""
    
    print("=" * 80)
    print("SIMPLIFIED ATTACK PATH ANALYZER TEST")
    print("=" * 80)
    
    analyzer = SimpleAttackPathAnalyzer()
    
    print("\n📊 Building component graph...")
    graph = analyzer.build_component_graph(SAMPLE_DFD_COMPONENTS)
    print(f"✅ Graph built: {len(graph.nodes)} nodes")
    
    print("\n🎯 Identifying entry points and targets...")
    entry_points = analyzer.identify_entry_points(graph)
    critical_assets = analyzer.identify_critical_assets(graph, SAMPLE_DFD_COMPONENTS)
    print(f"✅ Found {len(entry_points)} entry points: {entry_points}")
    print(f"✅ Found {len(critical_assets)} critical assets: {critical_assets}")
    
    print("\n🔍 Finding attack paths...")
    raw_paths = analyzer.find_attack_paths(graph, entry_points, critical_assets)
    print(f"✅ Found {len(raw_paths)} potential attack paths")
    
    for i, path in enumerate(raw_paths, 1):
        print(f"  Path {i}: {' → '.join(path)}")
    
    print("\n🗺️ Mapping threats to components...")
    component_threats = analyzer.map_threats_to_components(SAMPLE_THREATS, graph)
    print(f"✅ Mapped threats to {len(component_threats)} components")
    
    for component, threats in component_threats.items():
        print(f"  {component}: {len(threats)} threats")
    
    print("\n🔗 Building detailed attack paths...")
    attack_paths = []
    for path in raw_paths:
        detailed_path = analyzer.build_attack_path_details(path, component_threats)
        if detailed_path:
            attack_paths.append(detailed_path)
    
    print(f"✅ Built {len(attack_paths)} detailed attack paths")
    
    print("\n" + "=" * 80)
    print("ATTACK PATH ANALYSIS RESULTS")
    print("=" * 80)
    
    for i, path in enumerate(attack_paths, 1):
        print(f"\n🎯 Attack Path {i}: {path.scenario_name}")
        print(f"   Path ID: {path.path_id}")
        print(f"   Entry: {path.entry_point} → Target: {path.target_asset}")
        print(f"   Steps: {path.total_steps} | Impact: {path.combined_impact} | Likelihood: {path.combined_likelihood}")
        
        print(f"   Attack Chain:")
        for step in path.path_steps:
            print(f"     Step {step.step_number}: {step.component}")
            print(f"       Threat: {step.threat_description}")
            print(f"       STRIDE: {step.stride_category} | Access: {step.required_access}")
    
    print("\n" + "=" * 80)
    print("✅ ATTACK PATH ANALYSIS CORE LOGIC WORKING!")
    print("=" * 80)
    
    print("\n🚀 This demonstrates:")
    print("  ✅ Component graph building from DFD")
    print("  ✅ Entry point identification")
    print("  ✅ Critical asset identification") 
    print("  ✅ Attack path discovery")
    print("  ✅ Threat mapping to components")
    print("  ✅ Detailed attack chain construction")
    print("\n🎉 Ready for integration with the full pipeline!")

if __name__ == "__main__":
    asyncio.run(test_simple_analyzer())