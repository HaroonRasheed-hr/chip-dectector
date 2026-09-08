"""RF-DETR provider stub (Part B).

The AI team will replace :meth:`infer` with the real RF-DETR + TensorRT call
once their model artifacts (``.pt``/``.onnx``/``.trt``) land under
``core/ai_engine/models/``. Until then this stub fails fast on ``load`` so
nobody mistakes it for a working provider.
"""
import time

from apps.inference.bridge.dto.inference_request import InferenceRequest
from apps.inference.bridge.dto.inference_response import InferenceResponse
from apps.inference.bridge.interfaces.ai_provider import AIProvider
from core.errors import inference_error_handler


class RfDetrProvider(AIProvider):
    name = 'rf_detr'
    model_name = 'rf_detr_v1'

    def __init__(self) -> None:
        self._ready = False

    def load(self) -> None:
        # Real loader will go here once the AI team delivers the model.
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        start = time.perf_counter()
        inference_error_handler.report(
            'rf_detr provider not yet implemented — awaiting AI team model',
            context={'station_id': request.station_id},
        )
        raise NotImplementedError('RF-DETR provider model is not loaded yet')

    def shutdown(self) -> None:
        self._ready = False
