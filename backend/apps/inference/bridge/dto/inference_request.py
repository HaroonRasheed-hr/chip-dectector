"""Inference request DTO (Bridge abstraction-side)."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class InferenceRequest:
    """Plain-data request handed from the API layer to the provider router."""

    image_bytes: bytes
    image_filename: str
    content_type: str
    model_hint: Optional[str] = None
    confidence_threshold: float = 0.5
    line_id: str = 'line-1'
    station_id: str = 'station-1'
