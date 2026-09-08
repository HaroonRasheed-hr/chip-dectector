"""Pixel-area + mm² conversion utilities shared by every provider (spec B.3)."""
from typing import Optional

from apps.inference.bridge.dto.inference_response import Detection, InferenceResponse


CHIP_CLASS_ID = 0
DEFECT_CLASS_ID = 1


def bbox_pixel_area(bbox: tuple[float, float, float, float]) -> float:
    x1, y1, x2, y2 = bbox
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def pick_chip_detection(detections: list[Detection]) -> Optional[Detection]:
    chips = [d for d in detections if d.class_id == CHIP_CLASS_ID]
    if not chips:
        return None
    return max(chips, key=lambda d: d.confidence)


def annotate_response_with_defect_area(
    response: InferenceResponse,
    *,
    chip_physical_area_mm2: float,
) -> InferenceResponse:
    """Populate defect-area fields on ``response`` using the chip bbox as scale."""
    chip = pick_chip_detection(response.detections)
    if chip is None:
        response.chip_detected = False
        response.defect_detected = any(d.class_id == DEFECT_CLASS_ID for d in response.detections)
        return response

    chip_pixel_area = bbox_pixel_area(chip.bbox_xyxy)
    if chip_pixel_area <= 0:
        return response

    defect_pixel_area = sum(
        bbox_pixel_area(d.bbox_xyxy) for d in response.detections if d.class_id == DEFECT_CLASS_ID
    )

    response.chip_detected = True
    response.defect_detected = defect_pixel_area > 0
    response.chip_pixel_area = chip_pixel_area
    response.defect_pixel_area = defect_pixel_area
    response.defect_area_mm2 = round((defect_pixel_area / chip_pixel_area) * chip_physical_area_mm2, 2)
    response.defect_percentage = round((response.defect_area_mm2 / chip_physical_area_mm2) * 100.0, 2)
    return response
