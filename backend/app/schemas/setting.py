from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SettingUpdate(BaseModel):
    value: str
    reason: str | None = None


class SettingOut(BaseModel):
    id: int
    key: str
    value: str
    value_type: str
    description: str | None = None
    is_sensitive: bool
    updated_by: int | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}
