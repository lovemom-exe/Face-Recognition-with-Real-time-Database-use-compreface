from __future__ import annotations


ROLE_ADMIN = "ADMIN"
ROLE_TEACHER = "TEACHER"
ROLE_STAFF = "STAFF"
ROLE_STUDENT = "STUDENT"

ACTIVE_ROLES = {ROLE_ADMIN, ROLE_TEACHER, ROLE_STAFF, ROLE_STUDENT}

USER_STATUS_PENDING = "PENDING"
USER_STATUS_ACTIVE = "ACTIVE"
USER_STATUS_DISABLED = "DISABLED"
ACTIVE_USER_STATUSES = {USER_STATUS_PENDING, USER_STATUS_ACTIVE, USER_STATUS_DISABLED}

SESSION_OPEN = "OPEN"
SESSION_CLOSED = "CLOSED"
SESSION_LOCKED = "LOCKED"
SESSION_CANCELLED = "CANCELLED"

SETTING_DEFAULTS: dict[str, dict[str, object]] = {
    "recognition_threshold": {
        "value": "0.97",
        "value_type": "float",
        "description": "Nguong similarity mac dinh cho nhan dien khuon mat.",
        "is_sensitive": False,
    },
    "liveness_threshold": {
        "value": "0.50",
        "value_type": "float",
        "description": "Nguong liveness neu he thong co bat chong gia mao.",
        "is_sensitive": False,
    },
    "late_threshold_default": {
        "value": "15",
        "value_type": "int",
        "description": "So phut mac dinh de tinh di muon.",
        "is_sensitive": False,
    },
    "max_image_upload_mb": {
        "value": "5",
        "value_type": "int",
        "description": "Dung luong toi da cho anh upload.",
        "is_sensitive": False,
    },
    "max_csv_upload_mb": {
        "value": "10",
        "value_type": "int",
        "description": "Dung luong toi da cho file CSV.",
        "is_sensitive": False,
    },
    "allow_manual_attendance": {
        "value": "true",
        "value_type": "bool",
        "description": "Cho phep giang vien diem danh thu cong.",
        "is_sensitive": False,
    },
    "auto_mark_absent_on_close": {
        "value": "true",
        "value_type": "bool",
        "description": "Tu dong danh vang sinh vien chua co log khi dong session.",
        "is_sensitive": False,
    },
    "session_auto_lock_after_days": {
        "value": "7",
        "value_type": "int",
        "description": "So ngay goi y khoa session sau khi dong.",
        "is_sensitive": False,
    },
    "export_school_name": {
        "value": "Face Attendance System",
        "value_type": "string",
        "description": "Ten don vi hien trong file export.",
        "is_sensitive": False,
    },
    "export_template": {
        "value": "default",
        "value_type": "string",
        "description": "Mau export dang su dung.",
        "is_sensitive": False,
    },
}
