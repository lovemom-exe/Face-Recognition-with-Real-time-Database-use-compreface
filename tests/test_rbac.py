from __future__ import annotations

import pytest

from backend.app.core.exceptions import AppException
from backend.app.services.permission_service import PermissionService


def test_admin_can_access_any_class_course(db_session, admin_user, class_course):
    PermissionService(db_session).ensure_class_course(admin_user, class_course.id)


def test_teacher_without_assignment_is_forbidden(db_session, teacher_user, class_course):
    with pytest.raises(AppException) as exc:
        PermissionService(db_session).ensure_class_course(teacher_user, class_course.id)
    assert exc.value.error_code == "FORBIDDEN"
