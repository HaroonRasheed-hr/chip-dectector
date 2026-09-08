"""CPU utilization collector — spec A.5."""
from typing import Any

import psutil

from core.errors import monitoring_error_handler


def collect() -> dict[str, Any]:
    try:
        return {
            'percent': psutil.cpu_percent(interval=None),
            'count_logical': psutil.cpu_count(logical=True),
            'count_physical': psutil.cpu_count(logical=False),
        }
    except Exception as exc:  # noqa: BLE001
        monitoring_error_handler.report('cpu collector failed', exc=exc)
        return {'percent': None, 'count_logical': None, 'count_physical': None}
