from __future__ import annotations

from fastapi import APIRouter

from ..compreface_client import CompreFaceClient, CompreFaceClientError
from ..config import settings

router = APIRouter(prefix="/api/compreface", tags=["compreface"])


@router.get("/status")
def compreface_status():
    client = CompreFaceClient()
    try:
        subjects = client.list_subjects()
        return {
            "status": "ok",
            "base_url": settings.compreface_base_url,
            "subject_count": len(subjects),
        }
    except CompreFaceClientError as exc:
        return {
            "status": "error",
            "base_url": settings.compreface_base_url,
            "error": str(exc),
        }


@router.get("/subjects")
def list_compreface_subjects():
    client = CompreFaceClient()
    try:
        subjects = client.list_subjects()
        return {"subjects": subjects, "count": len(subjects)}
    except CompreFaceClientError as exc:
        return {"subjects": [], "count": 0, "error": str(exc)}
