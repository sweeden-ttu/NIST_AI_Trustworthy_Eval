"""Logging utilities for rd-agent-mcp."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """Set up logging for the application."""
    if format_string is None:
        format_string = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

    logger = logging.getLogger("rd-agent-mcp")
    logger.setLevel(getattr(logging, level.upper()))

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, level.upper()))
    formatter = logging.Formatter(format_string)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class LogContext:
    """Context manager for logging."""

    def __init__(self, logger: logging.Logger, context: str, level: str = "INFO"):
        self.logger = logger
        self.context = context
        self.level = getattr(logging, level.upper())
        self.original_level = None

    def __enter__(self):
        self.original_level = self.logger.level
        self.logger.setLevel(self.level)
        self.logger.debug(f"Entering: {self.context}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug(f"Exiting: {self.context}")
        if exc_type:
            self.logger.error(f"Error in {self.context}: {exc_val}")
        self.logger.setLevel(self.original_level)
