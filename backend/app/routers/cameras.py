from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..api.deps import require_roles
from ..database import get_db
from ..models import Camera, User
from ..serializers import camera_to_dict

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


class CameraIn(BaseModel):
    camera_code: str
    name: str
    location: str | None = None
    stream_url: str | None = None
    status: str = "ACTIVE"


class CameraUpdate(BaseModel):
    camera_code: str | None = None
    name: str | None = None
    location: str | None = None
    stream_url: str | None = None
    status: str | None = None


@router.get("")
def list_cameras(db: Session = Depends(get_db)):
    return [camera_to_dict(item) for item in db.query(Camera).order_by(Camera.camera_code).all()]


@router.post("")
def create_camera(payload: CameraIn, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "STAFF"))):
    item = Camera(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return camera_to_dict(item)


@router.get("/{camera_id}")
def get_camera(camera_id: int, db: Session = Depends(get_db)):
    item = db.get(Camera, camera_id)
    if not item:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera_to_dict(item)


@router.put("/{camera_id}")
def update_camera(
    camera_id: int,
    payload: CameraUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN", "STAFF")),
):
    item = db.get(Camera, camera_id)
    if not item:
        raise HTTPException(status_code=404, detail="Camera not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return camera_to_dict(item)
