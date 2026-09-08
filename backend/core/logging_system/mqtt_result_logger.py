"""Structured per-event logger for MQTT publish/subscribe activity.

Every event becomes one JSON object on a single line in
``logs/mqtt-result.log``. The schema is intentionally flat so the file
can be ingested by jq, grep, or any log shipper without further
processing.

Common fields:
  - ``timestamp``  ISO-8601 UTC, millisecond precision (e.g. ``2026-05-16T21:30:00.123Z``)
  - ``event``      ``publish`` | ``receive`` | ``connection`` | ``error``
  - ``topic``      MQTT topic (omitted for connection events)
  - ``payload``    Original Python dict / decoded string. Long strings
                   (e.g. base64 images) are truncated to keep the file
                   readable — the full byte count is preserved.

Event-specific fields:
  - publish    →  ``status`` (``ok`` | ``queued`` | ``failed``),
                  ``qos``, ``retain``, optional ``error``,
                  optional ``queue_depth`` (when status=queued).
  - receive    →  no extras — payload is the decoded message.
  - connection →  ``state`` (``starting`` | ``connected`` |
                  ``disconnected`` | ``connect_failed`` |
                  ``connect_refused`` | ``stopped``), optional ``detail``.
  - error      →  ``error`` plus any caller-supplied context.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping

from core.logging_system.logger_config import get_mqtt_result_logger


logger = get_mqtt_result_logger()

# Strings longer than this get summarised — keeps base64 images and
# huge JSON blobs from blowing up the log file.
_MAX_FIELD_LEN = 512


def _utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec='milliseconds')
        .replace('+00:00', 'Z')
    )


def _truncate(value: Any) -> Any:
    if isinstance(value, str):
        if len(value) > _MAX_FIELD_LEN:
            return f'<truncated, {len(value)} chars>'
        return value
    if isinstance(value, Mapping):
        return {k: _truncate(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_truncate(v) for v in value]
    return value


def _emit(event: dict[str, Any]) -> None:
    event.setdefault('timestamp', _utc_iso())
    logger.info(json.dumps(event, separators=(',', ':'), default=str))


# ── Publish / subscribe events ───────────────────────────────────────────────

def log_publish(
    topic: str,
    payload: Any,
    status: str,
    *,
    qos: int | None = None,
    retain: bool = False,
    error: str | None = None,
    queue_depth: int | None = None,
) -> None:
    """Record a publish attempt.

    ``status`` is one of: ``"ok"`` (broker accepted), ``"queued"`` (broker
    unreachable — buffered for replay), ``"failed"`` (publish error).
    """
    event: dict[str, Any] = {
        'event': 'publish',
        'topic': topic,
        'status': status,
        'qos': qos,
        'retain': retain,
        'payload': _truncate(payload),
    }
    if error is not None:
        event['error'] = str(error)
    if queue_depth is not None:
        event['queue_depth'] = queue_depth
    _emit(event)


def log_receive(topic: str, payload: Any) -> None:
    """Record an inbound message from a subscribed topic."""
    _emit({
        'event': 'receive',
        'topic': topic,
        'payload': _truncate(payload),
    })


# ── Connection / lifecycle events ────────────────────────────────────────────

def log_connection(state: str, **detail: Any) -> None:
    """Record a broker lifecycle / connection-state change.

    ``state`` is one of: ``"starting"``, ``"connected"``,
    ``"disconnected"``, ``"connect_failed"``, ``"connect_refused"``,
    ``"stopped"``.
    """
    event: dict[str, Any] = {'event': 'connection', 'state': state}
    if detail:
        event['detail'] = _truncate(detail)
    _emit(event)


# ── Error events ─────────────────────────────────────────────────────────────

def log_error(error: str, *, topic: str | None = None, **context: Any) -> None:
    """Record a failure that is not a direct publish/receive outcome.

    Use this for serialise errors, command-handler exceptions, payload
    decode failures, etc. Direct publish failures should call
    ``log_publish(..., status='failed', error=...)`` instead so they
    stay correlated with their topic.
    """
    event: dict[str, Any] = {'event': 'error', 'error': str(error)}
    if topic is not None:
        event['topic'] = topic
    if context:
        event['context'] = _truncate(context)
    _emit(event)
