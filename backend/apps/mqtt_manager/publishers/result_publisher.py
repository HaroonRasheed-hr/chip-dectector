"""Inference-result publisher (alias for :mod:`apps.inference.services.mqtt_service`).

Kept here so the spec's ``mqtt_manager.publishers.result_publisher`` path
resolves to a real module if external callers reference it.
"""
from apps.inference.services.mqtt_service import publish_inference as publish_result  # noqa: F401
