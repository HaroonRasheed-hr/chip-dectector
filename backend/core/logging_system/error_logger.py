"""Convenience wrapper around the errors logger."""
from core.logging_system.logger_config import get_errors_logger

logger = get_errors_logger()


def error(message: str, *args, **kwargs) -> None:
    logger.error(message, *args, **kwargs)


def exception(message: str, *args, **kwargs) -> None:
    """Log an error and include the active traceback."""
    logger.exception(message, *args, **kwargs)
