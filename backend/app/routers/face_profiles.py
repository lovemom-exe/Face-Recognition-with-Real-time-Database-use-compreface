from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..compreface_client import CompreFaceClientError
from ..core.exceptions import AppException
from ..database import get_db
from ..models import FaceProfile, Student, User
from ..serializers import face_profile_to_dict
from ..services import FaceProfileService
from ..services.permission_service import PermissionService
from ..utils.file_validation import validate_image_upload

router = APIRouter(prefix="/api/students/{student_id}/face-profile", tags=["face enrollment"])


class FaceProfileIn(BaseModel):
    compreface_subject: str | None = None
    status: str = "PENDING"
    sample_count: int = 0


def _get_authorized_student(db: Session, student_id: int, current_user: User) -> Student:
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    permission = PermissionService(db)
    if student.class_id:
        permission.ensure_class(current_user, student.class_id)
    elif not permission.is_admin_or_staff(current_user):
        raise AppException("FORBIDDEN", "Sinh vien chua gan lop nen giang vien khong co quyen thao tac.", status_code=403)
    return student


@router.post("")
def create_face_profile(
    student_id: int,
    payload: FaceProfileIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = _get_authorized_student(db, student_id, current_user)

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
def get_face_profile(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_authorized_student(db, student_id, current_user)
    profile = db.query(FaceProfile).filter(FaceProfile.student_id == student_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Face profile not found")
    return face_profile_to_dict(profile)


@router.post("/images")
async def upload_face_images(
    student_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_authorized_student(db, student_id, current_user)
    profile = db.query(FaceProfile).filter(FaceProfile.student_id == student_id).first()
    if not profile:
        student = db.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        profile = FaceProfileService(db).ensure_profile(student)

    payload = []
    for file in files:
        content = await file.read()
        validate_image_upload(file, content)
        payload.append((file.filename or "face.jpg", content))
    profile = FaceProfileService(db).upload_examples(profile, payload)
    return face_profile_to_dict(profile)
