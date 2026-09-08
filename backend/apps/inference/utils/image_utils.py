"""Helpers for reading bytes from Django uploads without buffering twice."""
from django.core.files.uploadedfile import UploadedFile


def read_upload_bytes(uploaded: UploadedFile) -> bytes:
    """Read the upload into memory once and rewind for any later reads."""
    uploaded.seek(0)
    try:
        return uploaded.read()
    finally:
        uploaded.seek(0)
