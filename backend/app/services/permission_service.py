from __future__ import annotations

from sqlalchemy.orm import Session

from ..core.constants import ROLE_ADMIN, ROLE_STAFF, ROLE_TEACHER
from ..core.exceptions import AppException
from ..models import AttendanceSession, ClassCourse, TeacherAssignment, User


class PermissionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def require_roles(self, user: User, allowed_roles: set[str]) -> None:
        if user.role not in allowed_roles:
            raise AppException("FORBIDDEN", "Ban khong co quyen thuc hien thao tac nay.", status_code=403)

    def is_admin_or_staff(self, user: User) -> bool:
        return user.role in {ROLE_ADMIN, ROLE_STAFF}

    def accessible_class_ids(self, user: User) -> list[int] | None:
        if self.is_admin_or_staff(user):
            return None
        if user.role != ROLE_TEACHER:
            return []
        ids = {
            row[0]
            for row in self.db.query(ClassCourse.class_id)
            .filter(ClassCourse.teacher_id == user.id)
            .all()
        }
        ids.update(
            row[0]
            for row in self.db.query(TeacherAssignment.class_id)
            .filter(TeacherAssignment.teacher_id == user.id)
            .all()
        )
        return sorted(ids)

    def accessible_course_ids(self, user: User) -> list[int] | None:
        if self.is_admin_or_staff(user):
            return None
        if user.role != ROLE_TEACHER:
            return []
        ids = {
            row[0]
            for row in self.db.query(ClassCourse.course_id)
            .filter(ClassCourse.teacher_id == user.id)
            .all()
        }
        ids.update(
            row[0]
            for row in self.db.query(TeacherAssignment.course_id)
            .filter(TeacherAssignment.teacher_id == user.id, TeacherAssignment.course_id.is_not(None))
            .all()
        )
        return sorted(ids)

    def can_access_class_course(self, user: User, class_course_id: int) -> bool:
        if user.role in {ROLE_ADMIN, ROLE_STAFF}:
            return True
        if user.role != ROLE_TEACHER:
            return False
        class_course = self.db.get(ClassCourse, class_course_id)
        if not class_course:
            raise AppException("RESOURCE_NOT_FOUND", "Khong tim thay lop-mon hoc.", status_code=404)
        if class_course.teacher_id == user.id:
            return True
        exists = (
            self.db.query(TeacherAssignment)
            .filter(
                TeacherAssignment.teacher_id == user.id,
                TeacherAssignment.class_id == class_course.class_id,
                (TeacherAssignment.course_id == class_course.course_id) | (TeacherAssignment.course_id.is_(None)),
            )
            .first()
        )
        return exists is not None

    def ensure_class_course(self, user: User, class_course_id: int) -> None:
        if not self.can_access_class_course(user, class_course_id):
            raise AppException("FORBIDDEN", "Giang vien chua duoc gan voi lop-mon hoc nay.", status_code=403)

    def can_access_class(self, user: User, class_id: int) -> bool:
        if self.is_admin_or_staff(user):
            return True
        if user.role != ROLE_TEACHER:
            return False
        accessible_ids = self.accessible_class_ids(user) or []
        return class_id in accessible_ids

    def ensure_class(self, user: User, class_id: int) -> None:
        if not self.can_access_class(user, class_id):
            raise AppException("FORBIDDEN", "Giang vien chua duoc gan voi lop hoc nay.", status_code=403)

    def ensure_session(self, user: User, session_id: int) -> AttendanceSession:
        session = self.db.get(AttendanceSession, session_id)
        if not session:
            raise AppException("RESOURCE_NOT_FOUND", "Khong tim thay buoi diem danh.", status_code=404)
        self.ensure_class_course(user, session.class_course_id)
        return session
