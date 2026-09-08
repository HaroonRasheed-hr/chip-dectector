"""Fault-tolerant facade for persisting inference measurements."""
from typing import Any

from django.conf import settings

from core.persistence.jsonl_writer import append_jsonl


def persist_measurement(measurement: dict[str, Any]) -> bool:
    """Append a single inference measurement to ``measurements.jsonl``.

    Returns the success flag from :func:`append_jsonl`.
    """
    return append_jsonl(settings.MEASUREMENTS_JSONL_PATH, measurement)
