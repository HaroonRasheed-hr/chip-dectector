"""Stub provider used until the AI team delivers a real engine.

Returns a synthetic ``InferenceResponse`` so the frontend's detection flow
(upload → infer → masked image displayed) is fully exercisable end-to-end
without touching the real model. Swap it out by setting
``INFERENCE_DEFAULT_PROVIDER`` in ``.env`` once a real provider is wired up.
"""
import base64
import io
import time
from typing import Optional

from PIL import Image, ImageDraw

from apps.inference.bridge.dto.inference_request import InferenceRequest
from apps.inference.bridge.dto.inference_response import Detection, InferenceResponse
from apps.inference.bridge.interfaces.ai_provider import AIProvider
from core.errors import inference_error_handler
from core.logging_system.inference_logger import info as log_inference


class StubProvider(AIProvider):
    """Echo provider that draws a single placeholder bounding box."""

    name = 'stub'
    model_name = 'stub-v0'

    def __init__(self) -> None:
        self._ready = False

    def load(self) -> None:
        self._ready = True
        log_inference('Stub provider loaded')

    def is_ready(self) -> bool:
        return self._ready

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        start = time.perf_counter()
        try:
            image = Image.open(io.BytesIO(request.image_bytes)).convert('RGB')
        except Exception as exc:  # noqa: BLE001
            inference_error_handler.report('stub provider failed to decode image', exc=exc)
            raise

        width, height = image.size

        chip_box = (
            int(width * 0.10), int(height * 0.10),
            int(width * 0.90), int(height * 0.90),
        )
        defect_box = (
            int(width * 0.45), int(height * 0.45),
            int(width * 0.60), int(height * 0.60),
        )

        masked = _draw_defect_overlay(image, defect_box)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return InferenceResponse(
            detections=[
                Detection(class_id=0, class_name='ic_chip', confidence=0.99, bbox_xyxy=tuple(map(float, chip_box))),
                Detection(class_id=1, class_name='defect', confidence=0.91, bbox_xyxy=tuple(map(float, defect_box))),
            ],
            masked_image_base64=_encode_jpeg_base64(masked),
            inference_time_ms=elapsed_ms,
            model_name=self.model_name,
            provider_name=self.name,
            confidence_scores=[0.99, 0.91],
        )


def _draw_defect_overlay(image: Image.Image, defect_box: tuple[int, int, int, int]) -> Image.Image:
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # 50% alpha red fill — matches spec B.4.1 (40–60% alpha).
    draw.rectangle(defect_box, fill=(255, 0, 0, 128), outline=(255, 0, 0, 255), width=3)
    return Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')


def _encode_jpeg_base64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format='JPEG', quality=85)
    return base64.b64encode(buf.getvalue()).decode('ascii')
