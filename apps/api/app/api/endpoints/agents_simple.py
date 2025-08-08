"""Simple Agents API - Fast endpoint without complex registry dependencies"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/api/agents", tags=["agents-simple"])

# Mock agent data that matches the frontend expectations
MOCK_AGENTS = [
    {
        "name": "architectural_risk",
        "version": "3.0.0", 
        "description": "Detects systemic architectural flaws and design vulnerabilities that traditional scanners miss",
        "category": "architecture",
        "enabled": True,
        "priority": 1,
        "estimated_tokens": 3500,
        "requires_document": True,
        "requires_components": True,
        "metrics": {
            "total_executions": 0,
            "success_rate": 0.0,
            "avg_threats": 0.0,
            "avg_execution_time": 0.0,
            "total_tokens_used": 0,
            "last_executed": None
        }
    },
    {
        "name": "business_financial",
        "version": "3.0.0",
        "description": "Connects technical threats to business impact and quantifies financial risks", 
        "category": "business",
        "enabled": True,
        "priority": 2,
        "estimated_tokens": 3800,
        "requires_document": True,
        "requires_components": True,
        "metrics": {
            "total_executions": 0,
            "success_rate": 0.0,
            "avg_threats": 0.0,
            "avg_execution_time": 0.0,
            "total_tokens_used": 0,
            "last_executed": None
        }
    },
    {
        "name": "compliance_governance",
        "version": "3.0.0",
        "description": "Views system through auditor's lens and identifies regulatory compliance gaps",
        "category": "compliance", 
        "enabled": True,
        "priority": 3,
        "estimated_tokens": 4000,
        "requires_document": True,
        "requires_components": True,
        "metrics": {
            "total_executions": 0,
            "success_rate": 0.0,
            "avg_threats": 0.0,
            "avg_execution_time": 0.0,
            "total_tokens_used": 0,
            "last_executed": None
        }
    }
]


@router.get("/list", response_model=Dict[str, Any])
async def list_agents_simple():
    """Fast agents endpoint with mock data"""
    return {
        "agents": MOCK_AGENTS,
        "total": len(MOCK_AGENTS),
        "categories": ["architecture", "business", "compliance"],
        "enabled_count": 3
    }


@router.post("/{agent_name}/test")
async def test_agent_simple(agent_name: str):
    """Simple agent test endpoint"""
    if agent_name not in [a["name"] for a in MOCK_AGENTS]:
        return {"status": "error", "message": f"Agent {agent_name} not found"}
    
    return {
        "status": "success",
        "agent": agent_name,
        "execution_time": 0.0,
        "threats_found": 0,
        "average_confidence": 0.0,
        "estimated_tokens": next(a["estimated_tokens"] for a in MOCK_AGENTS if a["name"] == agent_name),
        "threats_sample": [],
        "context_info": {
            "document_length": 0,
            "components_count": 17
        }
    }