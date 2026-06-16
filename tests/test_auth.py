from __future__ import annotations

import pytest

from backend.app.core.exceptions import AppException
from backend.app.schemas.auth import TeacherRegisterRequest
from backend.app.services.auth_service import AuthService
from backend.app.services.user_service import UserService


def test_login_success_returns_token(db_session, admin_user):
    token, user = AuthService(db_session).login("admin", "password123")
    assert token
    assert user.id == admin_user.id
    assert user.failed_login_count == 0


def test_login_wrong_password_fails(db_session, admin_user):
    with pytest.raises(AppException) as exc:
        AuthService(db_session).login("admin", "wrong-password")
    assert exc.value.error_code == "INVALID_CREDENTIALS"


def test_register_teacher_creates_pending_account(db_session):
    user = AuthService(db_session).register_teacher(
        TeacherRegisterRequest(email="teacher@hust.edu.vn", full_name="Teacher One", password="password123")
    )
    assert user.role == "TEACHER"
    assert user.status == "PENDING"
    assert user.is_active is False
    assert user.username == "teacher"


def test_register_teacher_rejects_non_school_email(db_session):
    with pytest.raises(AppException) as exc:
        AuthService(db_session).register_teacher(
            TeacherRegisterRequest(email="teacher@gmail.com", full_name="Teacher One", password="password123")
        )
    assert exc.value.error_code == "INVALID_TEACHER_EMAIL_DOMAIN"


def test_pending_teacher_cannot_login_until_admin_approves(db_session, admin_user):
    teacher = AuthService(db_session).register_teacher(
        TeacherRegisterRequest(email="teacher@hust.edu.vn", full_name="Teacher One", password="password123")
    )
    with pytest.raises(AppException) as exc:
        AuthService(db_session).login("teacher@hust.edu.vn", "password123")
    assert exc.value.error_code == "USER_PENDING_APPROVAL"

    UserService(db_session).approve_teacher(teacher.id, actor=admin_user)
    token, user = AuthService(db_session).login("teacher@hust.edu.vn", "password123")
    assert token
    assert user.id == teacher.id
    assert user.status == "ACTIVE"


def test_change_password_updates_login_secret(db_session, teacher_user):
    AuthService(db_session).change_password(teacher_user, "password123", "new-password123")
    with pytest.raises(AppException):
        AuthService(db_session).login("teacher", "password123")
    token, user = AuthService(db_session).login("teacher@example.com", "new-password123")
    assert token
    assert user.id == teacher_user.id
