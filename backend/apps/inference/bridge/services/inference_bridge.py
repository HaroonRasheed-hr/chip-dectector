"""Bridge facade — single entry point the API layer (and only the API layer) calls.

Per spec A.4.1, the frontend / DRF view must NOT import a provider directly.
They build an :class:`InferenceRequest`, hand it to :func:`run_inference`, and
get an :class:`InferenceResponse` back — engine-agnostic from end to end.
"""
from django.conf import settings

from apps.inference.bridge.dto.inference_request import InferenceRequest
from apps.inference.bridge.dto.inference_response import InferenceResponse
from apps.inference.bridge.services.image_processor import annotate_response_with_defect_area
from apps.inference.bridge.services.provider_router import get_router
from core.errors import inference_error_handler
from core.logging_system.inference_logger import info as log_inference


def run_inference(request: InferenceRequest) -> InferenceResponse:
    """Resolve a provider, run inference, annotate defect area, return the response."""
    router = get_router()
    provider = router.resolve(request.model_hint)

    try:
        response = provider.infer(request)
    except Exception as exc:  # noqa: BLE001
        inference_error_handler.report(
            f'inference failed (provider={provider.name})',
            exc=exc,
            context={'station_id': request.station_id, 'line_id': request.line_id},
        )
        raise

    annotate_response_with_defect_area(
        response,
        chip_physical_area_mm2=settings.INFERENCE['CHIP_PHYSICAL_AREA_MM2'],
    )

    log_inference(
        'Inference ok provider=%s time_ms=%.2f defect=%s pct=%.2f',
        response.provider_name,
        response.inference_time_ms,
        response.defect_detected,
        response.defect_percentage,
    )
    return response
