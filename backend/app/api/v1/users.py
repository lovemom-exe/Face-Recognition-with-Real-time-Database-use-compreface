from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ...api.deps import require_admin
from ...database import get_db
from ...models import User
from ...schemas.user import UserCreate, UserOut, UserUpdate
from ...services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    role: str | None = None,
    status: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return UserService(db).list_users(role=role, status=status, is_active=is_active)


@router.post("", response_model=UserOut)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return UserService(db).create_user(payload, actor=current_user, request=request)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    item = db.get(User, user_id)
    if not item:
        from ...core.exceptions import AppException

        raise AppException("RESOURCE_NOT_FOUND", "Khong tim thay user.", status_code=404)
    return item


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return UserService(db).update_user(user_id, payload, actor=current_user, request=request)


@router.post("/{user_id}/approve", response_model=UserOut)
def approve_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return UserService(db).approve_teacher(user_id, actor=current_user, request=request)


@router.post("/{user_id}/disable", response_model=UserOut)
def disable_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return UserService(db).disable_user(user_id, actor=current_user, request=request)


@router.delete("/{user_id}", response_model=UserOut)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return UserService(db).disable_user(user_id, actor=current_user, request=request)
