from __future__ import annotations

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Face Attendance System"
    debug: bool = True

    database_url: str = Field(default="sqlite:///backend_attendance.db", validation_alias="DATABASE_URL")

    jwt_secret_key: str = "change-me-generate-with-secrets-token-urlsafe"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    password_pepper: str = "change-me-random-pepper"

    compreface_base_url: str = "http://localhost:8000"
    compreface_api_key: str = ""
    compreface_recognition_api_key: str = Field(default="", validation_alias="COMPREFACE_RECOGNITION_API_KEY")

    cors_allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    max_image_upload_mb: int = 5
    max_csv_upload_mb: int = 10
    backup_dir: str = "./backups"

    recognition_threshold: float = Field(default=0.97, validation_alias="ATTENDANCE_RECOGNITION_THRESHOLD")
    allowed_teacher_email_domains: list[str] = Field(
        default_factory=lambda: ["hust.edu.vn"],
        validation_alias="ALLOWED_TEACHER_EMAIL_DOMAINS",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return value
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("allowed_teacher_email_domains", mode="before")
    @classmethod
    def parse_teacher_email_domains(cls, value: object) -> list[str]:
        if isinstance(value, str):
            items = value.split(",")
        elif isinstance(value, list):
            items = value
        else:
            items = ["hust.edu.vn"]
        domains = []
        for item in items:
            domain = str(item).strip().lower()
            if domain.startswith("@"):
                domain = domain[1:]
            if domain:
                domains.append(domain)
        return domains or ["hust.edu.vn"]

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on", "debug", "development", "dev"}:
            return True
        if text in {"0", "false", "no", "off", "release", "production", "prod"}:
            return False
        return False

    @field_validator("compreface_api_key", mode="before")
    @classmethod
    def normalize_compreface_api_key(cls, value: object) -> str:
        return str(value or "")

    @property
    def effective_compreface_api_key(self) -> str:
        return self.compreface_api_key or self.compreface_recognition_api_key

    @model_validator(mode="after")
    def fill_legacy_compreface_key(self) -> "Settings":
        if not self.compreface_recognition_api_key and self.compreface_api_key:
            self.compreface_recognition_api_key = self.compreface_api_key
        if not self.compreface_api_key and self.compreface_recognition_api_key:
            self.compreface_api_key = self.compreface_recognition_api_key
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


settings = Settings()
