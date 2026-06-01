from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..models import AttendanceLog, AttendanceSession, Student
from ..serializers import attendance_log_to_dict
from ..services import attendance_status_for

router = APIRouter(prefix="/api/attendance-logs", tags=["attendance logs"])


class ManualAttendanceIn(BaseModel):
    session_id: int
    student_id: int
    camera_id: int | None = None
    status: str | None = None
    note: str = ""


class AttendanceLogUpdate(BaseModel):
    status: str | None = None
    note: str | None = None


@router.get("")
def list_logs(
    session_id: int | None = None,
    student_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(AttendanceLog)
    if session_id is not None:
        query = query.filter(AttendanceLog.session_id == session_id)
    if student_id is not None:
        query = query.filter(AttendanceLog.student_id == student_id)
    return [attendance_log_to_dict(item) for item in query.order_by(AttendanceLog.check_in_time.desc()).all()]


@router.post("/manual")
def create_manual_log(payload: ManualAttendanceIn, db: Session = Depends(get_db)):
    session = db.get(AttendanceSession, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    if session.status != "OPEN":
        raise HTTPException(status_code=400, detail="Buổi điểm danh chưa được mở hoặc đã đóng.")
    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên.")
    if student.class_id != session.class_course.class_id:
        raise HTTPException(status_code=400, detail="Sinh viên không thuộc lớp của buổi điểm danh này.")
    status = payload.status or attendance_status_for(session, datetime.utcnow())
    item = AttendanceLog(
        session_id=payload.session_id,
        student_id=payload.student_id,
        camera_id=payload.camera_id,
        status=status,
        note=payload.note,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(AttendanceLog).filter(
            AttendanceLog.session_id == payload.session_id,
            AttendanceLog.student_id == payload.student_id,
        ).first()
        if existing:
            existing.status = status
            existing.note = payload.note
            db.commit()
            db.refresh(existing)
            return attendance_log_to_dict(existing)
        raise
    db.refresh(item)
    return attendance_log_to_dict(item)


@router.put("/{log_id}")
def update_log(log_id: int, payload: AttendanceLogUpdate, db: Session = Depends(get_db)):
    item = db.get(AttendanceLog, log_id)
    if not item:
        raise HTTPException(status_code=404, detail="Attendance log not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return attendance_log_to_dict(item)
