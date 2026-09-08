"""One-shot monitor publisher.

The recurring monitoring publish loop lives in
:mod:`core.monitoring.scheduler`; this helper covers ad-hoc snapshots.
"""
from core.monitoring.telemetry import collect_snapshot
from core.mqtt.mqtt_connection import publish_json
from core.mqtt.topics import SYSTEM_MONITOR


def publish_now() -> None:
    publish_json(SYSTEM_MONITOR, collect_snapshot())
