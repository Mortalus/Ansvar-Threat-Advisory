"""
Simple Workflow Service

A simplified version that bypasses complex database session management
to demonstrate the working modular workflow system.
"""

import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4

from ..core.agents.registry import agent_registry
from ..core.llm import get_llm_provider

logger = logging.getLogger(__name__)


class SimpleWorkflowService:
    """
    Simplified workflow service for demonstration purposes.
    Focuses on the core workflow logic without complex database operations.
    """
    
    def __init__(self):
        self._templates = {}  # In-memory storage for demo
        self._executions = {}
        
    async def create_template(self, name: str, description: str, steps: List[Dict]) -> Dict[str, Any]:
        """Create workflow template (in-memory for demo)"""
        template_id = str(uuid4())
        
        # Validate steps have valid agents
        for step in steps:
            agent_type = step.get('agent_type')
            if not agent_type:
                raise ValueError(f"Step missing agent_type: {step}")
            
            agent = agent_registry.get_agent(agent_type)
            if not agent:
                raise ValueError(f"Agent not found: {agent_type}")
        
        template = {
            'id': template_id,
            'name': name,
            'description': description,
            'steps': steps,
            'automation_settings': {
                'enabled': True,
                'confidence_threshold': 0.85
            },
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True
        }
        
        self._templates[template_id] = template
        logger.info(f"✅ Created workflow template: {name} ({template_id})")
        
        return template
    
    async def start_workflow(self, template_id: str, client_id: str = None, initial_data: Dict = None) -> Dict[str, Any]:
        """Start workflow execution"""
        if template_id not in self._templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self._templates[template_id]
        execution_id = str(uuid4())
        
        execution = {
            'id': execution_id,
            'template_id': template_id,
            'template_name': template['name'],
            'client_id': client_id,
            'status': 'pending',
            'current_step': 0,
            'total_steps': len(template['steps']),
            'progress_percent': 0,
            'started_at': datetime.utcnow().isoformat(),
            'data': initial_data or {},
            'steps': [],
            'threats': []
        }
        
        self._executions[execution_id] = execution
        logger.info(f"✅ Started workflow execution: {execution_id}")
        
        return execution
    
    async def execute_workflow_step(self, execution_id: str, step_index: int) -> Dict[str, Any]:
        """Execute a single workflow step"""
        if execution_id not in self._executions:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution = self._executions[execution_id]
        template = self._templates[execution['template_id']]
        
        if step_index >= len(template['steps']):
            raise ValueError(f"Step index {step_index} out of range")
        
        step_config = template['steps'][step_index]
        step_name = step_config.get('name', f'Step {step_index + 1}')
        agent_type = step_config.get('agent_type')
        
        logger.info(f"🔄 Executing step {step_index}: {step_name} with {agent_type}")
        
        # Get agent
        agent = agent_registry.get_agent(agent_type)
        if not agent:
            raise ValueError(f"Agent not found: {agent_type}")
        
        # Build execution context
        context = self._build_execution_context(execution, step_config)
        
        # Get LLM provider with step mapping
        llm_step_mapping = {
            "document_analysis": "dfd_extraction",
            "architectural_risk": "threat_generation",
            "business_financial": "threat_refinement",
            "compliance_governance": "threat_generation",
            "data_flow_analysis": "dfd_extraction"
        }
        llm_step = llm_step_mapping.get(agent_type, "threat_generation")
        
        start_time = datetime.utcnow()
        
        try:
            # Get LLM provider
            llm_provider = await get_llm_provider(step=llm_step)
            logger.info(f"✅ LLM provider: {type(llm_provider).__name__}")
            
            # Execute agent (simplified - using mock execution for demo)
            threats = await self._execute_agent_mock(agent, context, llm_provider)
            
        except Exception as e:
            logger.error(f"❌ Agent execution failed: {e}")
            # Use fallback mock execution
            threats = await self._execute_agent_fallback(agent_type, context)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Calculate confidence
        avg_confidence = 0.0
        if threats:
            confidences = [t.get('confidence_score', 0.8) for t in threats]
            avg_confidence = sum(confidences) / len(confidences)
        else:
            avg_confidence = 0.85  # Default confidence for demo
        
        # Determine automation
        confidence_threshold = step_config.get('confidence_threshold', 0.8)
        automated = avg_confidence >= confidence_threshold
        
        step_result = {
            'step_index': step_index,
            'step_name': step_name,
            'agent_name': agent_type,
            'status': 'completed',
            'automated': automated,
            'requires_review': not automated,
            'confidence_score': avg_confidence,
            'execution_time_ms': int(execution_time),
            'threat_count': len(threats),
            'threats': threats,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        # Update execution
        execution['steps'].append(step_result)
        execution['threats'].extend(threats)
        execution['current_step'] = step_index + 1
        execution['progress_percent'] = (step_index + 1) / execution['total_steps'] * 100
        execution['last_activity_at'] = datetime.utcnow().isoformat()
        
        if step_index + 1 >= execution['total_steps']:
            execution['status'] = 'completed'
            execution['completed_at'] = datetime.utcnow().isoformat()
        else:
            execution['status'] = 'running'
        
        logger.info(f"✅ Step {step_index} completed: {len(threats)} threats, confidence {avg_confidence:.2f}")
        
        return step_result
    
    async def execute_complete_workflow(self, execution_id: str) -> Dict[str, Any]:
        """Execute all workflow steps in sequence"""
        execution = self._executions[execution_id]
        template = self._templates[execution['template_id']]
        
        execution['status'] = 'running'
        logger.info(f"🚀 Starting complete workflow execution: {execution['template_name']}")
        
        try:
            # Execute each step
            for i in range(len(template['steps'])):
                await self.execute_workflow_step(execution_id, i)
            
            execution['status'] = 'completed'
            logger.info(f"✅ Workflow execution completed: {execution_id}")
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            execution['status'] = 'failed'
            execution['error'] = str(e)
        
        return execution
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status"""
        return self._executions.get(execution_id)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all templates"""
        return list(self._templates.values())
    
    def list_executions(self) -> List[Dict[str, Any]]:
        """List all executions"""
        return list(self._executions.values())
    
    def _build_execution_context(self, execution: Dict, step_config: Dict):
        """Build agent execution context"""
        from ..core.agents.base import AgentExecutionContext
        
        # Get document content
        document_content = execution['data'].get('document_content', 'Sample document content for testing')
        
        # Convert component strings to component dictionaries if needed
        raw_components = execution['data'].get('components', ['Web App', 'API', 'Database'])
        if raw_components and isinstance(raw_components[0], str):
            # Convert string components to dictionary format
            components = [
                {
                    "name": comp,
                    "type": "generic",
                    "trust_zone": "internal",
                    "id": f"comp_{i}"
                }
                for i, comp in enumerate(raw_components)
            ]
        else:
            components = raw_components
        
        existing_threats = execution.get('threats', [])
        
        return AgentExecutionContext(
            document_text=document_content,
            components=components,
            existing_threats=existing_threats,
            pipeline_id=execution['id'],
            user_config=step_config.get('parameters', {})
        )
    
    async def _execute_agent_mock(self, agent, context, llm_provider) -> List[Dict]:
        """Mock agent execution for demonstration"""
        # For demo purposes, return mock threats based on agent type
        agent_name = agent.get_metadata().name.lower()
        
        if 'document' in agent_name:
            return [
                {
                    "threat_name": "Authentication Bypass",
                    "description": "Potential authentication bypass in login system",
                    "stride_category": "Spoofing",
                    "affected_component": "Authentication Service",
                    "potential_impact": "High - Unauthorized access",
                    "likelihood": "Medium",
                    "mitigation": "Implement multi-factor authentication",
                    "confidence_score": 0.90
                }
            ]
        elif 'architectural' in agent_name:
            return [
                {
                    "threat_name": "Privilege Escalation",
                    "description": "System architecture allows privilege escalation",
                    "stride_category": "Elevation of Privilege",
                    "affected_component": "Service Architecture",
                    "potential_impact": "Critical - Full system compromise",
                    "likelihood": "Medium",
                    "mitigation": "Implement zero-trust architecture",
                    "confidence_score": 0.95
                }
            ]
        elif 'business' in agent_name:
            return [
                {
                    "threat_name": "Data Exposure Risk",
                    "description": "Financial data exposure through API vulnerabilities",
                    "stride_category": "Information Disclosure",
                    "affected_component": "Financial API",
                    "potential_impact": "High - Regulatory compliance breach",
                    "likelihood": "Low",
                    "mitigation": "Implement data classification and encryption",
                    "confidence_score": 0.80
                }
            ]
        else:
            return [
                {
                    "threat_name": "Generic Security Risk",
                    "description": "General security risk identified",
                    "stride_category": "Tampering",
                    "affected_component": "System Component",
                    "potential_impact": "Medium",
                    "likelihood": "Low",
                    "mitigation": "Implement security controls",
                    "confidence_score": 0.75
                }
            ]
    
    async def _execute_agent_fallback(self, agent_type: str, context) -> List[Dict]:
        """Fallback agent execution"""
        return [
            {
                "threat_name": f"Fallback Threat ({agent_type})",
                "description": f"Fallback threat generated by {agent_type} agent",
                "stride_category": "Tampering",
                "affected_component": "System Component",
                "potential_impact": "Medium",
                "likelihood": "Low",
                "mitigation": "Implement appropriate security controls",
                "confidence_score": 0.70
            }
        ]


# Global instance for easy access
simple_workflow_service = SimpleWorkflowService()