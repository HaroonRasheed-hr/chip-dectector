"""Thin re-export of the bridge-layer area math (kept for spec parity)."""
from apps.inference.bridge.services.image_processor import (
    annotate_response_with_defect_area,
    bbox_pixel_area,
    pick_chip_detection,
)

__all__ = ['annotate_response_with_defect_area', 'bbox_pixel_area', 'pick_chip_detection']
