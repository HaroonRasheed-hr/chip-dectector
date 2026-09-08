"""Lifecycle status publisher (spec A.4.2 → ``visionpulse/system/status``)."""
from core.mqtt.mqtt_connection import publish_json
from core.mqtt.topics import SYSTEM_STATUS
from core.persistence.jsonl_writer import utc_iso_timestamp


def publish_status(event: str, **details) -> None:
    """Publish a lifecycle event — e.g. ``startup`` / ``shutdown`` / ``heartbeat``."""
    publish_json(SYSTEM_STATUS, {
        'timestamp': utc_iso_timestamp(),
        'event': event,
        **details,
    })
