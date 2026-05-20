"""
Logging configuration using loguru.
"""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup application logging with loguru.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Remove default logger
    logger.remove()

    # Console logging
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # File logging - Application logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "app" / "app_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="00:00",  # New file at midnight
        retention="30 days",  # Keep logs for 30 days
        compression="zip",  # Compress old logs
        encoding="utf-8",
    )

    # File logging - Error logs
    logger.add(
        log_dir / "app" / "error_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        encoding="utf-8",
    )

    # File logging - Access logs
    logger.add(
        log_dir / "access" / "access_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {extra[client]} | {extra[method]} | {extra[path]} | {extra[status_code]} | {extra[response_time]}",
        level="INFO",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        filter=lambda record: "access" in record["extra"],
    )

    logger.info(f"Logging initialized with level: {log_level}")
