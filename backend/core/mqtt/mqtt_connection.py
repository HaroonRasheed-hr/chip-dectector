"""Public entry points for managing the global MQTT connection lifecycle."""
from core.mqtt.mqtt_client import get_mqtt_client


def start_mqtt() -> None:
    """Start the singleton MQTT client (idempotent)."""
    get_mqtt_client().start()


def stop_mqtt() -> None:
    """Stop the singleton MQTT client (idempotent)."""
    get_mqtt_client().stop()


def publish_json(topic: str, payload: dict, qos: int | None = None, retain: bool = False) -> bool:
    """Convenience shortcut for callers that don't need a client reference."""
    return get_mqtt_client().publish_json(topic, payload, qos=qos, retain=retain)
