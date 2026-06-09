from __future__ import annotations

from backend.app.services.audit_service import AuditService


def test_audit_service_creates_log(db_session, admin_user):
    item = AuditService(db_session).log(
        actor=admin_user,
        action="TEST_ACTION",
        resource_type="TEST",
        resource_id="1",
        new_value={"ok": True},
        commit=True,
    )
    assert item.id is not None
    assert item.actor_user_id == admin_user.id
