"""Exponential-backoff delay computation for MQTT reconnect attempts (spec A.4.2)."""


class ExponentialBackoff:
    """Doubling backoff capped at ``max_delay`` seconds."""

    def __init__(self, min_delay: int = 1, max_delay: int = 60) -> None:
        self._min = max(1, int(min_delay))
        self._max = max(self._min, int(max_delay))
        self._current = self._min

    def next_delay(self) -> int:
        delay = self._current
        self._current = min(self._max, self._current * 2)
        return delay

    def reset(self) -> None:
        self._current = self._min
