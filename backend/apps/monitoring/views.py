"""DRF view exposing a single live telemetry snapshot — spec A.5."""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.monitoring.telemetry import collect_snapshot


class MetricsView(APIView):
    """``GET /api/monitoring/metrics/`` — polled by the System Monitoring Panel."""

    permission_classes = (AllowAny,)

    def get(self, request):
        return Response(collect_snapshot())
