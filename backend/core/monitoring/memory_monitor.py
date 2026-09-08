"""Memory usage collector — spec A.5."""
from typing import Any

import psutil

from core.errors import monitoring_error_handler


def collect() -> dict[str, Any]:
    try:
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'used': mem.used,
            'available': mem.available,
            'percent': mem.percent,
        }
    except Exception as exc:  # noqa: BLE001
        monitoring_error_handler.report('memory collector failed', exc=exc)
        return {'total': None, 'used': None, 'available': None, 'percent': None}
