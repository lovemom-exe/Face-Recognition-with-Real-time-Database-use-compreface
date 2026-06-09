from __future__ import annotations

from backend.app.services.settings_service import SettingsService


def test_settings_defaults_are_seeded(db_session):
    service = SettingsService(db_session)
    service.ensure_defaults()
    keys = {item.key for item in service.list_settings()}
    assert "recognition_threshold" in keys
    assert "allow_manual_attendance" in keys
