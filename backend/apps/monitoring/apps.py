"""Monitoring app config — starts the telemetry scheduler when the server boots."""
from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitoring'
    label = 'monitoring'

    def ready(self) -> None:
        from core.monitoring.scheduler import get_scheduler

        get_scheduler().start()
