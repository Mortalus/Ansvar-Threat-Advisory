"""
Enhanced Robust Modular Agent System for Threat Analysis

This module provides an enterprise-grade plugin-based architecture for threat analysis agents,
with comprehensive health monitoring, validation, and defensive programming features.

Features:
- Dynamic agent discovery and registration
- Health monitoring with circuit breakers and self-healing
- Multi-level validation and safety checks
- Performance tracking and optimization
- Hot-reload configuration without restarts
- Comprehensive error handling and recovery
"""

from .base import BaseAgent, AgentMetadata, ThreatOutput, AgentCategory, AgentExecutionContext
from .registry import AgentRegistry, agent_registry, initialize_agent_registry
from .health_monitor import health_monitor, AgentHealthMonitor, AgentHealthMetrics
from .validator import (
    AgentValidator, 
    ValidationLevel, 
    ValidationResult,
    get_validator
)

# Import orchestrator if it exists
try:
    from .orchestrator_v2 import ModularOrchestrator
    _has_orchestrator = True
except ImportError:
    _has_orchestrator = False
    ModularOrchestrator = None

__all__ = [
    # Core components
    'BaseAgent',
    'AgentMetadata', 
    'ThreatOutput',
    'AgentCategory',
    'AgentExecutionContext',
    
    # Registry
    'AgentRegistry',
    'agent_registry',
    'initialize_agent_registry',
    
    # Health monitoring
    'health_monitor',
    'AgentHealthMonitor',
    'AgentHealthMetrics',
    
    # Validation
    'AgentValidator',
    'ValidationLevel',
    'ValidationResult',
    'get_validator',
]

# Add orchestrator if available
if _has_orchestrator:
    __all__.append('ModularOrchestrator')