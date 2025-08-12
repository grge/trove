"""Production logging configuration with structured output."""

import logging
import sys
import json
from typing import Dict, Any, Optional
from datetime import datetime
import traceback


class TroveFormatter(logging.Formatter):
    """Custom formatter for Trove SDK logs with structured JSON output."""
    
    def __init__(self, include_context: bool = True, json_format: bool = True):
        self.include_context = include_context
        self.json_format = json_format
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        if self.json_format:
            return self._format_json(record)
        else:
            return self._format_text(record)
    
    def _format_json(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Build log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add context if available
        if self.include_context and hasattr(record, 'trove_context'):
            log_entry['context'] = record.trove_context
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        # Add performance metrics if available
        if hasattr(record, 'performance_metrics'):
            log_entry['performance'] = record.performance_metrics
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))
    
    def _format_text(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable text."""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build basic message
        message = f"{timestamp} - {record.name} - {record.levelname} - {record.getMessage()}"
        
        # Add context if available
        if self.include_context and hasattr(record, 'trove_context'):
            context_str = ', '.join(f"{k}={v}" for k, v in record.trove_context.items())
            message += f" | Context: {context_str}"
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            message += f" | Request: {record.request_id}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


class ContextualLogger:
    """Logger that maintains context across operations."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
        self.request_id: Optional[str] = None
    
    def set_context(self, **context):
        """Set context for subsequent log messages."""
        self.context.update(context)
    
    def set_request_id(self, request_id: str):
        """Set request ID for request tracing."""
        self.request_id = request_id
    
    def clear_context(self):
        """Clear all context."""
        self.context.clear()
        self.request_id = None
    
    def _create_record(self, level: int, message: str, **extra_context) -> logging.LogRecord:
        """Create log record with context."""
        # Merge context
        full_context = {**self.context, **extra_context}
        
        # Create log record
        record = self.logger.makeRecord(
            self.logger.name, level, __file__, 0, message, (), None
        )
        
        if full_context:
            record.trove_context = full_context
        if self.request_id:
            record.request_id = self.request_id
        
        return record
    
    def debug(self, message: str, **context):
        """Log debug message with context."""
        if self.logger.isEnabledFor(logging.DEBUG):
            record = self._create_record(logging.DEBUG, message, **context)
            self.logger.handle(record)
    
    def info(self, message: str, **context):
        """Log info message with context."""
        if self.logger.isEnabledFor(logging.INFO):
            record = self._create_record(logging.INFO, message, **context)
            self.logger.handle(record)
    
    def warning(self, message: str, **context):
        """Log warning message with context."""
        if self.logger.isEnabledFor(logging.WARNING):
            record = self._create_record(logging.WARNING, message, **context)
            self.logger.handle(record)
    
    def error(self, message: str, **context):
        """Log error message with context."""
        if self.logger.isEnabledFor(logging.ERROR):
            record = self._create_record(logging.ERROR, message, **context)
            self.logger.handle(record)
    
    def critical(self, message: str, **context):
        """Log critical message with context."""
        if self.logger.isEnabledFor(logging.CRITICAL):
            record = self._create_record(logging.CRITICAL, message, **context)
            self.logger.handle(record)
    
    def log_performance(self, message: str, metrics: Dict[str, Any], **context):
        """Log message with performance metrics."""
        if self.logger.isEnabledFor(logging.INFO):
            record = self._create_record(logging.INFO, message, **context)
            record.performance_metrics = metrics
            self.logger.handle(record)


def configure_logging(
    level: str = "INFO",
    format_style: str = "json",
    log_file: Optional[str] = None,
    include_context: bool = True
) -> logging.Logger:
    """Configure logging for the Trove SDK.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_style: Log format style ('json' or 'text')
        log_file: Optional file path for log output
        include_context: Whether to include context information in logs
    
    Returns:
        Configured root logger instance
    """
    
    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create root logger
    logger = logging.getLogger('trove')
    logger.setLevel(numeric_level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create handler
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    json_format = format_style.lower() == "json"
    formatter = TroveFormatter(include_context=include_context, json_format=json_format)
    
    handler.setFormatter(formatter)
    handler.setLevel(numeric_level)
    logger.addHandler(handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger


def configure_production_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_performance_logs: bool = True
) -> logging.Logger:
    """Configure logging for production environments.
    
    Args:
        log_level: Logging level for production
        log_file: File path for log output (uses stdout if None)
        enable_performance_logs: Whether to enable performance logging
    
    Returns:
        Configured logger
    """
    logger = configure_logging(
        level=log_level,
        format_style="json",  # Always use JSON in production
        log_file=log_file,
        include_context=True
    )
    
    if enable_performance_logs:
        # Set performance logger to INFO level
        perf_logger = logging.getLogger('trove.performance')
        perf_logger.setLevel(logging.INFO)
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return logger


def configure_development_logging(log_level: str = "DEBUG") -> logging.Logger:
    """Configure logging for development environments.
    
    Args:
        log_level: Logging level for development
    
    Returns:
        Configured logger
    """
    return configure_logging(
        level=log_level,
        format_style="text",  # Human-readable in development
        log_file=None,  # Output to console
        include_context=True
    )


# Pre-configured contextual loggers for different components
transport_logger = ContextualLogger('trove.transport')
search_logger = ContextualLogger('trove.search')
resources_logger = ContextualLogger('trove.resources')
citations_logger = ContextualLogger('trove.citations')
performance_logger = ContextualLogger('trove.performance')
models_logger = ContextualLogger('trove.models')


def get_logger(name: str) -> ContextualLogger:
    """Get a contextual logger for a specific component.
    
    Args:
        name: Logger name (will be prefixed with 'trove.')
    
    Returns:
        ContextualLogger instance
    """
    full_name = f"trove.{name}" if not name.startswith('trove.') else name
    return ContextualLogger(full_name)


def setup_request_logging(request_id: str) -> None:
    """Set up request-scoped logging context.
    
    Args:
        request_id: Unique identifier for the request
    """
    # Set request ID on all component loggers
    transport_logger.set_request_id(request_id)
    search_logger.set_request_id(request_id)
    resources_logger.set_request_id(request_id)
    citations_logger.set_request_id(request_id)


def clear_request_logging() -> None:
    """Clear request-scoped logging context."""
    transport_logger.clear_context()
    search_logger.clear_context()
    resources_logger.clear_context()
    citations_logger.clear_context()


# Default logger instance
_default_logger = None


def get_default_logger() -> logging.Logger:
    """Get the default configured logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = configure_logging()
    return _default_logger