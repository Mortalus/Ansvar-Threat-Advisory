"""
Modular Agent System for Threat Analysis

This module provides a plugin-based architecture for threat analysis agents,
allowing dynamic addition, removal, and configuration of agents without
requiring code changes or service restarts.
"""

from .base import BaseAgent, AgentMetadata, ThreatOutput, AgentCategory
from .registry import AgentRegistry, agent_registry

__all__ = [
    'BaseAgent',
    'AgentMetadata', 
    'ThreatOutput',
    'AgentCategory',
    'AgentRegistry',
    'agent_registry'
]