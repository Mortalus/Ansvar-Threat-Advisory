#!/usr/bin/env python3
"""
Modular Workflow System Demo

Demonstrates the complete end-to-end threat modeling workflow
without requiring database connectivity.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
from uuid import uuid4

# Add the app directory to Python path
sys.path.insert(0, '/Users/jeffreyvonrotz/SynologyDrive/Projects/ThreatModelingPipeline/apps/api')

class MockLLMProvider:
    """Mock LLM provider for demonstration"""
    
    async def generate_completion(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3):
        """Generate mock completion for testing"""
        print("🧪 Using mock LLM provider for demonstration")
        
        # Return mock threat analysis based on prompt content
        if "document_analysis" in prompt.lower():
            return {
                'content': '''
                [
                    {
                        "Threat Name": "Authentication Bypass",
                        "Description": "Potential authentication bypass vulnerabilities in login system",
                        "STRIDE Category": "Spoofing",
                        "Affected Component": "Authentication Service",
                        "Potential Impact": "High - Unauthorized access to system",
                        "Likelihood": "Medium - Requires specific conditions",
                        "Suggested Mitigation": "Implement multi-factor authentication and session validation"
                    },
                    {
                        "Threat Name": "Data Exposure",
                        "Description": "Sensitive data may be exposed through API responses",
                        "STRIDE Category": "Information Disclosure", 
                        "Affected Component": "API Gateway",
                        "Potential Impact": "High - Customer data breach",
                        "Likelihood": "Low - Requires API exploitation", 
                        "Suggested Mitigation": "Implement response filtering and data classification"
                    }
                ]
                '''
            }
        elif "architectural" in prompt.lower():
            return {
                'content': '''
                [
                    {
                        "Threat Name": "Privilege Escalation",
                        "Description": "System architecture allows privilege escalation between services",
                        "STRIDE Category": "Elevation of Privilege",
                        "Affected Component": "Service Architecture",
                        "Potential Impact": "Critical - Full system compromise",
                        "Likelihood": "Medium - Requires insider knowledge",
                        "Suggested Mitigation": "Implement zero-trust architecture and service mesh"
                    }
                ]
                '''
            }
        else:
            return {
                'content': '''
                [
                    {
                        "Threat Name": "Generic Security Risk",
                        "Description": "General security risk identified in system",
                        "STRIDE Category": "Tampering",
                        "Affected Component": "System Component",
                        "Potential Impact": "Medium - Potential system impact",
                        "Likelihood": "Low - Requires specific conditions",
                        "Suggested Mitigation": "Implement security controls and monitoring"
                    }
                ]
                '''
            }

class WorkflowDemo:
    """Demonstration of the modular workflow system"""
    
    def __init__(self):
        self.llm_provider = MockLLMProvider()
        self.agents = self._init_mock_agents()
        
    def _init_mock_agents(self):
        """Initialize mock agents for demonstration"""
        return {
            'document_analysis': {
                'name': 'Document Analysis',
                'description': 'Analyzes documents for security threats',
                'category': 'analysis',
                'confidence_baseline': 0.85
            },
            'architectural_risk': {
                'name': 'Architectural Risk Analysis',
                'description': 'Identifies architectural security risks',
                'category': 'architecture', 
                'confidence_baseline': 0.90
            },
            'business_financial': {
                'name': 'Business Impact Analysis',
                'description': 'Quantifies business and financial impact',
                'category': 'business',
                'confidence_baseline': 0.75
            }
        }
    
    async def create_workflow_template(self, name: str, description: str, steps: List[Dict]) -> Dict[str, Any]:
        """Create a workflow template"""
        template_id = str(uuid4())
        
        template = {
            'id': template_id,
            'name': name,
            'description': description,
            'steps': steps,
            'automation_settings': {
                'enabled': True,
                'confidence_threshold': 0.85,
                'max_auto_approvals_per_day': 50
            },
            'client_access_rules': {
                'authentication_method': 'token',
                'token_expiry_days': 30
            },
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True
        }
        
        print(f"✅ Created workflow template: {name}")
        print(f"   Template ID: {template_id}")
        print(f"   Steps: {len(steps)}")
        
        return template
    
    async def execute_workflow_step(self, step_config: Dict, context: Dict) -> Dict[str, Any]:
        """Execute a single workflow step"""
        agent_type = step_config['agent_type']
        step_name = step_config['name']
        
        print(f"🔄 Executing step: {step_name} ({agent_type})")
        
        if agent_type not in self.agents:
            raise ValueError(f"Agent {agent_type} not found")
        
        agent_info = self.agents[agent_type]
        
        # Simulate agent execution with LLM
        start_time = datetime.utcnow()
        
        prompt = f"""
        Analyze the following system for security threats using the {agent_info['name']} perspective:
        
        Document: {context.get('document_content', 'Sample application architecture document')}
        Components: {context.get('components', ['Web Frontend', 'API Gateway', 'Database'])}
        Existing Threats: {len(context.get('existing_threats', []))} previously identified
        
        Focus on {agent_info['description'].lower()}.
        """
        
        # Get LLM response
        llm_response = await self.llm_provider.generate_completion(prompt)
        
        # Parse threats from response
        try:
            threats_data = json.loads(llm_response['content'].strip())
            if not isinstance(threats_data, list):
                threats_data = [threats_data]
        except:
            threats_data = []
        
        # Calculate execution metrics
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        confidence_score = agent_info['confidence_baseline'] + (len(threats_data) * 0.05)
        confidence_score = min(confidence_score, 1.0)
        
        # Determine automation
        automated = confidence_score >= step_config.get('confidence_threshold', 0.8)
        requires_review = not automated
        
        result = {
            'step_name': step_name,
            'agent_name': agent_type,
            'status': 'completed',
            'automated': automated,
            'requires_review': requires_review,
            'confidence_score': confidence_score,
            'execution_time_ms': int(execution_time),
            'threat_count': len(threats_data),
            'threats': threats_data
        }
        
        print(f"   ✅ Completed: {len(threats_data)} threats, confidence {confidence_score:.2f}")
        if automated:
            print(f"   🤖 AUTOMATED: High confidence - no review required")
        else:
            print(f"   👤 REVIEW REQUIRED: Low confidence - manual review needed")
        
        return result
    
    async def execute_complete_workflow(self, template: Dict, initial_data: Dict) -> Dict[str, Any]:
        """Execute a complete workflow from template"""
        execution_id = str(uuid4())
        
        print(f"\\n🚀 Starting workflow execution: {template['name']}")
        print(f"   Execution ID: {execution_id}")
        
        context = {
            'document_content': initial_data.get('document_content', 'Sample threat modeling document'),
            'components': initial_data.get('components', ['Web App', 'API', 'Database']),
            'existing_threats': []
        }
        
        results = {
            'execution_id': execution_id,
            'template_name': template['name'],
            'status': 'running',
            'steps': [],
            'all_threats': [],
            'metadata': {
                'total_steps': len(template['steps']),
                'completed_steps': 0,
                'automated_steps': 0,
                'manual_reviews': 0,
                'total_threats': 0
            }
        }
        
        # Execute each step
        for i, step_config in enumerate(template['steps']):
            try:
                step_result = await self.execute_workflow_step(step_config, context)
                
                results['steps'].append(step_result)
                results['metadata']['completed_steps'] += 1
                
                if step_result['automated']:
                    results['metadata']['automated_steps'] += 1
                if step_result['requires_review']:
                    results['metadata']['manual_reviews'] += 1
                
                # Add threats to global collection
                step_threats = step_result.get('threats', [])
                results['all_threats'].extend(step_threats)
                results['metadata']['total_threats'] += len(step_threats)
                
                # Update context for next step
                context['existing_threats'].extend(step_threats)
                
            except Exception as e:
                print(f"   ❌ Step {i+1} failed: {e}")
                results['steps'].append({
                    'step_name': step_config['name'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        results['status'] = 'completed'
        
        return results

async def main():
    """Main demonstration function"""
    print("=" * 80)
    print("🛡️  MODULAR THREAT MODELING WORKFLOW DEMONSTRATION")
    print("=" * 80)
    
    demo = WorkflowDemo()
    
    # 1. Create workflow template
    print("\\n📋 Step 1: Creating Workflow Template")
    print("-" * 50)
    
    template = await demo.create_workflow_template(
        name="Complete Threat Analysis",
        description="Comprehensive threat modeling workflow with multiple analysis perspectives",
        steps=[
            {
                'name': 'Document Analysis',
                'description': 'Initial document and requirement analysis',
                'agent_type': 'document_analysis',
                'confidence_threshold': 0.8
            },
            {
                'name': 'Architectural Risk Assessment',
                'description': 'Deep architectural security analysis',
                'agent_type': 'architectural_risk',
                'confidence_threshold': 0.85
            },
            {
                'name': 'Business Impact Analysis',
                'description': 'Business and financial impact assessment',
                'agent_type': 'business_financial',
                'confidence_threshold': 0.75
            }
        ]
    )
    
    # 2. Execute workflow
    print("\\n⚙️  Step 2: Executing Workflow")
    print("-" * 50)
    
    initial_data = {
        'document_content': """
        Web Application Architecture:
        - React frontend with authentication
        - Node.js API backend with JWT tokens
        - PostgreSQL database with user data
        - Redis for session management
        - AWS deployment with S3 storage
        """,
        'components': [
            'React Frontend',
            'Node.js API',
            'PostgreSQL Database', 
            'Redis Cache',
            'AWS Infrastructure'
        ]
    }
    
    workflow_results = await demo.execute_complete_workflow(template, initial_data)
    
    # 3. Display results
    print("\\n📊 Step 3: Workflow Results")
    print("-" * 50)
    
    metadata = workflow_results['metadata']
    
    print(f"Execution Status: {workflow_results['status'].upper()}")
    print(f"Template: {workflow_results['template_name']}")
    print(f"Execution ID: {workflow_results['execution_id']}")
    print()
    print("📈 Execution Statistics:")
    print(f"  • Total Steps: {metadata['total_steps']}")
    print(f"  • Completed: {metadata['completed_steps']}")
    print(f"  • Automated: {metadata['automated_steps']}")
    print(f"  • Requiring Review: {metadata['manual_reviews']}")
    print(f"  • Total Threats Found: {metadata['total_threats']}")
    
    print("\\n🔍 Step Details:")
    for i, step in enumerate(workflow_results['steps'], 1):
        if step['status'] == 'completed':
            automation_status = "🤖 AUTOMATED" if step['automated'] else "👤 REVIEW REQUIRED"
            print(f"  {i}. {step['step_name']}")
            print(f"     Agent: {step['agent_name']}")
            print(f"     Status: {automation_status}")
            print(f"     Confidence: {step['confidence_score']:.2f}")
            print(f"     Threats Found: {step['threat_count']}")
            print(f"     Execution Time: {step['execution_time_ms']}ms")
        else:
            print(f"  {i}. {step['step_name']} - FAILED: {step.get('error', 'Unknown error')}")
        print()
    
    print("🚨 All Threats Identified:")
    for i, threat in enumerate(workflow_results['all_threats'], 1):
        print(f"  {i}. {threat.get('Threat Name', 'Unknown Threat')}")
        print(f"     Category: {threat.get('STRIDE Category', 'Unknown')}")
        print(f"     Component: {threat.get('Affected Component', 'Unknown')}")
        print(f"     Impact: {threat.get('Potential Impact', 'Unknown')}")
        print(f"     Mitigation: {threat.get('Suggested Mitigation', 'None provided')}")
        print()
    
    print("=" * 80)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("🎯 Key Features Demonstrated:")
    print("  • Modular agent-based workflow execution")
    print("  • Confidence-based automation decisions") 
    print("  • Multi-step threat analysis pipeline")
    print("  • Defensive error handling and resilience")
    print("  • Real-time progress tracking and metrics")
    print("  • Structured threat output and reporting")
    print()
    print("🔧 Production Features (Not Shown):")
    print("  • Database persistence and state management")
    print("  • User authentication and authorization")
    print("  • Client access control and token management")
    print("  • Manual review workflow and approvals")
    print("  • Integration with existing LLM providers")
    print("  • WebSocket real-time updates")
    print("  • Export functionality (PDF, JSON, etc.)")

if __name__ == "__main__":
    asyncio.run(main())