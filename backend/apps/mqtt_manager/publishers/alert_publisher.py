"""Alert publisher (spec B.5.3 — defect-percentage threshold breaches)."""
from core.mqtt.mqtt_connection import publish_json
from core.mqtt.topics import ic_inspection_alert
from core.persistence.jsonl_writer import utc_iso_timestamp


def publish_alert(line_id: str, station_id: str, severity: str, **details) -> None:
    publish_json(ic_inspection_alert(line_id, station_id), {
        'timestamp': utc_iso_timestamp(),
        'line_id': line_id,
        'station_id': station_id,
        'severity': severity,
        **details,
    })
