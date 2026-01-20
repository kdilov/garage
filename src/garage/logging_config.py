# src/garage/logging_config.py
"""Structured logging configuration."""
import json
import logging
import logging.config
from datetime import datetime, timezone
from typing import Any

from flask import Flask, g, request


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production environments."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        try:
            if request:
                log_data['request_id'] = getattr(g, 'request_id', None)
                log_data['path'] = request.path
                log_data['method'] = request.method
        except RuntimeError:
            pass
        
        extra_fields = [
            'user_id', 'box_id', 'item_id', 'email',
            'duration_ms', 'error', 'status_code',
            'storage_backend', 'file_path', 'bucket'
        ]
        for field in extra_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


class DevelopmentFormatter(logging.Formatter):
    """Colored log formatter for development."""
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        
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
    """Configure logging based on application configuration."""
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_format = app.config.get('LOG_FORMAT', 'json')
    
    if log_format == 'json':
        formatter_config = {'()': f'{__name__}.JSONFormatter'}
    else:
        formatter_config = {'()': f'{__name__}.DevelopmentFormatter'}
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {'standard': formatter_config},
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
            'garage': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False,
            },
            'werkzeug': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
            'sqlalchemy.engine': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
            'botocore': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
        },
    }
    
    logging.config.dictConfig(config)
    
    @app.before_request
    def add_request_id():
        import uuid
        g.request_id = str(uuid.uuid4())[:8]
    
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
