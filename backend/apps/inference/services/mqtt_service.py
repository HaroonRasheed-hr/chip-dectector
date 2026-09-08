"""Publish inference results + alerts to the right MQTT topics."""
from typing import Any

from apps.inference.bridge.dto.inference_request import InferenceRequest
from apps.inference.bridge.dto.inference_response import InferenceResponse
from apps.inference.services.threshold_service import severity_for_defect_pct
from core.mqtt.mqtt_connection import publish_json
from core.mqtt.topics import (
    INFERENCE_RESULTS,
    ic_inspection_alert,
    ic_inspection_defect_area,
    ic_inspection_result,
)
from core.persistence.jsonl_writer import utc_iso_timestamp


def publish_inference(request: InferenceRequest, response: InferenceResponse) -> None:
    """Publish all required MQTT messages for one inference run.

    Per spec B.3 — if no ic_chip bbox was detected, the result is invalid and
    must NOT hit the result topic. We still publish a defect_area (with zero
    values) so monitoring consumers see the event.
    """
    timestamp = utc_iso_timestamp()
    line, station = request.line_id, request.station_id

    result_payload: dict[str, Any] = {
        'timestamp': timestamp,
        'station_id': station,
        'line_id': line,
        'image_base64': response.masked_image_base64 or '',
        'defect_detected': response.defect_detected,
        'defect_area_mm2': response.defect_area_mm2,
        'defect_percentage': response.defect_percentage,
        'confidence_scores': response.confidence_scores,
        'inference_time_ms': round(response.inference_time_ms, 2),
        'model_name': response.model_name,
        'provider': response.provider_name,
    }

    # Full-stack mirror topic (spec A.4.2)
    publish_json(INFERENCE_RESULTS, result_payload)

    # AI-pipeline topics (spec B.5.1) — skip the result topic if no chip detected
    if response.chip_detected:
        publish_json(ic_inspection_result(line, station), result_payload)

    publish_json(ic_inspection_defect_area(line, station), {
        'timestamp': timestamp,
        'defect_area_mm2': response.defect_area_mm2,
        'defect_percentage': response.defect_percentage,
    })

    severity = severity_for_defect_pct(response.defect_percentage)
    if severity != 'none':
        publish_json(ic_inspection_alert(line, station), {
            'timestamp': timestamp,
            'station_id': station,
            'line_id': line,
            'severity': severity,
            'defect_percentage': response.defect_percentage,
            'defect_area_mm2': response.defect_area_mm2,
        })
