from __future__ import annotations

import pytest
from io import BytesIO

from starlette.datastructures import Headers, UploadFile

from backend.app.core.exceptions import AppException
from backend.app.utils.file_validation import validate_image_upload


def test_validate_image_upload_accepts_jpeg():
    file = UploadFile(file=BytesIO(b"abc"), filename="frame.jpg", headers=Headers({"content-type": "image/jpeg"}))
    assert validate_image_upload(file, b"abc").endswith(".jpg")


def test_validate_image_upload_rejects_text_file():
    file = UploadFile(file=BytesIO(b"abc"), filename="frame.txt", headers=Headers({"content-type": "text/plain"}))
    with pytest.raises(AppException) as exc:
        validate_image_upload(file, b"abc")
    assert exc.value.error_code == "INVALID_FILE_TYPE"
