from __future__ import annotations

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.config import settings


class HealthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def db_health(self) -> dict[str, object]:
        self.db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}

    def compreface_health(self) -> dict[str, object]:
        try:
            response = requests.get(settings.compreface_base_url, timeout=3)
            return {"status": "ok" if response.status_code < 500 else "degraded", "status_code": response.status_code}
        except requests.RequestException as exc:
            return {"status": "unreachable", "error": str(exc)}
