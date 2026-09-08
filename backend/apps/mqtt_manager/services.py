"""High-level MQTT service used by the app's ready() hook."""
from apps.mqtt_manager.publishers.status_publisher import publish_status
from apps.mqtt_manager.subscribers.command_subscriber import subscribe_to_commands
from core.mqtt.mqtt_connection import start_mqtt, stop_mqtt


def start_mqtt_subsystem() -> None:
    """Bring up MQTT: connect, subscribe to commands, announce startup."""
    start_mqtt()
    subscribe_to_commands()
    publish_status('startup')


def stop_mqtt_subsystem() -> None:
    publish_status('shutdown')
    stop_mqtt()
