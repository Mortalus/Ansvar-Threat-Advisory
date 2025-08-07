"""
Circuit Breaker and Retry Patterns for Distributed System Resilience

Implements defensive programming patterns for external dependencies:
- Database connections with exponential backoff
- LLM API calls with circuit breakers  
- Graceful degradation strategies
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

# Type variables for generic retry decorators
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

class CircuitBreakerState:
    """Circuit breaker state management"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests  
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls
    Prevents cascading failures in distributed systems
    """
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitBreakerState.CLOSED
        
    def __call__(self, func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == CircuitBreakerState.OPEN:
                if time.time() - self.last_failure_time < self.timeout:
                    logger.warning(f"🚫 Circuit breaker OPEN for {func.__name__}, rejecting call")
                    raise Exception(f"Circuit breaker open for {func.__name__}")
                else:
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"🔄 Circuit breaker HALF_OPEN for {func.__name__}, testing service")
                    
            try:
                result = await func(*args, **kwargs)
                
                # Success - reset circuit breaker
                if self.state == CircuitBreakerState.HALF_OPEN:
                    logger.info(f"✅ Service recovered, circuit breaker CLOSED for {func.__name__}")
                    
                self.failure_count = 0
                self.state = CircuitBreakerState.CLOSED
                return result
                
            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitBreakerState.OPEN
                    logger.error(
                        f"💥 Circuit breaker OPEN for {func.__name__} "
                        f"(failures: {self.failure_count}/{self.failure_threshold})"
                    )
                else:
                    logger.warning(
                        f"⚠️ Service failure {self.failure_count}/{self.failure_threshold} "
                        f"for {func.__name__}: {e}"
                    )
                
                raise
                
        return wrapper

# Database retry decorator with exponential backoff
def with_db_retry(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10
):
    """
    Retry decorator for database operations
    Handles transient connection issues with exponential backoff
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type((
            ConnectionError,
            OSError,  # Includes network errors
            Exception  # Temporary - narrow this down for production
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )

# LLM API retry decorator with circuit breaker
def with_llm_retry(
    max_attempts: int = 3,
    min_wait: float = 2,
    max_wait: float = 30
):
    """
    Retry decorator for LLM API calls
    Handles rate limiting and transient API failures
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError,
            # Add specific LLM provider exceptions here
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )

# Circuit breaker instances for different services
db_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=30.0,
    expected_exception=Exception
)

llm_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=120.0,  # Longer timeout for LLM services
    expected_exception=Exception
)

# Fallback strategies
class FallbackStrategies:
    """Graceful degradation strategies for when services fail"""
    
    @staticmethod
    async def get_sample_dfd_components() -> Dict[str, Any]:
        """Fallback DFD components when extraction fails"""
        return {
            "project_name": "Fallback E-commerce Example",
            "project_version": "1.0",
            "industry_context": "E-commerce/Retail",
            "external_entities": ["Customer", "Payment Processor", "Admin"],
            "assets": ["Customer Database", "Product Catalog", "Payment Gateway"],
            "processes": ["Web Server", "API Gateway", "Auth Service"],
            "trust_boundaries": ["Internet", "DMZ", "Internal Network"],
            "data_flows": [{
                "source": "Customer",
                "destination": "Web Server", 
                "data_description": "User authentication and shopping requests",
                "data_classification": "PII",
                "protocol": "HTTPS",
                "authentication_mechanism": "JWT + Session"
            }],
            "fallback_reason": "DFD extraction service unavailable"
        }
    
    @staticmethod 
    async def get_sample_threats() -> Dict[str, Any]:
        """Fallback threat data when generation fails"""
        return {
            "threats": [
                {
                    "Threat Category": "Spoofing",
                    "Threat Name": "Authentication Bypass",
                    "Description": "Attacker bypasses authentication to access unauthorized resources",
                    "Potential Impact": "High",
                    "Likelihood": "Medium",
                    "Suggested Mitigation": "Implement multi-factor authentication and session management"
                }
            ],
            "total_count": 1,
            "fallback_reason": "Threat generation service unavailable"
        }

# Resilient wrapper functions
@db_circuit_breaker
@with_db_retry(max_attempts=3)
async def resilient_db_operation(operation_func: Callable, *args, **kwargs):
    """
    Execute database operation with circuit breaker and retry logic
    """
    logger.info(f"🔄 Executing resilient DB operation: {operation_func.__name__}")
    return await operation_func(*args, **kwargs)

@llm_circuit_breaker  
@with_llm_retry(max_attempts=3)
async def resilient_llm_operation(operation_func: Callable, *args, **kwargs):
    """
    Execute LLM operation with circuit breaker and retry logic
    """
    logger.info(f"🧠 Executing resilient LLM operation: {operation_func.__name__}")
    return await operation_func(*args, **kwargs)

# Health check for circuit breakers
def get_circuit_breaker_status() -> Dict[str, Any]:
    """Get status of all circuit breakers for monitoring"""
    return {
        "database": {
            "state": db_circuit_breaker.state,
            "failure_count": db_circuit_breaker.failure_count,
            "last_failure": db_circuit_breaker.last_failure_time
        },
        "llm": {
            "state": llm_circuit_breaker.state,
            "failure_count": llm_circuit_breaker.failure_count,
            "last_failure": llm_circuit_breaker.last_failure_time
        }
    }