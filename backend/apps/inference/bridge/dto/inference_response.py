"""Inference response DTO (Bridge abstraction-side)."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Detection:
    """One bounding-box detection returned by a provider."""

    class_id: int
    class_name: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]  # (x1, y1, x2, y2)


@dataclass
class InferenceResponse:
    """Provider-agnostic result the API layer serialises and returns."""

    detections: list[Detection] = field(default_factory=list)
    masked_image_base64: Optional[str] = None  # JPEG base64, red defect overlay
    inference_time_ms: float = 0.0
    model_name: str = ''
    provider_name: str = ''

    # Defect-area summary (computed via chip bbox + physical reference)
    defect_detected: bool = False
    chip_detected: bool = False
    defect_area_mm2: float = 0.0
    defect_percentage: float = 0.0
    chip_pixel_area: float = 0.0
    defect_pixel_area: float = 0.0

    # Provider extras (raw scores, debug data, etc.)
    confidence_scores: list[float] = field(default_factory=list)
