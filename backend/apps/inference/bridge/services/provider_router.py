"""Provider selection + lifecycle (Bridge implementation-side).

Knows the registered providers, picks one per request (or falls back to the
default), and keeps each provider loaded between calls so the model is only
initialised once.
"""
from typing import Optional

from django.conf import settings

from apps.inference.bridge.interfaces.ai_provider import AIProvider
from apps.inference.bridge.providers.future_provider import StubProvider
from apps.inference.bridge.providers.rf_detr_provider import RfDetrProvider
from apps.inference.bridge.providers.tensorrt_provider import TensorRTProvider
from core.errors import inference_error_handler
from core.logging_system.inference_logger import info as log_inference


class ProviderRouter:
    """Lazy-loading registry of AIProvider instances keyed by name."""

    def __init__(self) -> None:
        self._registry: dict[str, AIProvider] = {
            'stub': StubProvider(),
            'rf_detr': RfDetrProvider(),
            'tensorrt': TensorRTProvider(),
        }
        self._loaded: set[str] = set()

    def resolve(self, requested: Optional[str] = None) -> AIProvider:
        name = requested or settings.INFERENCE.get('DEFAULT_PROVIDER', 'stub')
        provider = self._registry.get(name)
        if provider is None:
            inference_error_handler.report(
                f'unknown inference provider "{name}" — falling back to stub',
            )
            provider = self._registry['stub']

        if provider.name not in self._loaded:
            try:
                provider.load()
                self._loaded.add(provider.name)
                log_inference('Loaded inference provider: %s', provider.name)
            except Exception as exc:  # noqa: BLE001
                inference_error_handler.report(
                    f'provider "{provider.name}" failed to load', exc=exc,
                )
                raise

        return provider

    def shutdown_all(self) -> None:
        for name in list(self._loaded):
            try:
                self._registry[name].shutdown()
            except Exception as exc:  # noqa: BLE001
                inference_error_handler.report(
                    f'provider "{name}" shutdown failed', exc=exc,
                )
        self._loaded.clear()


# ── module-level singleton ───────────────────────────────────────────────────
_router: Optional[ProviderRouter] = None


def get_router() -> ProviderRouter:
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router
