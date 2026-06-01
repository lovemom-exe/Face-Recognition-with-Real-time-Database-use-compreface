"""
Phase 1 CompreFace smoke test.

This script checks the current Face Recognition service API key, optionally
creates a subject, uploads sample face images, and recognizes a test image.
By default it only lists subjects, so it is safe to run without changing data.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import requests


DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_API_KEY = ""
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp", ".ico"}


class CompreFaceSmokeError(RuntimeError):
    pass


def configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def pretty_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def build_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def request_json(
    method: str,
    url: str,
    api_key: str,
    *,
    expected_statuses: Iterable[int] = (200,),
    timeout: float = 15.0,
    **kwargs: Any,
) -> tuple[int, Any]:
    headers = kwargs.pop("headers", {})
    headers["x-api-key"] = api_key

    try:
        response = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)
    except requests.RequestException as exc:
        raise CompreFaceSmokeError(f"Cannot reach CompreFace: {exc}") from exc

    status = response.status_code
    try:
        body: Any = response.json()
    except ValueError:
        body = response.text

    if status not in expected_statuses:
        raise CompreFaceSmokeError(
            f"{method} {url} returned HTTP {status}\nResponse:\n{pretty_json(body)}"
        )

    return status, body


def list_subjects(base_url: str, api_key: str) -> list[str]:
    url = build_url(base_url, "/api/v1/recognition/subjects/")
    _, body = request_json("GET", url, api_key)
    subjects = body.get("subjects", []) if isinstance(body, dict) else []
    print(f"[OK] Connected to CompreFace. Subjects found: {len(subjects)}")
    for subject in subjects:
        print(f"  - {subject}")
    return subjects


def create_subject(base_url: str, api_key: str, subject: str) -> None:
    url = build_url(base_url, "/api/v1/recognition/subjects")
    try:
        _, body = request_json(
            "POST",
            url,
            api_key,
            json={"subject": subject},
            expected_statuses=(200, 201),
        )
        print(f"[OK] Created subject: {body.get('subject', subject)}")
    except CompreFaceSmokeError as exc:
        print(f"[WARN] Could not create subject '{subject}'. It may already exist.")
        print(str(exc))


def iter_image_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]

    if not path.is_dir():
        raise CompreFaceSmokeError(f"Image path does not exist: {path}")

    return sorted(
        child
        for child in path.rglob("*")
        if child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS
    )


def upload_image(base_url: str, api_key: str, subject: str, image_path: Path, det_prob_threshold: float | None) -> Any:
    encoded_subject = quote(subject, safe="")
    url = build_url(base_url, f"/api/v1/recognition/faces?subject={encoded_subject}")
    if det_prob_threshold is not None:
        url = f"{url}&det_prob_threshold={det_prob_threshold}"

    mime_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
    with image_path.open("rb") as image_file:
        files = {"file": (image_path.name, image_file, mime_type)}
        _, body = request_json("POST", url, api_key, files=files, expected_statuses=(200, 201))

    print(f"[OK] Uploaded {image_path} -> image_id={body.get('image_id')}")
    return body


def upload_images(
    base_url: str,
    api_key: str,
    subject: str,
    image_path: Path,
    det_prob_threshold: float | None,
) -> None:
    images = iter_image_files(image_path)
    if not images:
        raise CompreFaceSmokeError(f"No supported image files found in: {image_path}")

    print(f"[INFO] Uploading {len(images)} image(s) for subject '{subject}'")
    for image in images:
        upload_image(base_url, api_key, subject, image, det_prob_threshold)


def list_faces(base_url: str, api_key: str, subject: str | None) -> None:
    url = build_url(base_url, "/api/v1/recognition/faces?page=0&size=100")
    if subject:
        url = f"{url}&subject={quote(subject, safe='')}"

    _, body = request_json("GET", url, api_key)
    faces = body.get("faces", []) if isinstance(body, dict) else []
    print(f"[OK] Saved face examples found: {len(faces)}")
    for face in faces:
        print(f"  - subject={face.get('subject')} image_id={face.get('image_id')}")


def recognize_image(
    base_url: str,
    api_key: str,
    image_path: Path,
    threshold: float,
    prediction_count: int,
    det_prob_threshold: float | None,
) -> None:
    url = build_url(base_url, f"/api/v1/recognition/recognize?prediction_count={prediction_count}")
    if det_prob_threshold is not None:
        url = f"{url}&det_prob_threshold={det_prob_threshold}"

    mime_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
    with image_path.open("rb") as image_file:
        files = {"file": (image_path.name, image_file, mime_type)}
        _, body = request_json("POST", url, api_key, files=files)

    print("[OK] Recognition response:")
    print(pretty_json(body))

    results = body.get("result", []) if isinstance(body, dict) else []
    for index, face in enumerate(results, start=1):
        subjects = face.get("subjects", [])
        if not subjects:
            print(f"[RESULT] Face #{index}: UNKNOWN (no subject predictions)")
            continue

        best = subjects[0]
        subject = best.get("subject", "UNKNOWN")
        similarity = float(best.get("similarity", 0.0))
        result_type = "MATCH" if similarity >= threshold else "LOW_CONFIDENCE"
        print(
            f"[RESULT] Face #{index}: {result_type} "
            f"subject={subject} similarity={similarity:.4f} threshold={threshold:.4f}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test CompreFace subject enrollment and recognition APIs."
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("COMPREFACE_BASE_URL", DEFAULT_BASE_URL),
        help="CompreFace base URL. Default: env COMPREFACE_BASE_URL or http://localhost:8000",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("COMPREFACE_RECOGNITION_API_KEY", DEFAULT_API_KEY),
        help="Recognition service API key. Default: env COMPREFACE_RECOGNITION_API_KEY.",
    )
    parser.add_argument("--subject", help="Subject name to create/use for uploads.")
    parser.add_argument("--create-subject", action="store_true", help="Create the subject before upload.")
    parser.add_argument("--upload", type=Path, help="Image file or folder to upload as examples for --subject.")
    parser.add_argument("--list-faces", action="store_true", help="List saved face examples.")
    parser.add_argument("--recognize", type=Path, help="Image file to recognize.")
    parser.add_argument("--threshold", type=float, default=0.97, help="Local decision threshold for result summary.")
    parser.add_argument("--prediction-count", type=int, default=1, help="Number of subject predictions per face.")
    parser.add_argument(
        "--det-prob-threshold",
        type=float,
        help="Optional CompreFace face-detection probability threshold.",
    )
    return parser.parse_args()


def main() -> int:
    configure_console_encoding()
    args = parse_args()

    if not args.api_key:
        print("[ERROR] Missing CompreFace API key. Set COMPREFACE_RECOGNITION_API_KEY or pass --api-key.", file=sys.stderr)
        return 2

    if args.upload and not args.subject:
        print("[ERROR] --upload requires --subject.", file=sys.stderr)
        return 2

    if args.create_subject and not args.subject:
        print("[ERROR] --create-subject requires --subject.", file=sys.stderr)
        return 2

    try:
        list_subjects(args.base_url, args.api_key)

        if args.create_subject:
            create_subject(args.base_url, args.api_key, args.subject)

        if args.upload:
            upload_images(args.base_url, args.api_key, args.subject, args.upload, args.det_prob_threshold)

        if args.list_faces:
            list_faces(args.base_url, args.api_key, args.subject)

        if args.recognize:
            recognize_image(
                args.base_url,
                args.api_key,
                args.recognize,
                args.threshold,
                args.prediction_count,
                args.det_prob_threshold,
            )

    except CompreFaceSmokeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
