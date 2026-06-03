from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import attendance_logs, attendance_sessions, cameras, classes, compreface, courses, face_profiles, recognition, reports, students


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}


app.include_router(classes.router)
app.include_router(students.router)
app.include_router(courses.router)
app.include_router(cameras.router)
app.include_router(compreface.router)
app.include_router(face_profiles.router)
app.include_router(attendance_sessions.router)
app.include_router(recognition.router)
app.include_router(attendance_logs.router)
app.include_router(reports.router)
