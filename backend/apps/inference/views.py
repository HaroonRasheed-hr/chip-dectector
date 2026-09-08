"""DRF views for the inference endpoints."""
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inference.serializers import (
    InferenceRequestSerializer,
    InferenceResponseSerializer,
)
from apps.inference.services.inference_service import execute_inference
from core.errors import backend_error_handler


class InferView(APIView):
    """``POST /api/inference/infer/`` — multipart upload, returns masked result.

    Auth is intentionally open (``AllowAny``) so the detection page works
    without a login during development. Switch to ``IsAuthenticated`` for
    production once the frontend wires the access token in.
    """

    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = InferenceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = execute_inference(
                uploaded_image=data['image'],
                user=request.user,
                model_hint=data.get('model') or None,
                confidence_threshold=data.get('confidence_threshold'),
                line_id=data.get('line_id') or None,
                station_id=data.get('station_id') or None,
            )
        except NotImplementedError as exc:
            backend_error_handler.report('inference provider not implemented', exc=exc)
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:  # noqa: BLE001
            backend_error_handler.report('inference request failed', exc=exc)
            return Response(
                {'detail': 'Inference failed. See server logs for details.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(InferenceResponseSerializer(result).data, status=status.HTTP_200_OK)
