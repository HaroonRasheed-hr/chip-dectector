"""Database models for the inference app.

Stores a row per inference run for admin browsing & audit. The authoritative
measurement store remains ``measurements.jsonl`` (spec A.4.3); this table is a
convenience mirror tied to the user who triggered the run.
"""
from django.conf import settings
from django.db import models


class InferenceRun(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inference_runs',
    )
    model_name = models.CharField(max_length=128)
    provider_name = models.CharField(max_length=64)
    line_id = models.CharField(max_length=64, default='line-1')
    station_id = models.CharField(max_length=64, default='station-1')

    confidence_threshold = models.FloatField(default=0.5)
    inference_time_ms = models.FloatField(default=0.0)

    chip_detected = models.BooleanField(default=False)
    defect_detected = models.BooleanField(default=False)
    defect_area_mm2 = models.FloatField(default=0.0)
    defect_percentage = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inference_runs'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'{self.model_name} @ {self.created_at:%Y-%m-%d %H:%M:%S} ({self.defect_percentage:.2f}%)'
