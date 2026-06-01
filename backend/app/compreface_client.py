from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from .config import settings


class CompreFaceClientError(RuntimeError):
    pass


class CompreFaceClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (base_url or settings.compreface_base_url).rstrip("/")
        self.api_key = api_key or settings.compreface_recognition_api_key

    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self.api_key}

    def _json(self, response: requests.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    def _request(self, method: str, path: str, *, expected: tuple[int, ...] = (200,), **kwargs: Any) -> Any:
        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers(),
                timeout=30,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise CompreFaceClientError(f"CompreFace request failed: {exc}") from exc

        body = self._json(response)
        if response.status_code not in expected:
            raise CompreFaceClientError(f"CompreFace HTTP {response.status_code}: {body}")
        return body

    def list_subjects(self) -> list[str]:
        body = self._request("GET", "/api/v1/recognition/subjects/")
        return body.get("subjects", [])

    def create_subject(self, subject: str) -> dict[str, Any]:
        try:
            return self._request(
                "POST",
                "/api/v1/recognition/subjects",
                json={"subject": subject},
                expected=(200, 201),
            )
        except CompreFaceClientError as exc:
            if "already" in str(exc).lower() or "409" in str(exc):
                return {"subject": subject, "already_exists": True}
            raise

    def upload_face_bytes(self, subject: str, file_name: str, content: bytes) -> dict[str, Any]:
        encoded_subject = quote(subject, safe="")
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        files = {"file": (file_name, content, mime_type)}
        return self._request(
            "POST",
            f"/api/v1/recognition/faces?subject={encoded_subject}",
            files=files,
            expected=(200, 201),
        )

    def upload_face_file(self, subject: str, path: Path) -> dict[str, Any]:
        return self.upload_face_bytes(subject, path.name, path.read_bytes())

    def recognize_bytes(self, file_name: str, content: bytes, prediction_count: int = 1) -> dict[str, Any]:
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        files = {"file": (file_name, content, mime_type)}
        return self._request(
            "POST",
            f"/api/v1/recognition/recognize?prediction_count={prediction_count}",
            files=files,
        )
