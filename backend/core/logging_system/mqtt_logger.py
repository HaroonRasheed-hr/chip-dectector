"""Convenience wrapper around the MQTT logger.

Every MQTT lifecycle / publish / subscribe event flows through this
module so it lands in ``logs/mqtt.log``. ERROR/WARNING records are also
mirrored into ``logs/errors.log`` / ``logs/warnings.log`` by the
``LOGGING`` config on the same logger.
"""
from core.logging_system.logger_config import get_mqtt_logger

logger = get_mqtt_logger()


def info(message: str, *args, **kwargs) -> None:
    logger.info(message, *args, **kwargs)


def debug(message: str, *args, **kwargs) -> None:
    logger.debug(message, *args, **kwargs)


def warning(message: str, *args, **kwargs) -> None:
    logger.warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs) -> None:
    logger.error(message, *args, **kwargs)


def exception(message: str, *args, **kwargs) -> None:
    """Log an error and include the active traceback."""
    logger.exception(message, *args, **kwargs)
