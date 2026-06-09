from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import TeacherAssignment


class TeacherAssignmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, assignment_id: int) -> TeacherAssignment | None:
        return self.db.get(TeacherAssignment, assignment_id)

    def list(self, *, teacher_id: int | None = None, class_id: int | None = None) -> list[TeacherAssignment]:
        query = self.db.query(TeacherAssignment)
        if teacher_id is not None:
            query = query.filter(TeacherAssignment.teacher_id == teacher_id)
        if class_id is not None:
            query = query.filter(TeacherAssignment.class_id == class_id)
        return query.order_by(TeacherAssignment.created_at.desc()).all()
