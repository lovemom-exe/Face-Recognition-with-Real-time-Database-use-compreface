from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ...api.deps import require_admin
from ...database import get_db
from ...models import User
from ...schemas.common import MessageResponse
from ...schemas.teacher_assignment import TeacherAssignmentCreate, TeacherAssignmentOut
from ...services.teacher_assignment_service import TeacherAssignmentService

router = APIRouter(prefix="/api/v1/teacher-assignments", tags=["teacher assignments"])


@router.get("", response_model=list[TeacherAssignmentOut])
def list_assignments(
    teacher_id: int | None = None,
    class_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return TeacherAssignmentService(db).list_assignments(teacher_id=teacher_id, class_id=class_id)


@router.post("", response_model=TeacherAssignmentOut)
def create_assignment(
    payload: TeacherAssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return TeacherAssignmentService(db).create_assignment(payload, actor=current_user, request=request)


@router.delete("/{assignment_id}", response_model=MessageResponse)
def delete_assignment(
    assignment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    TeacherAssignmentService(db).delete_assignment(assignment_id, actor=current_user, request=request)
    return MessageResponse(message="Da xoa phan cong giang vien.")
