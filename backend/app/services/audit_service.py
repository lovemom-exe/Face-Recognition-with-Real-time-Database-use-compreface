from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from ..models import AuditLog, User


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        *,
        actor: User | None,
        action: str,
        resource_type: str,
        resource_id: str | int | None = None,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        reason: str | None = None,
        request: Request | None = None,
        commit: bool = False,
    ) -> AuditLog:
        item = AuditLog(
            actor_user_id=actor.id if actor else None,
            actor_role=actor.role if actor else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, "request_id", None) if request else None,
        )
        self.db.add(item)
        if commit:
            self.db.commit()
            self.db.refresh(item)
        return item
