from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import SystemSetting


class SettingsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_key(self, key: str) -> SystemSetting | None:
        return self.db.query(SystemSetting).filter(SystemSetting.key == key).first()

    def list(self) -> list[SystemSetting]:
        return self.db.query(SystemSetting).order_by(SystemSetting.key).all()
