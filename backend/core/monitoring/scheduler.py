"""Background scheduler that publishes telemetry to MQTT on a fixed interval.

Runs in a daemon thread so it never blocks Django's shutdown path.
Interval is governed by ``settings.MONITORING['INTERVAL_SECONDS']`` (default 5s).
"""
import threading
from typing import Optional

from django.conf import settings

from core.errors import monitoring_error_handler
from core.logging_system.runtime_logger import info as log_runtime
from core.monitoring.telemetry import collect_snapshot
from core.mqtt.mqtt_connection import publish_json
from core.mqtt.topics import SYSTEM_MONITOR


class MonitoringScheduler:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        cfg = settings.MONITORING
        if not cfg.get('ENABLED'):
            log_runtime('Monitoring scheduler disabled')
            return
        if self._thread is not None and self._thread.is_alive():
            return

        interval = max(1, int(cfg.get('INTERVAL_SECONDS', 5)))
        publish = bool(cfg.get('PUBLISH_TO_MQTT', True))
        self._thread = threading.Thread(
            target=self._run,
            args=(interval, publish),
            name='monitoring-scheduler',
            daemon=True,
        )
        self._thread.start()
        log_runtime('Monitoring scheduler started (interval=%ds, publish=%s)', interval, publish)

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self, interval: int, publish: bool) -> None:
        while not self._stop_event.is_set():
            try:
                snapshot = collect_snapshot()
                if publish:
                    publish_json(SYSTEM_MONITOR, snapshot)
            except Exception as exc:  # noqa: BLE001
                monitoring_error_handler.report('scheduler tick failed', exc=exc)
            self._stop_event.wait(interval)


# ── module-level singleton ───────────────────────────────────────────────────
_scheduler: Optional[MonitoringScheduler] = None


def get_scheduler() -> MonitoringScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = MonitoringScheduler()
    return _scheduler
