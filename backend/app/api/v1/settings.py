from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ...api.deps import require_admin
from ...database import get_db
from ...models import User
from ...schemas.setting import SettingOut, SettingUpdate
from ...services.settings_service import SettingsService

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("", response_model=list[SettingOut])
def list_settings(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    service = SettingsService(db)
    return [service.mask(item) for item in service.list_settings()]


@router.get("/{key}", response_model=SettingOut)
def get_setting(key: str, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    service = SettingsService(db)
    return service.mask(service.get_setting(key))


@router.patch("/{key}", response_model=SettingOut)
def update_setting(
    key: str,
    payload: SettingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return SettingsService(db).update_setting(key, payload.value, actor=current_user, reason=payload.reason, request=request)
