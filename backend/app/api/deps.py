from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..core.constants import ROLE_ADMIN
from ..core.exceptions import AppException
from ..database import get_db
from ..models import User
from ..services.permission_service import PermissionService
from ..utils.tokens import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    subject = payload.get("sub")
    if not subject:
        raise AppException("INVALID_TOKEN", "Token khong hop le.", status_code=401)
    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise AppException("INVALID_TOKEN", "Token khong hop le.", status_code=401) from exc
    user = db.get(User, user_id)
    if not user:
        raise AppException("INVALID_TOKEN", "Token khong hop le.", status_code=401)
    if not user.is_active or user.status != "ACTIVE":
        raise AppException("USER_INACTIVE", "Tai khoan da bi vo hieu hoa.", status_code=403)
    return user


def require_roles(*roles: str) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in set(roles):
            raise AppException("FORBIDDEN", "Ban khong co quyen thuc hien thao tac nay.", status_code=403)
        return current_user

    return dependency


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != ROLE_ADMIN:
        raise AppException("FORBIDDEN", "Chi admin moi duoc thuc hien thao tac nay.", status_code=403)
    return current_user


def ensure_teacher_can_access_class_course(
    class_course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    PermissionService(db).ensure_class_course(current_user, class_course_id)
    return current_user
