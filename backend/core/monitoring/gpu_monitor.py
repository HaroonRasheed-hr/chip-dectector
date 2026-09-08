"""GPU utilization + VRAM collector via NVML — spec A.5.

Gracefully degrades when no NVIDIA driver/GPU is available so the rest of the
monitoring pipeline keeps running.
"""
from typing import Any

from core.errors import monitoring_error_handler

try:
    import pynvml  # type: ignore[import-not-found]
    _NVML_AVAILABLE = True
except ImportError:
    _NVML_AVAILABLE = False

_NVML_INITIALIZED = False


def _ensure_initialized() -> bool:
    global _NVML_INITIALIZED
    if not _NVML_AVAILABLE:
        return False
    if _NVML_INITIALIZED:
        return True
    try:
        pynvml.nvmlInit()
        _NVML_INITIALIZED = True
        return True
    except Exception:  # noqa: BLE001 — no GPU / driver missing
        return False


def collect() -> dict[str, Any]:
    if not _ensure_initialized():
        return {'available': False, 'devices': []}

    devices: list[dict[str, Any]] = []
    try:
        count = pynvml.nvmlDeviceGetCount()
        for i in range(count):
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8', errors='replace')
                devices.append({
                    'index': i,
                    'name': name,
                    'gpu_utilization_percent': util.gpu,
                    'memory_utilization_percent': util.memory,
                    'memory_total': mem.total,
                    'memory_used': mem.used,
                    'memory_free': mem.free,
                })
            except Exception as exc:  # noqa: BLE001
                monitoring_error_handler.report(f'gpu device {i} read failed', exc=exc)
    except Exception as exc:  # noqa: BLE001
        monitoring_error_handler.report('gpu collector failed', exc=exc)
        return {'available': False, 'devices': []}

    return {'available': True, 'devices': devices}
