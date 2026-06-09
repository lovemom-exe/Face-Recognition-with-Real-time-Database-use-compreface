from __future__ import annotations

from backend.app.models import TeacherAssignment
from backend.app.services.permission_service import PermissionService


def test_teacher_assignment_allows_class_course_access(db_session, teacher_user, class_course):
    db_session.add(
        TeacherAssignment(
            teacher_id=teacher_user.id,
            class_id=class_course.class_id,
            course_id=class_course.course_id,
            semester=class_course.semester,
        )
    )
    db_session.commit()
    PermissionService(db_session).ensure_class_course(teacher_user, class_course.id)


def test_teacher_accessible_scope_lists_assigned_class_and_course(db_session, teacher_user, class_course):
    db_session.add(
        TeacherAssignment(
            teacher_id=teacher_user.id,
            class_id=class_course.class_id,
            course_id=class_course.course_id,
            semester=class_course.semester,
        )
    )
    db_session.commit()

    service = PermissionService(db_session)
    assert service.accessible_class_ids(teacher_user) == [class_course.class_id]
    assert service.accessible_course_ids(teacher_user) == [class_course.course_id]
