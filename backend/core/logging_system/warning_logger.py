"""Convenience wrapper around the warnings logger."""
from core.logging_system.logger_config import get_warnings_logger

logger = get_warnings_logger()


def warning(message: str, *args, **kwargs) -> None:
    logger.warning(message, *args, **kwargs)
