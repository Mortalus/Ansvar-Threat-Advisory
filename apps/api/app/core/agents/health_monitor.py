"""
Agent Health Monitoring and Self-Healing System

Provides comprehensive health monitoring, automatic recovery, and performance tracking
for the modular agent system.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import traceback

# Try to import psutil for resource monitoring (optional)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from .base import BaseAgent, AgentExecutionContext
from .registry import agent_registry

logger = logging.getLogger(__name__)


@dataclass
class AgentHealthMetrics:
    """Comprehensive health metrics for an agent"""
    agent_name: str
    is_healthy: bool = True
    last_health_check: datetime = field(default_factory=datetime.utcnow)
    consecutive_failures: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    last_execution_time: Optional[float] = None
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_history: deque = field(default_factory=lambda: deque(maxlen=10))
    recovery_attempts: int = 0
    circuit_breaker_state: str = "closed"  # closed, open, half-open
    circuit_breaker_opens_at: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_executions == 0:
            return 100.0
        return (self.successful_executions / self.total_executions) * 100
    
    @property
    def reliability_score(self) -> float:
        """Calculate overall reliability score (0-100)"""
        factors = []
        
        # Success rate (40% weight)
        factors.append(self.success_rate * 0.4)
        
        # Uptime factor (30% weight) - penalize consecutive failures
        uptime_factor = max(0, 100 - (self.consecutive_failures * 20))
        factors.append(uptime_factor * 0.3)
        
        # Performance factor (30% weight) - based on response times
        if self.response_times:
            avg_time = sum(self.response_times) / len(self.response_times)
            # Assume <5s is excellent, >30s is poor
            perf_factor = max(0, min(100, 100 - ((avg_time - 5) * 3)))
            factors.append(perf_factor * 0.3)
        else:
            factors.append(30)  # Default 30% if no data
        
        return sum(factors)
    
    def record_execution(self, success: bool, execution_time: float, error: Optional[str] = None):
        """Record an execution result"""
        self.total_executions += 1
        self.last_execution_time = execution_time
        self.response_times.append(execution_time)
        
        if success:
            self.successful_executions += 1
            self.consecutive_failures = 0
            if self.circuit_breaker_state == "half-open":
                # Successful execution in half-open state, close the circuit
                self.circuit_breaker_state = "closed"
                logger.info(f"Circuit breaker for {self.agent_name} closed after successful execution")
        else:
            self.failed_executions += 1
            self.consecutive_failures += 1
            self.last_error = error
            self.last_error_time = datetime.utcnow()
            if error:
                self.error_history.append({
                    "error": error[:500],  # Limit error message size
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Check if circuit breaker should open
            if self.consecutive_failures >= 3 and self.circuit_breaker_state == "closed":
                self.circuit_breaker_state = "open"
                self.circuit_breaker_opens_at = datetime.utcnow() + timedelta(minutes=5)
                logger.warning(f"Circuit breaker opened for {self.agent_name} after {self.consecutive_failures} failures")
        
        # Update average execution time
        if self.response_times:
            self.average_execution_time = sum(self.response_times) / len(self.response_times)


class AgentHealthMonitor:
    """
    Comprehensive health monitoring system for agents
    Includes circuit breakers, self-healing, and performance tracking
    """
    
    def __init__(self):
        self.metrics: Dict[str, AgentHealthMetrics] = {}
        self.monitoring_enabled = True
        self.health_check_interval = 60  # seconds
        self.recovery_strategies: Dict[str, callable] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Configuration thresholds
        self.failure_threshold = 3  # Consecutive failures before circuit opens
        self.recovery_timeout = 300  # 5 minutes in half-open state
        self.memory_threshold_mb = 500  # Alert if agent uses >500MB
        self.response_time_threshold_s = 30  # Alert if response >30s
        
    def get_or_create_metrics(self, agent_name: str) -> AgentHealthMetrics:
        """Get or create metrics for an agent"""
        if agent_name not in self.metrics:
            self.metrics[agent_name] = AgentHealthMetrics(agent_name=agent_name)
        return self.metrics[agent_name]
    
    async def check_agent_health(self, agent: BaseAgent) -> bool:
        """
        Perform comprehensive health check on an agent
        Returns True if healthy, False otherwise
        """
        agent_name = agent.get_metadata().name
        metrics = self.get_or_create_metrics(agent_name)
        
        try:
            # Check circuit breaker state
            if metrics.circuit_breaker_state == "open":
                if datetime.utcnow() >= metrics.circuit_breaker_opens_at:
                    # Time to try half-open state
                    metrics.circuit_breaker_state = "half-open"
                    logger.info(f"Circuit breaker for {agent_name} entering half-open state")
                else:
                    # Still in open state
                    return False
            
            # Test agent validation with minimal context
            test_context = AgentExecutionContext(
                pipeline_id="health_check",
                document_text="",
                components={}
            )
            
            # Quick validation check
            start_time = time.time()
            is_valid = agent.validate_context(test_context)
            validation_time = time.time() - start_time
            
            # Check system resources if available
            if HAS_PSUTIL:
                process = psutil.Process()
                metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                metrics.cpu_usage_percent = process.cpu_percent(interval=0.1)
            else:
                # Use placeholder values if psutil not available
                metrics.memory_usage_mb = 0.0
                metrics.cpu_usage_percent = 0.0
            
            # Update health status
            metrics.is_healthy = is_valid and validation_time < 5.0  # 5 second timeout
            metrics.last_health_check = datetime.utcnow()
            
            # Alert on resource usage
            if metrics.memory_usage_mb > self.memory_threshold_mb:
                logger.warning(f"Agent {agent_name} using high memory: {metrics.memory_usage_mb:.2f}MB")
            
            return metrics.is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed for {agent_name}: {e}")
            metrics.is_healthy = False
            metrics.last_error = str(e)
            metrics.last_error_time = datetime.utcnow()
            return False
    
    async def monitor_execution(self, agent_name: str, execution_coroutine):
        """
        Monitor an agent execution with comprehensive tracking
        Wraps execution with health monitoring, timeout, and recovery
        """
        metrics = self.get_or_create_metrics(agent_name)
        
        # Check circuit breaker
        if metrics.circuit_breaker_state == "open":
            remaining = (metrics.circuit_breaker_opens_at - datetime.utcnow()).total_seconds()
            raise Exception(f"Circuit breaker open for {agent_name}. Retry in {remaining:.0f} seconds")
        
        start_time = time.time()
        success = False
        error_msg = None
        result = None
        
        try:
            # Execute with timeout
            timeout = 60  # 60 second timeout per agent
            result = await asyncio.wait_for(execution_coroutine, timeout=timeout)
            success = True
            
        except asyncio.TimeoutError:
            error_msg = f"Agent {agent_name} execution timed out after {timeout} seconds"
            logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Agent {agent_name} execution failed: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            
        finally:
            execution_time = time.time() - start_time
            metrics.record_execution(success, execution_time, error_msg)
            
            # Log performance warning if slow
            if execution_time > self.response_time_threshold_s:
                logger.warning(f"Agent {agent_name} slow response: {execution_time:.2f}s")
            
            # Attempt recovery if needed
            if not success and metrics.consecutive_failures >= self.failure_threshold:
                await self.attempt_recovery(agent_name)
        
        if not success:
            raise Exception(error_msg or f"Agent {agent_name} execution failed")
        
        return result
    
    async def attempt_recovery(self, agent_name: str):
        """
        Attempt to recover a failing agent
        """
        metrics = self.get_or_create_metrics(agent_name)
        metrics.recovery_attempts += 1
        
        logger.info(f"Attempting recovery for {agent_name} (attempt #{metrics.recovery_attempts})")
        
        try:
            # Strategy 1: Reload agent configuration
            agent = agent_registry.get_agent(agent_name)
            if agent:
                # Reset agent to default configuration
                default_config = {}
                await agent_registry.reload_agent(agent_name, default_config)
                logger.info(f"Reset {agent_name} to default configuration")
            
            # Strategy 2: Clear any cached data
            if hasattr(agent, 'clear_cache'):
                agent.clear_cache()
                logger.info(f"Cleared cache for {agent_name}")
            
            # Strategy 3: Custom recovery strategy if registered
            if agent_name in self.recovery_strategies:
                await self.recovery_strategies[agent_name](agent)
                logger.info(f"Applied custom recovery strategy for {agent_name}")
            
            # Test if recovery worked
            if await self.check_agent_health(agent):
                logger.info(f"✅ Recovery successful for {agent_name}")
                metrics.consecutive_failures = 0
                metrics.circuit_breaker_state = "closed"
            else:
                logger.warning(f"Recovery attempt failed for {agent_name}")
                
        except Exception as e:
            logger.error(f"Recovery attempt failed for {agent_name}: {e}")
    
    def register_recovery_strategy(self, agent_name: str, strategy: callable):
        """Register a custom recovery strategy for an agent"""
        self.recovery_strategies[agent_name] = strategy
        logger.info(f"Registered custom recovery strategy for {agent_name}")
    
    async def start_monitoring(self):
        """Start the background health monitoring task"""
        if self._monitoring_task:
            logger.warning("Monitoring already started")
            return
        
        self.monitoring_enabled = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Agent health monitoring started")
    
    async def stop_monitoring(self):
        """Stop the background health monitoring"""
        self.monitoring_enabled = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        logger.info("Agent health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_enabled:
            try:
                # Check health of all registered agents
                for agent in agent_registry.list_all_agents():
                    await self.check_agent_health(agent)
                
                # Check for agents needing recovery
                for agent_name, metrics in self.metrics.items():
                    if not metrics.is_healthy and metrics.consecutive_failures >= self.failure_threshold:
                        if metrics.recovery_attempts < 3:  # Max 3 recovery attempts
                            await self.attempt_recovery(agent_name)
                
                # Wait before next check
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Short pause on error
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive health report for all agents
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": "healthy",
            "total_agents": len(self.metrics),
            "healthy_agents": 0,
            "unhealthy_agents": 0,
            "agents": {}
        }
        
        for agent_name, metrics in self.metrics.items():
            agent_health = {
                "is_healthy": metrics.is_healthy,
                "reliability_score": round(metrics.reliability_score, 2),
                "success_rate": round(metrics.success_rate, 2),
                "total_executions": metrics.total_executions,
                "consecutive_failures": metrics.consecutive_failures,
                "average_response_time": round(metrics.average_execution_time, 2),
                "circuit_breaker_state": metrics.circuit_breaker_state,
                "last_error": metrics.last_error,
                "last_health_check": metrics.last_health_check.isoformat() if metrics.last_health_check else None
            }
            
            report["agents"][agent_name] = agent_health
            
            if metrics.is_healthy:
                report["healthy_agents"] += 1
            else:
                report["unhealthy_agents"] += 1
        
        # Determine overall health
        if report["unhealthy_agents"] == 0:
            report["overall_health"] = "healthy"
        elif report["unhealthy_agents"] < report["total_agents"] / 2:
            report["overall_health"] = "degraded"
        else:
            report["overall_health"] = "unhealthy"
        
        return report
    
    def get_agent_metrics(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed metrics for a specific agent"""
        if agent_name not in self.metrics:
            return None
        
        metrics = self.metrics[agent_name]
        return {
            "agent_name": agent_name,
            "is_healthy": metrics.is_healthy,
            "reliability_score": round(metrics.reliability_score, 2),
            "success_rate": round(metrics.success_rate, 2),
            "total_executions": metrics.total_executions,
            "successful_executions": metrics.successful_executions,
            "failed_executions": metrics.failed_executions,
            "consecutive_failures": metrics.consecutive_failures,
            "average_execution_time": round(metrics.average_execution_time, 2),
            "last_execution_time": round(metrics.last_execution_time, 2) if metrics.last_execution_time else None,
            "memory_usage_mb": round(metrics.memory_usage_mb, 2),
            "cpu_usage_percent": round(metrics.cpu_usage_percent, 2),
            "circuit_breaker_state": metrics.circuit_breaker_state,
            "recovery_attempts": metrics.recovery_attempts,
            "last_error": metrics.last_error,
            "last_error_time": metrics.last_error_time.isoformat() if metrics.last_error_time else None,
            "error_history": list(metrics.error_history),
            "recent_response_times": list(metrics.response_times)[-10:]  # Last 10
        }


# Global health monitor instance
health_monitor = AgentHealthMonitor()