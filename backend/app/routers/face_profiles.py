from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..compreface_client import CompreFaceClientError
from ..database import get_db
from ..models import FaceProfile, Student
from ..serializers import face_profile_to_dict
from ..services import FaceProfileService

router = APIRouter(prefix="/api/students/{student_id}/face-profile", tags=["face enrollment"])


class FaceProfileIn(BaseModel):
    compreface_subject: str | None = None
    status: str = "PENDING"
    sample_count: int = 0


@router.post("")
def create_face_profile(student_id: int, payload: FaceProfileIn, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    subject = payload.compreface_subject.strip() if payload.compreface_subject else None
    service = FaceProfileService(db)

    if subject:
        try:
            subjects = service.compreface.list_subjects()
        except CompreFaceClientError as exc:
            raise HTTPException(status_code=503, detail=f"Không kiểm tra được subject trên CompreFace: {exc}") from exc
        if subject not in subjects:
            raise HTTPException(status_code=400, detail="Subject không tồn tại trên CompreFace.")

        mapped = db.query(FaceProfile).filter(
            FaceProfile.compreface_subject == subject,
            FaceProfile.student_id != student_id,
            FaceProfile.status != "DISABLED",
        ).first()
        if mapped:
            raise HTTPException(status_code=409, detail="Subject này đã được map với sinh viên khác.")

    profile = db.query(FaceProfile).filter(FaceProfile.student_id == student_id).first()
    if profile:
        if subject:
            profile.compreface_subject = subject
    elif subject:
        profile = FaceProfile(student_id=student.id, compreface_subject=subject)
        db.add(profile)
    else:
        profile = service.ensure_profile(student)

    if subject:
        profile.status = payload.status if payload.status else "ACTIVE"
    elif payload.status and payload.status != "PENDING":
        profile.status = payload.status
    if subject and profile.status == "PENDING":
        profile.status = "ACTIVE"
    profile.sample_count = max(profile.sample_count, payload.sample_count)
    db.commit()
    db.refresh(profile)
    return face_profile_to_dict(profile)


@router.get("")
def get_face_profile(student_id: int, db: Session = Depends(get_db)):
    profile = db.query(FaceProfile).filter(FaceProfile.student_id == student_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Face profile not found")
    return face_profile_to_dict(profile)


@router.post("/images")
async def upload_face_images(
    student_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    profile = db.query(FaceProfile).filter(FaceProfile.student_id == student_id).first()
    if not profile:
        student = db.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        profile = FaceProfileService(db).ensure_profile(student)

    payload = [(file.filename or "face.jpg", await file.read()) for file in files]
    profile = FaceProfileService(db).upload_examples(profile, payload)
    return face_profile_to_dict(profile)
