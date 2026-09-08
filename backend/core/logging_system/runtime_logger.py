"""Convenience wrapper around the runtime logger."""
from core.logging_system.logger_config import get_runtime_logger

logger = get_runtime_logger()


def info(message: str, *args, **kwargs) -> None:
    logger.info(message, *args, **kwargs)


def debug(message: str, *args, **kwargs) -> None:
    logger.debug(message, *args, **kwargs)
