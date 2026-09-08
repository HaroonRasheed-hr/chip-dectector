"""Persist an :class:`InferenceResponse` to ``measurements.jsonl`` (spec A.4.3)."""
from apps.inference.bridge.dto.inference_request import InferenceRequest
from apps.inference.bridge.dto.inference_response import InferenceResponse
from core.persistence.persistence_manager import persist_measurement


def record_inference(request: InferenceRequest, response: InferenceResponse) -> bool:
    """Append a one-line JSON measurement record. Returns success flag."""
    payload = {
        'model': response.model_name or request.model_hint or 'unknown',
        'provider': response.provider_name,
        'line_id': request.line_id,
        'station_id': request.station_id,
        'confidence_threshold': request.confidence_threshold,
        'inference_time_ms': round(response.inference_time_ms, 2),
        'chip_detected': response.chip_detected,
        'defect_detected': response.defect_detected,
        'defect_area_mm2': response.defect_area_mm2,
        'defect_percentage': response.defect_percentage,
        'confidence_scores': response.confidence_scores,
    }
    return persist_measurement(payload)
