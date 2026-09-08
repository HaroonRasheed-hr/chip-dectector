"""Telemetry aggregator — combines all collectors into one snapshot dict.

The shape returned here is the payload published to ``visionpulse/system/monitor``
and surfaced via the ``GET /api/monitoring/metrics/`` endpoint.
"""
from typing import Any

from core.monitoring import (
    cpu_monitor,
    disk_monitor,
    gpu_monitor,
    memory_monitor,
    uptime_monitor,
)
from core.persistence.jsonl_writer import utc_iso_timestamp


def collect_snapshot() -> dict[str, Any]:
    """Single point-in-time reading of every monitored metric."""
    return {
        'timestamp': utc_iso_timestamp(),
        'cpu': cpu_monitor.collect(),
        'memory': memory_monitor.collect(),
        'disk': disk_monitor.collect(),
        'gpu': gpu_monitor.collect(),
        'uptime': uptime_monitor.collect(),
    }
