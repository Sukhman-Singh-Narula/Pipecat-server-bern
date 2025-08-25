"""
Utilities package - simplified version
"""

import logging
from loguru import logger as loguru_logger


def setup_logging(level="INFO"):
    """Setup logging configuration"""
    loguru_logger.remove()
    loguru_logger.add(
        sink=lambda message: print(message, end=""),
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    return loguru_logger


async def handle_generic_error(error: Exception, context: str = ""):
    """Handle generic errors with logging"""
    loguru_logger.error(f"Error in {context}: {str(error)}")
    return {
        "error": "Internal server error",
        "context": context,
        "details": str(error)
    }

__all__ = ["setup_logging", "handle_generic_error"]
