"""System uptime collector — spec A.5."""
import time
from typing import Any

import psutil

from core.errors import monitoring_error_handler


def collect() -> dict[str, Any]:
    try:
        boot = psutil.boot_time()
        return {
            'boot_time': boot,
            'uptime_seconds': max(0, int(time.time() - boot)),
        }
    except Exception as exc:  # noqa: BLE001
        monitoring_error_handler.report('uptime collector failed', exc=exc)
        return {'boot_time': None, 'uptime_seconds': None}
