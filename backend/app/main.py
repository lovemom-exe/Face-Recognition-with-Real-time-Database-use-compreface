from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from .config import settings
from .api.deps import get_current_user
from .api.v1 import audit_logs, auth, health as health_v1, settings as settings_api, teacher_assignments, users
from .core.exceptions import register_exception_handlers
from .core.logging_config import configure_logging
from .database import init_db
from .database import SessionLocal
from .middleware.rate_limit_middleware import limiter
from .middleware.request_id_middleware import RequestIdMiddleware
from .middleware.request_logging_middleware import RequestLoggingMiddleware
from .middleware.security_headers_middleware import SecurityHeadersMiddleware
from .routers import attendance_logs, attendance_sessions, cameras, classes, compreface, courses, face_profiles, recognition, reports, students
from .services.settings_service import SettingsService


configure_logging(settings.debug)
app = FastAPI(title=settings.app_name)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
register_exception_handlers(app)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        SettingsService(db).ensure_defaults()
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}


app.include_router(auth.router)
app.include_router(health_v1.router)
app.include_router(users.router)
app.include_router(teacher_assignments.router)
app.include_router(audit_logs.router)
app.include_router(settings_api.router)

protected_dependencies = [Depends(get_current_user)]
app.include_router(classes.router, dependencies=protected_dependencies)
app.include_router(students.router, dependencies=protected_dependencies)
app.include_router(courses.router, dependencies=protected_dependencies)
app.include_router(cameras.router, dependencies=protected_dependencies)
app.include_router(compreface.router, dependencies=protected_dependencies)
app.include_router(face_profiles.router, dependencies=protected_dependencies)
app.include_router(attendance_sessions.router, dependencies=protected_dependencies)
app.include_router(recognition.router, dependencies=protected_dependencies)
app.include_router(attendance_logs.router, dependencies=protected_dependencies)
app.include_router(reports.router, dependencies=protected_dependencies)
