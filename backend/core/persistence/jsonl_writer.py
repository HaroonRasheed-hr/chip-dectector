"""Append-only JSONL writer (spec A.4.3).

Every write is wrapped in try/except so a file-system error never propagates
into the inference pipeline. Failures are reported via the errors logger.
"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.logging_system.error_logger import exception as log_error_exception
from core.logging_system.runtime_logger import debug as log_debug

_WRITE_LOCK = threading.Lock()


def utc_iso_timestamp() -> str:
    """ISO 8601 UTC timestamp with second precision, e.g. ``2026-05-14T10:30:00Z``."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def append_jsonl(path: Path, payload: dict[str, Any]) -> bool:
    """Append one JSON object as a single line.

    Adds a ``timestamp`` field if the caller didn't supply one. Returns ``True``
    on success, ``False`` on any I/O or serialisation failure.
    """
    if 'timestamp' not in payload:
        payload = {'timestamp': utc_iso_timestamp(), **payload}

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        with _WRITE_LOCK:
            with path.open('a', encoding='utf-8') as fp:
                fp.write(line + '\n')
        log_debug('Appended measurement to %s', path.name)
        return True
    except (OSError, TypeError, ValueError):
        log_error_exception('Failed to append JSONL record to %s', path)
        return False
