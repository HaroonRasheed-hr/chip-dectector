"""In-memory queue of MQTT messages held while the broker is unreachable.

Drained by :class:`core.mqtt.mqtt_client.MQTTClient` on reconnect.
"""
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class QueuedMessage:
    topic: str
    payload: str           # serialized JSON sent over the wire
    qos: int
    retain: bool
    # Original Python object kept alongside so the result logger can
    # record structured payloads (and not the raw JSON string) for both
    # immediate and replayed publishes. Not serialised — purely
    # in-memory metadata.
    payload_obj: Any = field(default=None, repr=False, compare=False)


class MessageQueue:
    """Thread-safe bounded FIFO of pending MQTT publishes."""

    def __init__(self, maxlen: int = 1000) -> None:
        self._buffer: deque[QueuedMessage] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def enqueue(self, message: QueuedMessage) -> None:
        with self._lock:
            self._buffer.append(message)

    def dequeue(self) -> Optional[QueuedMessage]:
        with self._lock:
            if not self._buffer:
                return None
            return self._buffer.popleft()

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)

    def is_empty(self) -> bool:
        return len(self) == 0
