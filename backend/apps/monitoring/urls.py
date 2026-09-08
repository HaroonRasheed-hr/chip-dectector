from django.urls import path

from apps.monitoring.views import MetricsView

app_name = 'monitoring'

urlpatterns = [
    path('metrics/', MetricsView.as_view(), name='metrics'),
]
