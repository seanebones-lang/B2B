"""Structured logging configuration"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional
import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_json: bool = False
) -> None:
    """
    Setup structured logging with structlog
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        enable_json: Enable JSON logging format (for production)
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if enable_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a structured logger instance
    
    Args:
        name: Logger name (defaults to calling module)
        
    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


# Initialize logging on import
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    enable_json=os.getenv("ENVIRONMENT") == "production"
)
