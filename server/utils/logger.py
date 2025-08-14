"""
Logging utilities and setup
"""
import logging
import sys
from datetime import datetime
from typing import Optional


class LoggerMixin:
    """Mixin class to add logging capabilities"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def log_error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)


def setup_logging(log_level: str = "info"):
    """
    Setup application logging configuration
    
    Args:
        log_level: Logging level (debug, info, warning, error)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from external libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info(f"Logging initialized at {log_level.upper()} level")


def log_security_event(violation_type: str, identifier: str, details: dict):
    """
    Log security events
    
    Args:
        violation_type: Type of security violation
        identifier: Identifier associated with the violation (IP, device_id, etc.)
        details: Additional details about the violation
    """
    security_logger = logging.getLogger("security")
    security_logger.warning(
        f"Security violation: {violation_type}",
        extra={
            "violation_type": violation_type,
            "identifier": identifier,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
    )
