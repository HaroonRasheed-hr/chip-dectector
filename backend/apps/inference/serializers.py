"""Request/response serializers for the inference endpoints."""
from rest_framework import serializers


class InferenceRequestSerializer(serializers.Serializer):
    """Multipart payload for ``POST /api/inference/infer/``."""

    image = serializers.ImageField()
    model = serializers.CharField(required=False, allow_blank=True, max_length=128)
    confidence_threshold = serializers.FloatField(required=False, min_value=0.0, max_value=1.0)
    line_id = serializers.CharField(required=False, allow_blank=True, max_length=64)
    station_id = serializers.CharField(required=False, allow_blank=True, max_length=64)


class DetectionSerializer(serializers.Serializer):
    class_id = serializers.IntegerField()
    class_name = serializers.CharField()
    confidence = serializers.FloatField()
    bbox_xyxy = serializers.ListField(child=serializers.FloatField(), min_length=4, max_length=4)


class InferenceResponseSerializer(serializers.Serializer):
    model_name = serializers.CharField()
    provider_name = serializers.CharField()
    inference_time_ms = serializers.FloatField()
    confidence_threshold = serializers.FloatField()
    chip_detected = serializers.BooleanField()
    defect_detected = serializers.BooleanField()
    defect_area_mm2 = serializers.FloatField()
    defect_percentage = serializers.FloatField()
    confidence_scores = serializers.ListField(child=serializers.FloatField())
    detections = DetectionSerializer(many=True)
    output_image = serializers.CharField(allow_null=True)
