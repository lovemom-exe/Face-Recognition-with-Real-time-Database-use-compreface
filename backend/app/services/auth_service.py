from __future__ import annotations

from datetime import datetime, timedelta
import re

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.constants import ROLE_TEACHER, USER_STATUS_ACTIVE, USER_STATUS_DISABLED, USER_STATUS_PENDING
from ..core.exceptions import AppException
from ..models import User
from ..repositories.user_repository import UserRepository
from ..schemas.auth import TeacherRegisterRequest
from ..utils.password import hash_password, verify_password
from ..utils.tokens import create_access_token
from .audit_service import AuditService


MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def register_teacher(self, payload: TeacherRegisterRequest, *, request: Request | None = None) -> User:
        email = str(payload.email).strip().lower()
        self._validate_teacher_email_domain(email)
        if self.repo.get_by_email(email):
            raise AppException("USER_ALREADY_EXISTS", "Email nay da duoc dang ky.", status_code=409)

        item = User(
            username=self._generate_username(email),
            email=email,
            full_name=payload.full_name.strip(),
            role=ROLE_TEACHER,
            status=USER_STATUS_PENDING,
            is_active=False,
            password_hash=hash_password(payload.password),
        )
        self.db.add(item)
        try:
            self.db.flush()
            AuditService(self.db).log(
                actor=None,
                action="TEACHER_REGISTERED",
                resource_type="USER",
                resource_id=item.id,
                new_value={
                    "id": item.id,
                    "username": item.username,
                    "email": item.email,
                    "full_name": item.full_name,
                    "role": item.role,
                    "status": item.status,
                    "is_active": item.is_active,
                },
                request=request,
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppException("USER_ALREADY_EXISTS", "Email nay da duoc dang ky.", status_code=409) from exc
        self.db.refresh(item)
        return item

    def login(self, username: str, password: str, *, request: Request | None = None) -> tuple[str, User]:
        user = self.repo.get_by_login(username)
        if not user:
            raise AppException("INVALID_CREDENTIALS", "Tai khoan hoac mat khau khong dung.", status_code=401)
        now = datetime.utcnow()
        if user.status == USER_STATUS_PENDING:
            AuditService(self.db).log(actor=user, action="LOGIN_BLOCKED_PENDING", resource_type="USER", resource_id=user.id, request=request)
            self.db.commit()
            raise AppException("USER_PENDING_APPROVAL", "Tai khoan dang cho admin duyet.", status_code=403)
        if not user.is_active or user.status != USER_STATUS_ACTIVE:
            AuditService(self.db).log(actor=user, action="LOGIN_BLOCKED_INACTIVE", resource_type="USER", resource_id=user.id, request=request)
            self.db.commit()
            message = "Tai khoan da bi khoa." if user.status == USER_STATUS_DISABLED else "Tai khoan da bi vo hieu hoa."
            raise AppException("USER_INACTIVE", message, status_code=403)
        if user.locked_until and user.locked_until > now:
            raise AppException("ACCOUNT_LOCKED", "Tai khoan dang bi khoa tam thoi.", status_code=423)
        if not verify_password(password, user.password_hash):
            user.failed_login_count += 1
            if user.failed_login_count >= MAX_FAILED_LOGINS:
                user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
                code = "ACCOUNT_LOCKED"
                action = "LOGIN_LOCKED"
            else:
                code = "INVALID_CREDENTIALS"
                action = "LOGIN_FAILED"
            AuditService(self.db).log(actor=user, action=action, resource_type="USER", resource_id=user.id, request=request)
            self.db.commit()
            raise AppException(code, "Tai khoan hoac mat khau khong dung.", status_code=401)

        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = now
        AuditService(self.db).log(actor=user, action="LOGIN_SUCCESS", resource_type="USER", resource_id=user.id, request=request)
        self.db.commit()
        self.db.refresh(user)
        return create_access_token(str(user.id), user.role), user

    def change_password(self, user: User, old_password: str, new_password: str, *, request: Request | None = None) -> None:
        if not verify_password(old_password, user.password_hash):
            raise AppException("INVALID_CREDENTIALS", "Mat khau hien tai khong dung.", status_code=400)
        user.password_hash = hash_password(new_password)
        AuditService(self.db).log(actor=user, action="PASSWORD_CHANGED", resource_type="USER", resource_id=user.id, request=request)
        self.db.commit()

    def _validate_teacher_email_domain(self, email: str) -> None:
        domain = email.rsplit("@", 1)[-1].lower()
        allowed = {item.lower().lstrip("@") for item in settings.allowed_teacher_email_domains}
        if allowed and domain not in allowed:
            raise AppException(
                "INVALID_TEACHER_EMAIL_DOMAIN",
                "Chi chap nhan email truong cua giang vien.",
                status_code=400,
                details={"allowed_domains": sorted(allowed)},
            )

    def _generate_username(self, email: str) -> str:
        local_part = email.split("@", 1)[0].lower()
        base = re.sub(r"[^a-z0-9_.-]+", "_", local_part).strip("._-") or "teacher"
        base = base[:70]
        candidate = base
        suffix = 2
        while self.repo.get_by_username(candidate):
            tail = f"-{suffix}"
            candidate = f"{base[:80 - len(tail)]}{tail}"
            suffix += 1
        return candidate
