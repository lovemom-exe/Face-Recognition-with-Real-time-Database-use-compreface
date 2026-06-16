from __future__ import annotations

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.constants import ACTIVE_ROLES, ROLE_ADMIN, ROLE_TEACHER, USER_STATUS_ACTIVE, USER_STATUS_DISABLED
from ..core.exceptions import AppException
from ..models import User
from ..repositories.user_repository import UserRepository
from ..schemas.user import UserCreate, UserUpdate
from ..utils.password import hash_password
from .audit_service import AuditService


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def list_users(self, *, role: str | None = None, status: str | None = None, is_active: bool | None = None) -> list[User]:
        if role:
            self._validate_role(role)
        return self.repo.list(role=role, status=status, is_active=is_active)

    def create_user(self, payload: UserCreate, *, actor: User | None = None, request: Request | None = None) -> User:
        self._validate_role(payload.role)
        item = User(
            username=payload.username.strip(),
            email=str(payload.email) if payload.email else None,
            full_name=payload.full_name.strip(),
            role=payload.role,
            status=USER_STATUS_ACTIVE if payload.is_active else USER_STATUS_DISABLED,
            is_active=payload.is_active,
            password_hash=hash_password(payload.password),
        )
        self.db.add(item)
        try:
            self.db.flush()
            AuditService(self.db).log(
                actor=actor,
                action="USER_CREATED",
                resource_type="USER",
                resource_id=item.id,
                new_value=self._snapshot(item),
                request=request,
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppException("USER_ALREADY_EXISTS", "Username hoac email da ton tai.", status_code=409) from exc
        self.db.refresh(item)
        return item

    def update_user(
        self,
        user_id: int,
        payload: UserUpdate,
        *,
        actor: User | None = None,
        request: Request | None = None,
    ) -> User:
        item = self.repo.get(user_id)
        if not item:
            raise AppException("RESOURCE_NOT_FOUND", "Khong tim thay user.", status_code=404)
        old = self._snapshot(item)
        updates = payload.model_dump(exclude_unset=True)
        if "role" in updates and updates["role"] is not None:
            self._validate_role(updates["role"])
            item.role = updates["role"]
        if "email" in updates:
            item.email = str(updates["email"]) if updates["email"] else None
        if updates.get("full_name") is not None:
            item.full_name = updates["full_name"].strip()
        if "is_active" in updates and updates["is_active"] is not None:
            item.is_active = bool(updates["is_active"])
            item.status = USER_STATUS_ACTIVE if item.is_active else USER_STATUS_DISABLED
        if updates.get("password"):
            item.password_hash = hash_password(updates["password"])

        new = self._snapshot(item)
        if old == new:
            return item
        try:
            AuditService(self.db).log(
                actor=actor,
                action="USER_UPDATED",
                resource_type="USER",
                resource_id=item.id,
                old_value=old,
                new_value=new,
                request=request,
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppException("USER_ALREADY_EXISTS", "Email da duoc user khac su dung.", status_code=409) from exc
        self.db.refresh(item)
        return item

    def deactivate_user(self, user_id: int, *, actor: User | None = None, request: Request | None = None) -> User:
        return self.update_user(user_id, UserUpdate(is_active=False), actor=actor, request=request)

    def approve_teacher(self, user_id: int, *, actor: User | None = None, request: Request | None = None) -> User:
        item = self.repo.get(user_id)
        if not item:
            raise AppException("RESOURCE_NOT_FOUND", "Khong tim thay user.", status_code=404)
        if item.role != ROLE_TEACHER:
            raise AppException("INVALID_USER_ROLE", "Chi co the duyet tai khoan giang vien.", status_code=400)
        old = self._snapshot(item)
        item.status = USER_STATUS_ACTIVE
        item.is_active = True
        new = self._snapshot(item)
        AuditService(self.db).log(
            actor=actor,
            action="TEACHER_APPROVED",
            resource_type="USER",
            resource_id=item.id,
            old_value=old,
            new_value=new,
            request=request,
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def disable_user(self, user_id: int, *, actor: User | None = None, request: Request | None = None) -> User:
        item = self.repo.get(user_id)
        if not item:
            raise AppException("RESOURCE_NOT_FOUND", "Khong tim thay user.", status_code=404)
        if actor and item.id == actor.id:
            raise AppException("CANNOT_DISABLE_SELF", "Admin khong the tu khoa tai khoan dang dang nhap.", status_code=400)
        if item.role == ROLE_ADMIN:
            raise AppException("CANNOT_DISABLE_ADMIN", "Khong the khoa tai khoan admin bang thao tac nay.", status_code=400)
        old = self._snapshot(item)
        item.status = USER_STATUS_DISABLED
        item.is_active = False
        new = self._snapshot(item)
        if old == new:
            return item
        AuditService(self.db).log(
            actor=actor,
            action="USER_DISABLED",
            resource_type="USER",
            resource_id=item.id,
            old_value=old,
            new_value=new,
            request=request,
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def _validate_role(self, role: str) -> None:
        if role not in ACTIVE_ROLES:
            raise AppException("INVALID_ROLE", "Role khong hop le.", status_code=400, details={"role": role})

    def _snapshot(self, item: User) -> dict[str, object]:
        return {
            "id": item.id,
            "username": item.username,
            "email": item.email,
            "full_name": item.full_name,
            "role": item.role,
            "is_active": item.is_active,
            "status": item.status,
        }
