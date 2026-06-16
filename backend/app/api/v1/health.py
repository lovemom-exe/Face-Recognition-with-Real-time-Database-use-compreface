from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.config import settings
from ...database import get_db
from ...services.health_service import HealthService

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@router.get("/db")
def db_health(db: Session = Depends(get_db)):
    return HealthService(db).db_health()


@router.get("/compreface")
def compreface_health(db: Session = Depends(get_db)):
    return HealthService(db).compreface_health()
