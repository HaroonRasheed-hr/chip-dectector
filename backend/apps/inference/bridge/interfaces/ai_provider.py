"""Bridge abstraction — every concrete AI engine implements this interface.

Per spec A.4.1 the API layer never imports a provider directly; it routes
through :class:`AIProvider` so the engine can be swapped without touching
the frontend or the views layer.
"""
from abc import ABC, abstractmethod

from apps.inference.bridge.dto.inference_request import InferenceRequest
from apps.inference.bridge.dto.inference_response import InferenceResponse


class AIProvider(ABC):
    """Stable contract for any inference engine plugged into the bridge."""

    name: str = 'abstract'
    model_name: str = ''

    @abstractmethod
    def load(self) -> None:
        """Initialize the engine. Called once at startup (or first request)."""

    @abstractmethod
    def is_ready(self) -> bool:
        """True once :meth:`load` has succeeded and the engine can serve requests."""

    @abstractmethod
    def infer(self, request: InferenceRequest) -> InferenceResponse:
        """Run inference on a single image and return a provider-agnostic response."""

    def shutdown(self) -> None:  # noqa: D401 — optional hook
        """Release any model/GPU resources. Default no-op."""
        return None
