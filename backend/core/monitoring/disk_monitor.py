"""Disk allocation + I/O collector — spec A.5."""
from typing import Any

import psutil

from core.errors import monitoring_error_handler


def collect() -> dict[str, Any]:
    partitions = []
    try:
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    'device': part.device,
                    'mountpoint': part.mountpoint,
                    'fstype': part.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent,
                })
            except (PermissionError, OSError):
                continue
    except Exception as exc:  # noqa: BLE001
        monitoring_error_handler.report('disk partitions enumeration failed', exc=exc)

    io = None
    try:
        counters = psutil.disk_io_counters()
        if counters is not None:
            io = {
                'read_bytes': counters.read_bytes,
                'write_bytes': counters.write_bytes,
                'read_count': counters.read_count,
                'write_count': counters.write_count,
            }
    except Exception as exc:  # noqa: BLE001
        monitoring_error_handler.report('disk io collector failed', exc=exc)

    return {'partitions': partitions, 'io': io}
