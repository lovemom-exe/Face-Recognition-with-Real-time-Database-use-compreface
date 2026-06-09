from __future__ import annotations

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.constants import ROLE_TEACHER
from ..core.exceptions import AppException
from ..models import Course, StudyClass, TeacherAssignment, User
from ..repositories.teacher_assignment_repository import TeacherAssignmentRepository
from ..schemas.teacher_assignment import TeacherAssignmentCreate
from .audit_service import AuditService


class TeacherAssignmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TeacherAssignmentRepository(db)

    def list_assignments(self, teacher_id: int | None = None, class_id: int | None = None) -> list[TeacherAssignment]:
        return self.repo.list(teacher_id=teacher_id, class_id=class_id)

    def create_assignment(
        self,
        payload: TeacherAssignmentCreate,
        *,
        actor: User | None = None,
        request: Request | None = None,
    ) -> TeacherAssignment:
        teacher = self.db.get(User, payload.teacher_id)
        if not teacher or teacher.role != ROLE_TEACHER:
            raise AppException("RESOURCE_NOT_FOUND", "Khong tim thay giang vien hop le.", status_code=404)
        if not self.db.get(StudyClass, payload.class_id):
            raise AppException("RESOURCE_NOT_FOUND", "Khong tim thay lop hoc.", status_code=404)
        if payload.course_id and not self.db.get(Course, payload.course_id):
            raise AppException("RESOURCE_NOT_FOUND", "Khong tim thay mon hoc.", status_code=404)
        item = TeacherAssignment(
            teacher_id=payload.teacher_id,
            class_id=payload.class_id,
            course_id=payload.course_id,
            semester=payload.semester,
            created_by=actor.id if actor else None,
        )
        self.db.add(item)
        try:
            self.db.flush()
            AuditService(self.db).log(
                actor=actor,
                action="TEACHER_ASSIGNMENT_CREATED",
                resource_type="TEACHER_ASSIGNMENT",
                resource_id=item.id,
                new_value={
                    "teacher_id": item.teacher_id,
                    "class_id": item.class_id,
                    "course_id": item.course_id,
                    "semester": item.semester,
                },
                request=request,
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppException("DUPLICATE_ASSIGNMENT", "Giang vien da duoc gan voi pham vi nay.", status_code=409) from exc
        self.db.refresh(item)
        return item

    def delete_assignment(self, assignment_id: int, *, actor: User | None = None, request: Request | None = None) -> None:
        item = self.repo.get(assignment_id)
        if not item:
            raise AppException("RESOURCE_NOT_FOUND", "Khong tim thay phan cong giang vien.", status_code=404)
        old = {"teacher_id": item.teacher_id, "class_id": item.class_id, "course_id": item.course_id, "semester": item.semester}
        self.db.delete(item)
        AuditService(self.db).log(
            actor=actor,
            action="TEACHER_ASSIGNMENT_DELETED",
            resource_type="TEACHER_ASSIGNMENT",
            resource_id=assignment_id,
            old_value=old,
            request=request,
        )
        self.db.commit()
