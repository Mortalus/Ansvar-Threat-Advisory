"""
Structured Contextual Logging Configuration

Phase 2: Implements distributed system observability
- Request ID propagation across service boundaries
- Structured JSON logging for searchability
- Context-aware log formatting
- Performance tracking and tracing
"""

import logging
import json
import uuid
import time
from contextvars import ContextVar
from typing import Any, Dict, Optional
from datetime import datetime

# Context variables for request tracing
REQUEST_ID_CTX: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
USER_ID_CTX: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
PIPELINE_ID_CTX: ContextVar[Optional[str]] = ContextVar('pipeline_id', default=None)

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    Automatically includes request context in every log message
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Base log structure
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request context
        request_id = REQUEST_ID_CTX.get()
        if request_id:
            log_obj["request_id"] = request_id
            
        user_id = USER_ID_CTX.get()
        if user_id:
            log_obj["user_id"] = user_id
            
        pipeline_id = PIPELINE_ID_CTX.get()
        if pipeline_id:
            log_obj["pipeline_id"] = pipeline_id
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in (
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage'
            ):
                extra_fields[key] = value
        
        if extra_fields:
            log_obj["extra"] = extra_fields
            
        return json.dumps(log_obj, default=str)

class RequestContextLogger:
    """
    Logger wrapper that automatically includes request context
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def _log(self, level: int, message: str, **kwargs):
        """Log with automatic context inclusion"""
        extra = kwargs.copy()
        
        # Add performance metrics if provided
        if 'duration_ms' in extra:
            extra['performance'] = {
                'duration_ms': extra.pop('duration_ms'),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)

def setup_logging(
    level: str = "INFO",
    enable_structured: bool = True,
    log_file: Optional[str] = None
):
    """
    Configure structured logging for the application
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_structured: Whether to use JSON structured format
        log_file: Optional log file path
    """
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    
    if enable_structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    configure_app_loggers()

def configure_app_loggers():
    """Configure application-specific loggers"""
    
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Enable detailed logging for our application
    logging.getLogger("app").setLevel(logging.INFO)
    logging.getLogger("app.core").setLevel(logging.INFO)
    logging.getLogger("app.api").setLevel(logging.INFO)
    logging.getLogger("app.services").setLevel(logging.INFO)
    logging.getLogger("app.tasks").setLevel(logging.INFO)
    
    # Ensure Celery workers get our logs
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("celery.task").setLevel(logging.INFO)

def get_logger(name: str) -> RequestContextLogger:
    """Get a context-aware logger instance"""
    logger = logging.getLogger(name)
    return RequestContextLogger(logger)

def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None, 
    pipeline_id: Optional[str] = None
):
    """Set request context for logging"""
    if request_id:
        REQUEST_ID_CTX.set(request_id)
    if user_id:
        USER_ID_CTX.set(user_id)
    if pipeline_id:
        PIPELINE_ID_CTX.set(pipeline_id)

def clear_request_context():
    """Clear request context"""
    REQUEST_ID_CTX.set(None)
    USER_ID_CTX.set(None)
    PIPELINE_ID_CTX.set(None)

def generate_request_id() -> str:
    """Generate a unique request ID for tracing"""
    return f"req_{uuid.uuid4().hex[:12]}"

class LoggingMiddleware:
    """
    ASGI middleware for request logging and tracing
    """
    
    def __init__(self, app, skip_paths: list = None):
        self.app = app
        self.skip_paths = skip_paths or ['/health', '/metrics']
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Skip logging for certain paths
        path = scope.get("path", "")
        if any(skip_path in path for skip_path in self.skip_paths):
            await self.app(scope, receive, send)
            return
        
        # Generate or extract request ID
        request_id = None
        for name, value in scope.get("headers", []):
            if name == b"x-request-id":
                request_id = value.decode()
                break
        
        if not request_id:
            request_id = generate_request_id()
        
        # Set request context
        set_request_context(request_id=request_id)
        
        logger = get_logger("app.middleware")
        start_time = time.time()
        
        logger.info(
            f"🚀 Request started: {scope.get('method', 'UNKNOWN')} {path}",
            method=scope.get('method'),
            path=path,
            query_string=scope.get('query_string', b'').decode(),
            client=scope.get('client', ['unknown', 0])[0] if scope.get('client') else 'unknown'
        )
        
        # Process request
        try:
            await self.app(scope, receive, send)
            
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.info(
                f"✅ Request completed: {scope.get('method', 'UNKNOWN')} {path}",
                duration_ms=duration_ms,
                status="completed"
            )
            
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"❌ Request failed: {scope.get('method', 'UNKNOWN')} {path}",
                duration_ms=duration_ms,
                error=str(e),
                status="failed"
            )
            raise
        finally:
            clear_request_context()

# Performance tracking decorator
def track_performance(operation_name: str):
    """Decorator to track operation performance"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(f"app.performance.{func.__module__}")
            start_time = time.time()
            
            logger.debug(f"🔄 Starting {operation_name}")
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                logger.info(
                    f"✅ Completed {operation_name}",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    status="success"
                )
                
                return result
                
            except Exception as e:
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                logger.error(
                    f"❌ Failed {operation_name}",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    error=str(e),
                    status="failed"
                )
                raise
        
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(f"app.performance.{func.__module__}")
            start_time = time.time()
            
            logger.debug(f"🔄 Starting {operation_name}")
            
            try:
                result = func(*args, **kwargs)
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                logger.info(
                    f"✅ Completed {operation_name}",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    status="success"
                )
                
                return result
                
            except Exception as e:
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                logger.error(
                    f"❌ Failed {operation_name}",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    error=str(e),
                    status="failed"
                )
                raise
        
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator