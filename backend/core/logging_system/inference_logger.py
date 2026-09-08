"""Convenience wrapper around the inference logger."""
from core.logging_system.logger_config import get_inference_logger

logger = get_inference_logger()


def info(message: str, *args, **kwargs) -> None:
    logger.info(message, *args, **kwargs)


def error(message: str, *args, **kwargs) -> None:
    logger.error(message, *args, **kwargs)


def exception(message: str, *args, **kwargs) -> None:
    logger.exception(message, *args, **kwargs)
