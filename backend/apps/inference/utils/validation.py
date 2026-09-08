"""Upload validation helpers — first-line defence before invoking the model."""
from rest_framework.exceptions import ValidationError

_ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/bmp'}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_image_upload(uploaded_file) -> None:
    """Raise :class:`ValidationError` if the upload isn't a usable image."""
    if uploaded_file is None:
        raise ValidationError({'image': 'No image uploaded.'})

    if uploaded_file.size <= 0:
        raise ValidationError({'image': 'Uploaded file is empty.'})

    if uploaded_file.size > _MAX_BYTES:
        raise ValidationError({'image': f'File exceeds {_MAX_BYTES // (1024 * 1024)} MB limit.'})

    content_type = (uploaded_file.content_type or '').lower()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise ValidationError({'image': f'Unsupported content type: {content_type or "unknown"}.'})
