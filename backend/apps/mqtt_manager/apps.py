"""MQTT manager app config — boots the MQTT client when the server starts."""
from django.apps import AppConfig


class MqttManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mqtt_manager'
    label = 'mqtt_manager'

    def ready(self) -> None:
        from apps.mqtt_manager.services import start_mqtt_subsystem

        start_mqtt_subsystem()
