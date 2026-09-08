"""Application-layer orchestrator for a single inference request.

This sits BETWEEN the DRF view and the bridge facade — it's the only place
that knows about HTTP, the DB mirror, JSONL persistence, and MQTT publishing.
The view stays thin (just (de)serialisation); the bridge stays engine-only.
"""
from typing import Any, Optional

from django.conf import settings

from apps.inference.bridge.dto.inference_request import InferenceRequest
from apps.inference.bridge.services.inference_bridge import run_inference
from apps.inference.models import InferenceRun
from apps.inference.services import mqtt_service, persistence_service
from apps.inference.services.threshold_service import resolve_threshold
from apps.inference.utils.base64_encoder import to_data_url
from apps.inference.utils.image_utils import read_upload_bytes
from apps.inference.utils.validation import validate_image_upload
from core.errors import backend_error_handler


def execute_inference(
    *,
    uploaded_image,
    user,
    model_hint: Optional[str] = None,
    confidence_threshold: Optional[float] = None,
    line_id: Optional[str] = None,
    station_id: Optional[str] = None,
) -> dict[str, Any]:
    """End-to-end inference flow used by the DRF view."""
    validate_image_upload(uploaded_image)

    request = InferenceRequest(
        image_bytes=read_upload_bytes(uploaded_image),
        image_filename=getattr(uploaded_image, 'name', 'upload.bin'),
        content_type=getattr(uploaded_image, 'content_type', 'application/octet-stream'),
        model_hint=model_hint,
        confidence_threshold=resolve_threshold(confidence_threshold),
        line_id=line_id or settings.INFERENCE['DEFAULT_LINE_ID'],
        station_id=station_id or settings.INFERENCE['DEFAULT_STATION_ID'],
    )

    response = run_inference(request)

    # Side effects: persist to JSONL, mirror to DB, publish to MQTT.
    try:
        persistence_service.record_inference(request, response)
    except Exception as exc:  # noqa: BLE001
        backend_error_handler.report('JSONL persistence failed', exc=exc)

    try:
        InferenceRun.objects.create(
            user=user if getattr(user, 'is_authenticated', False) else None,
            model_name=response.model_name,
            provider_name=response.provider_name,
            line_id=request.line_id,
            station_id=request.station_id,
            confidence_threshold=request.confidence_threshold,
            inference_time_ms=response.inference_time_ms,
            chip_detected=response.chip_detected,
            defect_detected=response.defect_detected,
            defect_area_mm2=response.defect_area_mm2,
            defect_percentage=response.defect_percentage,
        )
    except Exception as exc:  # noqa: BLE001
        backend_error_handler.report('InferenceRun DB write failed', exc=exc)

    try:
        mqtt_service.publish_inference(request, response)
    except Exception as exc:  # noqa: BLE001
        backend_error_handler.report('MQTT inference publish failed', exc=exc)

    output_image_data_url = (
        to_data_url(response.masked_image_base64) if response.masked_image_base64 else None
    )

    return {
        'model_name': response.model_name,
        'provider_name': response.provider_name,
        'inference_time_ms': round(response.inference_time_ms, 2),
        'confidence_threshold': request.confidence_threshold,
        'chip_detected': response.chip_detected,
        'defect_detected': response.defect_detected,
        'defect_area_mm2': response.defect_area_mm2,
        'defect_percentage': response.defect_percentage,
        'confidence_scores': response.confidence_scores,
        'detections': [
            {
                'class_id': d.class_id,
                'class_name': d.class_name,
                'confidence': d.confidence,
                'bbox_xyxy': list(d.bbox_xyxy),
            }
            for d in response.detections
        ],
        'output_image': output_image_data_url,
    }
