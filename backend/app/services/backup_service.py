from __future__ import annotations

from pathlib import Path

from ..core.config import settings


class BackupService:
    def backup_dir(self) -> Path:
        path = Path(settings.backup_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
