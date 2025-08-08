"""
Agent Health Monitoring API Endpoints

Provides real-time health status, metrics, and management for agents
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import logging

from app.core.agents import health_monitor, get_validator, ValidationLevel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents/health", tags=["agent-health"])


@router.get("/status")
async def get_health_status():
    """
    Get overall health status of the agent system
    
    Returns comprehensive health report including:
    - Overall system health
    - Individual agent health status
    - Reliability scores and metrics
    """
    try:
        report = health_monitor.get_health_report()
        return report
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {e}")


@router.get("/metrics/{agent_name}")
async def get_agent_metrics(agent_name: str):
    """
    Get detailed health metrics for a specific agent
    
    Returns:
    - Performance metrics (success rate, response times)
    - Circuit breaker status
    - Error history
    - Resource usage
    """
    try:
        metrics = health_monitor.get_agent_metrics(agent_name)
        
        if metrics is None:
            raise HTTPException(status_code=404, detail=f"No metrics found for agent {agent_name}")
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent metrics: {e}")


@router.post("/monitor/start")
async def start_health_monitoring():
    """
    Start background health monitoring
    
    Begins continuous health checks and metric collection
    """
    try:
        await health_monitor.start_monitoring()
        return {
            "status": "success",
            "message": "Health monitoring started",
            "monitoring_interval": health_monitor.health_check_interval
        }
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {e}")


@router.post("/monitor/stop")
async def stop_health_monitoring():
    """
    Stop background health monitoring
    """
    try:
        await health_monitor.stop_monitoring()
        return {
            "status": "success",
            "message": "Health monitoring stopped"
        }
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {e}")


@router.post("/circuit-breaker/{agent_name}/reset")
async def reset_circuit_breaker(agent_name: str):
    """
    Reset circuit breaker for a specific agent
    
    Closes an open circuit breaker and resets failure counters
    """
    try:
        metrics = health_monitor.get_or_create_metrics(agent_name)
        
        # Reset circuit breaker
        metrics.circuit_breaker_state = "closed"
        metrics.consecutive_failures = 0
        metrics.circuit_breaker_opens_at = None
        
        logger.info(f"Circuit breaker reset for {agent_name}")
        
        return {
            "status": "success",
            "message": f"Circuit breaker reset for {agent_name}",
            "current_state": metrics.circuit_breaker_state
        }
        
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset circuit breaker: {e}")


@router.post("/recover/{agent_name}")
async def trigger_recovery(agent_name: str):
    """
    Manually trigger recovery for a failing agent
    
    Attempts to recover an agent using registered recovery strategies
    """
    try:
        await health_monitor.attempt_recovery(agent_name)
        
        # Check if recovery was successful
        from app.core.agents import agent_registry
        agent = agent_registry.get_agent(agent_name)
        
        if agent:
            is_healthy = await health_monitor.check_agent_health(agent)
            
            return {
                "status": "success" if is_healthy else "partial",
                "message": f"Recovery {'successful' if is_healthy else 'attempted'} for {agent_name}",
                "is_healthy": is_healthy
            }
        else:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to recover {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger recovery: {e}")


@router.get("/thresholds")
async def get_health_thresholds():
    """
    Get current health monitoring thresholds and configuration
    """
    return {
        "failure_threshold": health_monitor.failure_threshold,
        "recovery_timeout": health_monitor.recovery_timeout,
        "memory_threshold_mb": health_monitor.memory_threshold_mb,
        "response_time_threshold_s": health_monitor.response_time_threshold_s,
        "health_check_interval": health_monitor.health_check_interval,
        "monitoring_enabled": health_monitor.monitoring_enabled
    }


@router.put("/thresholds")
async def update_health_thresholds(
    failure_threshold: Optional[int] = Query(None, ge=1, le=10),
    recovery_timeout: Optional[int] = Query(None, ge=60, le=3600),
    memory_threshold_mb: Optional[int] = Query(None, ge=100, le=5000),
    response_time_threshold_s: Optional[int] = Query(None, ge=1, le=300),
    health_check_interval: Optional[int] = Query(None, ge=10, le=600)
):
    """
    Update health monitoring thresholds
    
    Allows dynamic adjustment of monitoring parameters
    """
    try:
        updated = {}
        
        if failure_threshold is not None:
            health_monitor.failure_threshold = failure_threshold
            updated["failure_threshold"] = failure_threshold
        
        if recovery_timeout is not None:
            health_monitor.recovery_timeout = recovery_timeout
            updated["recovery_timeout"] = recovery_timeout
        
        if memory_threshold_mb is not None:
            health_monitor.memory_threshold_mb = memory_threshold_mb
            updated["memory_threshold_mb"] = memory_threshold_mb
        
        if response_time_threshold_s is not None:
            health_monitor.response_time_threshold_s = response_time_threshold_s
            updated["response_time_threshold_s"] = response_time_threshold_s
        
        if health_check_interval is not None:
            health_monitor.health_check_interval = health_check_interval
            updated["health_check_interval"] = health_check_interval
        
        return {
            "status": "success",
            "message": "Thresholds updated",
            "updated": updated
        }
        
    except Exception as e:
        logger.error(f"Failed to update thresholds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update thresholds: {e}")


@router.get("/validation/levels")
async def get_validation_levels():
    """
    Get available validation levels and their configurations
    """
    levels = {}
    
    for level in ValidationLevel:
        validator = get_validator(level)
        levels[level.value] = {
            "rules_count": len(validator.validation_rules),
            "thresholds": validator.quality_thresholds,
            "description": {
                "minimal": "Basic validation only",
                "standard": "Default balanced validation",
                "strict": "Comprehensive validation",
                "paranoid": "Maximum validation with redundancy"
            }.get(level.value, "Unknown")
        }
    
    return levels


@router.post("/validation/test")
async def test_validation(
    agent_name: str,
    level: str = Query("standard", enum=["minimal", "standard", "strict", "paranoid"])
):
    """
    Test validation for a specific agent
    
    Runs validation checks at the specified level
    """
    try:
        from app.core.agents import agent_registry, AgentExecutionContext
        
        # Get agent
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Create test context
        test_context = AgentExecutionContext(
            pipeline_id="validation-test",
            step_num=0,
            document_content="Test document for validation",
            components=[{"name": "test_component", "type": "process"}]
        )
        
        # Get validator
        validation_level = ValidationLevel(level)
        validator = get_validator(validation_level)
        
        # Run validation
        result = validator.validate_agent_input(agent, test_context)
        
        return {
            "agent": agent_name,
            "validation_level": level,
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test validation for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test validation: {e}")