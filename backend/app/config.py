from __future__ import annotations

import os


class Settings:
    app_name = "Face Attendance MVP API"
    database_url = os.environ.get("BACKEND_DATABASE_URL", "sqlite:///backend_attendance.db")
    compreface_base_url = os.environ.get("COMPREFACE_BASE_URL", "http://localhost:8000")
    compreface_recognition_api_key = os.environ.get(
        "COMPREFACE_RECOGNITION_API_KEY",
        "",
    )
    recognition_threshold = float(os.environ.get("ATTENDANCE_RECOGNITION_THRESHOLD", "0.75"))


settings = Settings()
