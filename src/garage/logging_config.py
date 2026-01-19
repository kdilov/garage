# src/garage/logging_config.py
"""
Structured logging configuration for the Garage Inventory application.

WHY THIS EXISTS:
- print() statements don't help you debug production issues
- JSON logs can be parsed by CloudWatch, Datadog, Splunk, etc.
- Consistent log format makes it easy to search and alert on issues
- Different formats for dev (readable) vs prod (machine-parseable)

WHAT IT DOES:
- In production (LOG_FORMAT=json): Outputs single-line JSON for log aggregators
- In development (LOG_FORMAT=text): Outputs colored, human-readable logs
- Automatically includes context like user_id, box_id when available
- Adds request IDs for tracing requests through the system
"""
import json
import logging
import logging.config
from datetime import datetime, timezone
from typing import Any

from flask import Flask, g, request


class JSONFormatter(logging.Formatter):
    """
    Formats logs as single-line JSON objects.
    
    Example output:
    {"timestamp": "2024-01-15T10:30:00Z", "level": "INFO", "logger": "garage.routes.boxes", 
     "message": "Box created", "user_id": 1, "box_id": 42}
    
    This format is essential for production because:
    1. Log aggregators can parse and index each field
    2. You can search for all actions by a specific user_id
    3. You can alert on error counts, response times, etc.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add request context if we're inside a request
        # This helps trace a user's journey through the app
        try:
            if request:
                log_data['request_id'] = getattr(g, 'request_id', None)
                log_data['path'] = request.path
                log_data['method'] = request.method
        except RuntimeError:
            # We're outside a request context (e.g., during startup)
            pass
        
        # Add any extra fields that were passed to the logger
        # e.g., logger.info("Box created", extra={'box_id': 42})
        extra_fields = [
            'user_id', 'box_id', 'item_id', 'email',
            'duration_ms', 'error', 'status_code',
            'storage_backend', 'file_path', 'bucket'
        ]
        for field in extra_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Include full exception traceback if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter with colors for development.
    
    Example output:
    INFO     garage.routes.boxes: Box created [user_id=1, box_id=42]
    
    Colors make it easy to spot errors (red) vs info (green) when
    watching logs scroll by during development.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Build a string showing any extra context
        extras = []
        for field in ['user_id', 'box_id', 'item_id', 'error']:
            if hasattr(record, field):
                extras.append(f"{field}={getattr(record, field)}")
        
        extra_str = f" [{', '.join(extras)}]" if extras else ""
        
        formatted = (
            f"{color}{record.levelname:8}{self.RESET} "
            f"{record.name}: {record.getMessage()}{extra_str}"
        )
        
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def configure_logging(app: Flask) -> None:
    """
    Configure logging based on application configuration.
    
    Call this early in create_app() so all other components can log properly.
    
    Config options:
        LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL
        LOG_FORMAT: 'json' (production) or 'text' (development)
    """
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_format = app.config.get('LOG_FORMAT', 'json')
    
    # Choose formatter based on environment
    if log_format == 'json':
        formatter_config = {'()': f'{__name__}.JSONFormatter'}
    else:
        formatter_config = {'()': f'{__name__}.DevelopmentFormatter'}
    
    # Standard Python logging configuration dictionary
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': formatter_config,
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'standard',
                'stream': 'ext://sys.stdout',
            },
        },
        'root': {
            'level': log_level,
            'handlers': ['console'],
        },
        'loggers': {
            # Our application logs
            'garage': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False,
            },
            # Reduce noise from third-party libraries
            'werkzeug': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False,
            },
            'sqlalchemy.engine': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False,
            },
            'botocore': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False,
            },
        },
    }
    
    logging.config.dictConfig(config)
    
    # Add a unique request ID to every request for tracing
    @app.before_request
    def add_request_id():
        import uuid
        g.request_id = str(uuid.uuid4())[:8]
    
    # Log completed requests in production (useful for debugging)
    if log_format == 'json':
        @app.after_request
        def log_request(response):
            logger = logging.getLogger('garage.requests')
            logger.info(
                "Request completed",
                extra={
                    'status_code': response.status_code,
                    'path': request.path,
                    'method': request.method,
                }
            )
            return response