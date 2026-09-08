"""MQTT domain: broker disconnections, publish failures, topic errors."""
from typing import Any, Optional

from core.errors.error_node_handler import capture_error

DOMAIN = 'MQTT'


def report(message: str, *, exc: Optional[BaseException] = None,
           context: Optional[dict[str, Any]] = None) -> None:
    capture_error(DOMAIN, message, exc=exc, context=context)
