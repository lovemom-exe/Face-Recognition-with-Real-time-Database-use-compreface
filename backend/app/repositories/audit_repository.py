from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..models import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        *,
        actor_user_id: int | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        query = self.db.query(AuditLog)
        if actor_user_id is not None:
            query = query.filter(AuditLog.actor_user_id == actor_user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if from_time:
            query = query.filter(AuditLog.created_at >= from_time)
        if to_time:
            query = query.filter(AuditLog.created_at <= to_time)
        return query.order_by(AuditLog.created_at.desc()).limit(min(limit, 500)).all()
