from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from ..core.constants import SETTING_DEFAULTS
from ..core.exceptions import AppException
from ..models import SystemSetting, User
from ..repositories.settings_repository import SettingsRepository
from .audit_service import AuditService


class SettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SettingsRepository(db)

    def ensure_defaults(self) -> None:
        changed = False
        for key, meta in SETTING_DEFAULTS.items():
            if self.repo.get_by_key(key):
                continue
            self.db.add(SystemSetting(key=key, **meta))
            changed = True
        if changed:
            self.db.commit()

    def list_settings(self) -> list[SystemSetting]:
        self.ensure_defaults()
        return self.repo.list()

    def get_setting(self, key: str) -> SystemSetting:
        self.ensure_defaults()
        item = self.repo.get_by_key(key)
        if not item:
            raise AppException("RESOURCE_NOT_FOUND", "Khong tim thay cau hinh he thong.", status_code=404)
        return item

    def update_setting(self, key: str, value: str, *, actor: User, reason: str | None, request: Request | None = None) -> SystemSetting:
        item = self.get_setting(key)
        old = {"value": item.value}
        if item.value == value:
            return item
        item.value = value
        item.updated_by = actor.id
        AuditService(self.db).log(
            actor=actor,
            action="SETTING_UPDATED",
            resource_type="SYSTEM_SETTING",
            resource_id=key,
            old_value=old,
            new_value={"value": "***" if item.is_sensitive else value},
            reason=reason,
            request=request,
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def mask(self, item: SystemSetting) -> SystemSetting:
        if item.is_sensitive:
            item.value = "***"
        return item
