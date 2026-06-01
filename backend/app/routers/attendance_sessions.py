from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AttendanceLog, AttendanceSession, Student
from ..serializers import attendance_log_to_dict, attendance_session_to_dict, student_to_dict

router = APIRouter(prefix="/api/attendance-sessions", tags=["attendance sessions"])


class AttendanceSessionIn(BaseModel):
    class_course_id: int
    created_by: int | None = None
    session_name: str
    start_time: datetime
    end_time: datetime | None = None
    late_threshold_minutes: int = 15
    status: str = "DRAFT"


class AttendanceSessionUpdate(BaseModel):
    session_name: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    late_threshold_minutes: int | None = None
    status: str | None = None


@router.get("")
def list_sessions(db: Session = Depends(get_db)):
    return [attendance_session_to_dict(item) for item in db.query(AttendanceSession).order_by(AttendanceSession.start_time.desc()).all()]


@router.get("/open")
def list_open_sessions(db: Session = Depends(get_db)):
    return [
        attendance_session_to_dict(item)
        for item in db.query(AttendanceSession)
        .filter(AttendanceSession.status == "OPEN")
        .order_by(AttendanceSession.start_time.desc())
        .all()
    ]


@router.post("")
def create_session(payload: AttendanceSessionIn, db: Session = Depends(get_db)):
    item = AttendanceSession(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return attendance_session_to_dict(item)


@router.get("/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    item = db.get(AttendanceSession, session_id)
    if not item:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    return attendance_session_to_dict(item)


@router.put("/{session_id}")
def update_session(session_id: int, payload: AttendanceSessionUpdate, db: Session = Depends(get_db)):
    item = db.get(AttendanceSession, session_id)
    if not item:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return attendance_session_to_dict(item)


@router.post("/{session_id}/open")
def open_session(session_id: int, db: Session = Depends(get_db)):
    item = db.get(AttendanceSession, session_id)
    if not item:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    item.status = "OPEN"
    db.commit()
    db.refresh(item)
    return attendance_session_to_dict(item)


@router.post("/{session_id}/close")
def close_session(session_id: int, db: Session = Depends(get_db)):
    item = db.get(AttendanceSession, session_id)
    if not item:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    item.status = "CLOSED"
    item.end_time = item.end_time or datetime.utcnow()
    db.commit()
    db.refresh(item)
    return attendance_session_to_dict(item)


@router.get("/{session_id}/results")
def session_results(session_id: int, db: Session = Depends(get_db)):
    item = db.get(AttendanceSession, session_id)
    if not item:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    return {
        "session": attendance_session_to_dict(item),
        "attendance_logs": [attendance_log_to_dict(log) for log in item.attendance_logs],
    }


@router.get("/{session_id}/roster")
def session_roster(session_id: int, db: Session = Depends(get_db)):
    item = db.get(AttendanceSession, session_id)
    if not item:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    class_id = item.class_course.class_id
    logs = {
        log.student_id: log
        for log in db.query(AttendanceLog).filter(AttendanceLog.session_id == session_id).all()
    }
    students = db.query(Student).filter(Student.class_id == class_id, Student.status == "ACTIVE").order_by(Student.full_name).all()
    return {
        "session": attendance_session_to_dict(item),
        "students": [
            {
                **student_to_dict(student),
                "attendance_log": attendance_log_to_dict(logs[student.id]) if student.id in logs else None,
                "attendance_status": logs[student.id].status if student.id in logs else "ABSENT",
            }
            for student in students
        ],
    }
