"""
Logging Configuration
Structured logging with loguru
"""
import sys
from typing import Optional

from loguru import logger


def get_logger(name: Optional[str] = None):
    """
    Get configured logger instance.

    Args:
        name: Logger name (optional)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing message")
    """
    # Remove default handler
    logger.remove()

    # Add custom handler with colors
    logger.add(
        sys.stdout,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level="INFO",
    )

    # Add file handler for errors
    logger.add(
        "logs/errors.log",
        rotation="10 MB",
        retention="1 week",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    )

    if name:
        return logger.bind(name=name)

    return logger
