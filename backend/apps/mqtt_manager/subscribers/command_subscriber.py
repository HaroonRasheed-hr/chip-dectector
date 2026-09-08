"""Subscribes to inbound MQTT command topics (spec B.5.1).

Inbound topic: ``ic_inspection/command/{station_id}``
Supported commands (JSON body):
  - ``{"action": "start"}``
  - ``{"action": "stop"}``
  - ``{"action": "set_threshold", "value": 0.6}``

Wired into the MQTT client during app startup (see
:class:`apps.mqtt_manager.apps.MqttManagerConfig`).
"""
import json
from typing import Optional

from django.conf import settings

from core.errors import mqtt_error_handler
from core.logging_system import mqtt_result_logger
from core.logging_system.mqtt_logger import info as log_runtime
from core.mqtt.mqtt_client import get_mqtt_client
from core.mqtt.topics import ic_inspection_command


def subscribe_to_commands(station_id: Optional[str] = None) -> None:
    """Subscribe and register the command handler with the MQTT client."""
    client = get_mqtt_client()
    if not client.enabled:
        return
    target_station = station_id or settings.INFERENCE['DEFAULT_STATION_ID']
    topic = ic_inspection_command(target_station)
    client.set_command_handler(_handle_command)
    client.subscribe(topic)
    log_runtime('Subscribed to command topic: %s', topic)


def _handle_command(topic: str, payload: str) -> None:
    try:
        message = json.loads(payload)
    except (TypeError, ValueError) as exc:
        mqtt_error_handler.report('command payload not JSON', exc=exc, context={'topic': topic})
        mqtt_result_logger.log_error(
            f'command payload not JSON: {exc!r}',
            topic=topic,
            raw_payload=payload,
        )
        return

    action = (message or {}).get('action')
    if action == 'start':
        log_runtime('Command received: start (topic=%s)', topic)
    elif action == 'stop':
        log_runtime('Command received: stop (topic=%s)', topic)
    elif action == 'set_threshold':
        log_runtime('Command received: set_threshold=%s (topic=%s)', message.get('value'), topic)
    else:
        mqtt_error_handler.report(
            f'unknown command action: {action!r}',
            context={'topic': topic, 'payload': message},
        )
        mqtt_result_logger.log_error(
            f'unknown command action: {action!r}',
            topic=topic,
            payload=message,
        )
