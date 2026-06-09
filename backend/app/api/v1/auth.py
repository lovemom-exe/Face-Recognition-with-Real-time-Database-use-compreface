from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...middleware.rate_limit_middleware import limiter
from ...models import User
from ...schemas.auth import ChangePasswordRequest, LoginRequest, TeacherRegisterRequest, TeacherRegisterResponse, TokenResponse
from ...schemas.common import MessageResponse
from ...schemas.user import UserOut
from ...services.audit_service import AuditService
from ...services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register-teacher", response_model=TeacherRegisterResponse)
@limiter.limit("10/hour")
def register_teacher(payload: TeacherRegisterRequest, request: Request, db: Session = Depends(get_db)):
    user = AuthService(db).register_teacher(payload, request=request)
    return TeacherRegisterResponse(
        message="Tai khoan dang cho admin duyet.",
        status="PENDING_APPROVAL",
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    token, user = AuthService(db).login(payload.username, payload.password, request=request)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    AuthService(db).change_password(current_user, payload.old_password, payload.new_password, request=request)
    return MessageResponse(message="Da doi mat khau.")


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    AuditService(db).log(actor=current_user, action="LOGOUT", resource_type="USER", resource_id=current_user.id, request=request, commit=True)
    return MessageResponse(message="Da dang xuat.")
