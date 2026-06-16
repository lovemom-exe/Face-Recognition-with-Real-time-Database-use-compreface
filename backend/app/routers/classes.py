from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..api.deps import get_current_user, require_roles
from ..database import get_db
from ..models import Student, StudyClass, User
from ..serializers import student_to_dict, study_class_to_dict
from ..services.permission_service import PermissionService

router = APIRouter(prefix="/api/classes", tags=["classes"])


class ClassIn(BaseModel):
    class_code: str
    class_name: str
    school_year: str | None = None
    status: str = "ACTIVE"


class ClassUpdate(BaseModel):
    class_code: str | None = None
    class_name: str | None = None
    school_year: str | None = None
    status: str | None = None


@router.get("")
def list_classes(
    include_disabled: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(StudyClass)
    accessible_class_ids = PermissionService(db).accessible_class_ids(current_user)
    if accessible_class_ids is not None:
        query = query.filter(StudyClass.id.in_(accessible_class_ids))
    if not include_disabled:
        query = query.filter(StudyClass.status == "ACTIVE")
    return [study_class_to_dict(item) for item in query.order_by(StudyClass.class_code).all()]


@router.post("")
def create_class(payload: ClassIn, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "STAFF"))):
    item = StudyClass(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return study_class_to_dict(item)


@router.get("/{class_id}")
def get_class(class_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.get(StudyClass, class_id)
    if not item:
        raise HTTPException(status_code=404, detail="Class not found")
    PermissionService(db).ensure_class(current_user, class_id)
    students = db.query(Student).filter(
        Student.class_id == class_id,
        Student.status == "ACTIVE",
    ).order_by(Student.full_name).all()
    return {
        **study_class_to_dict(item),
        "student_count": len(students),
        "students": [
            {
                **student_to_dict(student),
                "has_face_profile": bool(student.face_profile),
                "compreface_subject": student.face_profile.compreface_subject if student.face_profile else None,
                "sample_count": student.face_profile.sample_count if student.face_profile else 0,
                "face_profile_status": student.face_profile.status if student.face_profile else "NOT_MAPPED",
            }
            for student in students
        ],
    }


@router.put("/{class_id}")
def update_class(
    class_id: int,
    payload: ClassUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN", "STAFF")),
):
    item = db.get(StudyClass, class_id)
    if not item:
        raise HTTPException(status_code=404, detail="Class not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return study_class_to_dict(item)


@router.delete("/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "STAFF"))):
    item = db.get(StudyClass, class_id)
    if not item:
        raise HTTPException(status_code=404, detail="Class not found")
    item.status = "DISABLED"
    db.commit()
    return {"deleted": True}
