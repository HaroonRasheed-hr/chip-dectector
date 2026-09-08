"""TensorRT provider stub (Part B deployment target).

Wraps an FP16 ``.trt`` engine. Implementation deferred until the AI team
publishes the engine file for the deployment GPU (spec B.6).
"""
from apps.inference.bridge.dto.inference_request import InferenceRequest
from apps.inference.bridge.dto.inference_response import InferenceResponse
from apps.inference.bridge.interfaces.ai_provider import AIProvider
from core.errors import inference_error_handler


class TensorRTProvider(AIProvider):
    name = 'tensorrt'
    model_name = 'rf_detr_v1.trt'

    def __init__(self) -> None:
        self._ready = False

    def load(self) -> None:
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        inference_error_handler.report(
            'tensorrt provider not yet implemented — awaiting AI team engine',
            context={'station_id': request.station_id},
        )
        raise NotImplementedError('TensorRT provider engine is not loaded yet')

    def shutdown(self) -> None:
        self._ready = False
