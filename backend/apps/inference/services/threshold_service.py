"""Confidence-threshold + defect-severity helpers (spec A.3.4 + B.5.3)."""
from typing import Optional

from django.conf import settings


def resolve_threshold(requested: Optional[float]) -> float:
    """Clamp a requested threshold to [0, 1], falling back to the configured default."""
    if requested is None:
        return float(settings.INFERENCE['DEFAULT_CONFIDENCE_THRESHOLD'])
    try:
        value = float(requested)
    except (TypeError, ValueError):
        return float(settings.INFERENCE['DEFAULT_CONFIDENCE_THRESHOLD'])
    return max(0.0, min(1.0, value))


def severity_for_defect_pct(defect_pct: float) -> str:
    """Map a defect-percentage to the severity bands defined in spec B.5.3."""
    if defect_pct <= 2.0:
        return 'none'
    if defect_pct <= 5.0:
        return 'low'
    if defect_pct <= 10.0:
        return 'medium'
    return 'high'
