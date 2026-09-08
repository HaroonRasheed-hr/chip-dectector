"""General Error Node System (spec A.6.1).

Single chokepoint every domain calls to record an error. Each event is:
  1. Written to ``logs/errors.log`` (always, even when MQTT is down).
  2. Published to ``visionpulse/system/errors`` (best-effort, queued if offline).

Keeping the routing here means new error categories slot in by passing a
different ``domain`` string — no new wiring needed.
"""
import traceback
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from core.logging_system.error_logger import error as log_error
from core.logging_system.error_logger import exception as log_error_exception
from core.mqtt.topics import SYSTEM_ERRORS
from core.persistence.jsonl_writer import utc_iso_timestamp


@dataclass
class ErrorEvent:
    domain: str
    message: str
    severity: str = 'error'  # 'error' | 'critical' | 'warning'
    context: dict[str, Any] = field(default_factory=dict)
    exception_type: Optional[str] = None
    traceback_str: Optional[str] = None
    timestamp: str = field(default_factory=utc_iso_timestamp)


def capture_error(
    domain: str,
    message: str,
    *,
    exc: Optional[BaseException] = None,
    context: Optional[dict[str, Any]] = None,
    severity: str = 'error',
) -> ErrorEvent:
    """Record an error: log it + publish to MQTT.

    ``domain`` should be one of the values listed in spec A.6.1 (Backend,
    AI Pipeline, MQTT, File Handling, GPU Execution, Serialization,
    Monitoring Services, …).
    """
    event = ErrorEvent(
        domain=domain,
        message=message,
        severity=severity,
        context=context or {},
        exception_type=type(exc).__name__ if exc else None,
        traceback_str=''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)) if exc else None,
    )

    # 1. local log
    if exc is not None:
        log_error_exception('[%s] %s | context=%s', domain, message, event.context)
    else:
        log_error('[%s] %s | context=%s', domain, message, event.context)

    # 2. MQTT publish (lazy import to avoid circular import at module load)
    try:
        from core.mqtt.mqtt_connection import publish_json

        publish_json(SYSTEM_ERRORS, asdict(event))
    except Exception:  # noqa: BLE001 — MQTT path must never raise back here
        log_error_exception('Error-node MQTT publish failed for domain=%s', domain)

    return event
