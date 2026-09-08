"""Mask-overlay generator placeholder.

The stub provider renders its own overlay inline; real providers should call
into here so the red-defect mask logic (spec B.4.1, 40–60% alpha) lives in one
place. Filled in once the AI team's provider lands.
"""
import io

from PIL import Image, ImageDraw


def apply_red_defect_mask(image_bytes: bytes, defect_boxes: list[tuple[int, int, int, int]]) -> bytes:
    """Return a JPEG byte-string with red semi-transparent overlays on the boxes."""
    image = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for box in defect_boxes:
        draw.rectangle(box, fill=(255, 0, 0, 128), outline=(255, 0, 0, 255), width=3)
    merged = Image.alpha_composite(image, overlay).convert('RGB')
    buf = io.BytesIO()
    merged.save(buf, format='JPEG', quality=85)
    return buf.getvalue()
