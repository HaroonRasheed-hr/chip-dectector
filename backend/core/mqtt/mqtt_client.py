"""MQTT client wrapper over paho-mqtt with auto-reconnect and offline queue.

Spec A.4.2:
  - Automatic reconnect with exponential backoff
  - In-flight messages queued while disconnected and replayed on reconnect
  - Connection failures logged, never silently swallowed
"""
import json
import threading
import time
from typing import Any, Callable, Optional

import paho.mqtt.client as paho

from core.logging_system import mqtt_result_logger
from core.logging_system.mqtt_logger import (
    error as log_error,
    info as log_runtime,
    warning as log_warning,
)
from core.mqtt.queue_manager import MessageQueue, QueuedMessage
from core.mqtt.reconnect_handler import ExponentialBackoff


class MQTTClient:
    """Singleton-style wrapper around a paho ``Client``.

    Use :meth:`start` once at app startup, :meth:`publish_json` from anywhere,
    and :meth:`stop` at shutdown. Safe to call when MQTT is disabled — every
    method becomes a no-op so callers don't need to branch.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._enabled = bool(config.get('ENABLED'))
        self._client: Optional[paho.Client] = None
        self._connected = False
        self._stop_event = threading.Event()
        self._reconnect_thread: Optional[threading.Thread] = None
        self._queue = MessageQueue()
        self._backoff = ExponentialBackoff(
            min_delay=config.get('RECONNECT_MIN_DELAY', 1),
            max_delay=config.get('RECONNECT_MAX_DELAY', 60),
        )
        self._command_handler: Optional[Callable[[str, str], None]] = None

    # ── lifecycle ────────────────────────────────────────────────────────────
    def start(self) -> None:
        if not self._enabled:
            log_runtime('MQTT disabled — client not started')
            mqtt_result_logger.log_connection('disabled')
            return
        if self._client is not None:
            return

        client_id = self._config.get('CLIENT_ID') or 'visionpulse-backend'
        self._client = paho.Client(
            client_id=client_id,
            callback_api_version=paho.CallbackAPIVersion.VERSION2,
        )
        username = self._config.get('USERNAME') or ''
        password = self._config.get('PASSWORD') or ''
        if username:
            self._client.username_pw_set(username, password or None)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        self._reconnect_thread = threading.Thread(
            target=self._connect_loop,
            name='mqtt-reconnect',
            daemon=True,
        )
        self._reconnect_thread.start()
        log_runtime(
            'MQTT client starting (host=%s port=%s)',
            self._config.get('HOST'),
            self._config.get('PORT'),
        )
        mqtt_result_logger.log_connection(
            'starting',
            host=self._config.get('HOST'),
            port=self._config.get('PORT'),
            client_id=client_id,
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._client is not None:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:  # noqa: BLE001 — best-effort shutdown
                pass
            self._client = None
            self._connected = False
            log_runtime('MQTT client stopped')
            mqtt_result_logger.log_connection('stopped')

    # ── publish ──────────────────────────────────────────────────────────────
    def publish_json(
        self,
        topic: str,
        payload: dict[str, Any],
        qos: Optional[int] = None,
        retain: bool = False,
    ) -> bool:
        """Serialize ``payload`` as JSON and publish (or queue) it.

        Returns ``True`` if the publish succeeded immediately, ``False`` if
        MQTT is disabled or the message was queued for later delivery.
        """
        if not self._enabled:
            return False
        effective_qos = self._config.get('QOS', 1) if qos is None else qos
        try:
            serialized = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            log_error('MQTT publish skipped — payload not JSON-serialisable (topic=%s)', topic)
            mqtt_result_logger.log_publish(
                topic,
                repr(payload),
                'failed',
                qos=effective_qos,
                retain=retain,
                error=f'payload not JSON-serialisable: {exc!r}',
            )
            return False

        message = QueuedMessage(
            topic=topic,
            payload=serialized,
            qos=effective_qos,
            retain=retain,
            payload_obj=payload,
        )

        if not self._connected or self._client is None:
            self._queue.enqueue(message)
            depth = len(self._queue)
            log_warning('MQTT not connected — queued message for %s (queue=%d)', topic, depth)
            mqtt_result_logger.log_publish(
                topic,
                payload,
                'queued',
                qos=effective_qos,
                retain=retain,
                queue_depth=depth,
            )
            return False

        return self._publish_direct(message)

    def _publish_direct(self, message: QueuedMessage) -> bool:
        # Prefer the original Python object for the result log; fall back
        # to the wire payload (string) for replayed messages whose dict
        # is no longer in memory.
        loggable_payload = (
            message.payload_obj if message.payload_obj is not None else message.payload
        )
        try:
            result = self._client.publish(
                message.topic, message.payload, qos=message.qos, retain=message.retain
            )
            if result.rc != paho.MQTT_ERR_SUCCESS:
                log_error('MQTT publish failed rc=%s topic=%s', result.rc, message.topic)
                mqtt_result_logger.log_publish(
                    message.topic,
                    loggable_payload,
                    'failed',
                    qos=message.qos,
                    retain=message.retain,
                    error=f'paho rc={result.rc}',
                )
                self._queue.enqueue(message)
                return False
            mqtt_result_logger.log_publish(
                message.topic,
                loggable_payload,
                'ok',
                qos=message.qos,
                retain=message.retain,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            log_error('MQTT publish exception topic=%s err=%r', message.topic, exc)
            mqtt_result_logger.log_publish(
                message.topic,
                loggable_payload,
                'failed',
                qos=message.qos,
                retain=message.retain,
                error=repr(exc),
            )
            self._queue.enqueue(message)
            return False

    # ── subscribe ────────────────────────────────────────────────────────────
    def subscribe(self, topic: str, qos: Optional[int] = None) -> None:
        if not self._enabled or self._client is None:
            return
        effective_qos = self._config.get('QOS', 1) if qos is None else qos
        try:
            self._client.subscribe(topic, qos=effective_qos)
            mqtt_result_logger.log_connection(
                'subscribed', topic=topic, qos=effective_qos,
            )
        except Exception as exc:  # noqa: BLE001
            log_error('MQTT subscribe failed topic=%s err=%r', topic, exc)
            mqtt_result_logger.log_error(
                f'subscribe failed: {exc!r}', topic=topic, qos=effective_qos,
            )

    def set_command_handler(self, handler: Callable[[str, str], None]) -> None:
        self._command_handler = handler

    # ── connection loop ─────────────────────────────────────────────────────
    def _connect_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._client.connect(
                    host=self._config.get('HOST', 'localhost'),
                    port=int(self._config.get('PORT', 1883)),
                    keepalive=int(self._config.get('KEEPALIVE', 60)),
                )
                self._client.loop_start()
                return  # paho handles reconnect via on_disconnect; exit loop
            except Exception as exc:  # noqa: BLE001
                delay = self._backoff.next_delay()
                log_error(
                    'MQTT connect failed (host=%s port=%s err=%r) — retrying in %ds',
                    self._config.get('HOST'),
                    self._config.get('PORT'),
                    exc,
                    delay,
                )
                mqtt_result_logger.log_connection(
                    'connect_failed',
                    host=self._config.get('HOST'),
                    port=self._config.get('PORT'),
                    error=repr(exc),
                    retry_in_seconds=delay,
                )
                self._stop_event.wait(delay)

    # ── paho callbacks ──────────────────────────────────────────────────────
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):  # noqa: D401
        if reason_code == 0 or getattr(reason_code, 'value', 1) == 0:
            self._connected = True
            self._backoff.reset()
            log_runtime('MQTT connected to broker')
            mqtt_result_logger.log_connection(
                'connected',
                host=self._config.get('HOST'),
                port=self._config.get('PORT'),
            )
            self._drain_queue()
        else:
            log_error('MQTT connect refused reason_code=%s', reason_code)
            mqtt_result_logger.log_connection(
                'connect_refused', reason_code=str(reason_code),
            )

    def _on_disconnect(self, client, userdata, *args, **kwargs):  # noqa: D401
        self._connected = False
        log_warning('MQTT disconnected — will auto-reconnect')
        mqtt_result_logger.log_connection('disconnected')

    def _on_message(self, client, userdata, msg):  # noqa: D401
        raw = msg.payload.decode('utf-8', errors='replace')
        # Best-effort decode for the structured log — fall back to the
        # raw string if the payload isn't JSON.
        try:
            decoded: Any = json.loads(raw)
        except (TypeError, ValueError):
            decoded = raw
        mqtt_result_logger.log_receive(msg.topic, decoded)

        if self._command_handler is None:
            return
        try:
            self._command_handler(msg.topic, raw)
        except Exception as exc:  # noqa: BLE001
            log_error('MQTT command handler raised topic=%s err=%r', msg.topic, exc)
            mqtt_result_logger.log_error(
                f'command handler raised: {exc!r}', topic=msg.topic,
            )

    def _drain_queue(self) -> None:
        delivered = 0
        while True:
            msg = self._queue.dequeue()
            if msg is None:
                break
            if self._publish_direct(msg):
                delivered += 1
            else:
                break  # re-queued; stop draining until next reconnect
        if delivered:
            log_runtime('Replayed %d queued MQTT messages', delivered)

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def enabled(self) -> bool:
        return self._enabled


# ── module-level singleton ───────────────────────────────────────────────────
_client_singleton: Optional[MQTTClient] = None


def get_mqtt_client() -> MQTTClient:
    global _client_singleton
    if _client_singleton is None:
        from django.conf import settings
        _client_singleton = MQTTClient(settings.MQTT)
    return _client_singleton
