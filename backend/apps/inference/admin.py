from django.contrib import admin

from apps.inference.models import InferenceRun


@admin.register(InferenceRun)
class InferenceRunAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'created_at', 'user', 'model_name', 'provider_name',
        'station_id', 'defect_detected', 'defect_percentage', 'inference_time_ms',
    )
    list_filter = ('provider_name', 'model_name', 'defect_detected', 'station_id')
    search_fields = ('model_name', 'station_id', 'line_id', 'user__email')
    readonly_fields = tuple(f.name for f in InferenceRun._meta.fields)
    ordering = ('-created_at',)
