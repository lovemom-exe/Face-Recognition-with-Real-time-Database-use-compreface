from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from ..core.config import settings
from ..core.exceptions import AppException


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
CSV_EXTENSIONS = {".csv"}
CSV_MIME_TYPES = {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"}


def safe_upload_name(filename: str | None, allowed_extensions: set[str]) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in allowed_extensions:
        raise AppException("INVALID_FILE_TYPE", "Dinh dang file khong duoc ho tro.", status_code=400)
    return f"{uuid4().hex}{suffix}"


def validate_image_upload(file: UploadFile, content: bytes) -> str:
    if file.content_type not in IMAGE_MIME_TYPES:
        raise AppException("INVALID_FILE_TYPE", "Chi ho tro anh JPG, PNG hoac WEBP.", status_code=400)
    if len(content) > settings.max_image_upload_mb * 1024 * 1024:
        raise AppException("FILE_TOO_LARGE", "Anh upload vuot qua dung luong cho phep.", status_code=413)
    return safe_upload_name(file.filename, IMAGE_EXTENSIONS)


def validate_csv_upload(file: UploadFile, content: bytes) -> str:
    if file.content_type and file.content_type not in CSV_MIME_TYPES:
        raise AppException("INVALID_FILE_TYPE", "Chi ho tro file CSV.", status_code=400)
    if len(content) > settings.max_csv_upload_mb * 1024 * 1024:
        raise AppException("FILE_TOO_LARGE", "File CSV vuot qua dung luong cho phep.", status_code=413)
    return safe_upload_name(file.filename, CSV_EXTENSIONS)
