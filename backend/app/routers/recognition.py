from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..serializers import attendance_log_to_dict, recognition_event_to_dict
from ..services import RecognitionService

router = APIRouter(prefix="/api/recognition", tags=["recognition"])


class ConfirmRecognitionIn(BaseModel):
    recognition_event_id: int | None = None
    session_id: int | None = None
    student_id: int | None = None
    camera_id: int | None = None
    note: str | None = None


@router.post("/image")
async def recognize_image(
    file: UploadFile = File(...),
    session_id: int | None = Form(default=None),
    camera_id: int | None = Form(default=None),
    threshold: float | None = Form(default=None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    result = RecognitionService(db).recognize_and_log(
        file_name=file.filename or "frame.jpg",
        content=content,
        session_id=session_id,
        camera_id=camera_id,
        threshold=threshold,
    )
    return {
        "events": [recognition_event_to_dict(event) for event in result["events"]],
        "attendance_logs": [attendance_log_to_dict(log) for log in result["attendance_logs"]],
        "detections": result["detections"],
        "recognized": result.get("recognized"),
        "similarity": result.get("similarity"),
        "subject": result.get("subject"),
        "student_id": result.get("student_id"),
        "student_code": result.get("student_code"),
        "student_name": result.get("student_name"),
        "class_id": result.get("class_id"),
        "class_name": result.get("class_name"),
        "course_name": result.get("course_name"),
        "session_id": result.get("session_id"),
        "belongs_to_session_class": result.get("belongs_to_session_class"),
        "status": result.get("status"),
        "message": result.get("message"),
        "event_id": result.get("event_id"),
    }


@router.post("/confirm")
def confirm_recognition(payload: ConfirmRecognitionIn, db: Session = Depends(get_db)):
    return RecognitionService(db).confirm_attendance(
        recognition_event_id=payload.recognition_event_id,
        session_id=payload.session_id,
        student_id=payload.student_id,
        camera_id=payload.camera_id,
        note=payload.note,
    )


@router.post("/{recognition_event_id}/reject")
def reject_recognition(recognition_event_id: int, db: Session = Depends(get_db)):
    return RecognitionService(db).reject_recognition(recognition_event_id)
