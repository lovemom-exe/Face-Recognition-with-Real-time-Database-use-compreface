from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...api.deps import require_admin
from ...database import get_db
from ...models import User
from ...repositories.audit_repository import AuditRepository
from ...schemas.audit_log import AuditLogOut

router = APIRouter(prefix="/api/v1/audit-logs", tags=["audit logs"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    actor_user_id: int | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return AuditRepository(db).list(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        from_time=from_time,
        to_time=to_time,
        limit=limit,
    )
