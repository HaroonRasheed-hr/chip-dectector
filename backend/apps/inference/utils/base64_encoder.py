"""Base64 helpers shared by providers + serializers."""
import base64


def to_data_url(jpeg_base64: str) -> str:
    """Wrap a JPEG base64 string in a ``data:`` URL the browser can render directly."""
    return f'data:image/jpeg;base64,{jpeg_base64}'


def encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')
