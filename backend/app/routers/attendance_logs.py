from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..attendance_services import AttendanceLogService, BusinessRuleError
from ..database import get_db
from ..models import AttendanceLog
from ..serializers import attendance_log_to_dict

router = APIRouter(prefix="/api/attendance-logs", tags=["attendance logs"])


class ManualAttendanceIn(BaseModel):
    session_id: int
    student_id: int
    camera_id: int | None = None
    status: str | None = "MANUAL"
    note: str = ""
    actor_id: int | None = None


class AttendanceLogUpdate(BaseModel):
    status: str | None = None
    note: str | None = None
    method: str | None = None
    reason: str | None = None
    actor_id: int | None = None


def _raise_business_error(exc: BusinessRuleError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


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
    try:
        return AttendanceLogService(db).manual_attendance(
            session_id=payload.session_id,
            student_id=payload.student_id,
            status=payload.status,
            note=payload.note,
            actor_id=payload.actor_id,
            camera_id=payload.camera_id,
        )
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.patch("/{log_id}")
def patch_log(log_id: int, payload: AttendanceLogUpdate, db: Session = Depends(get_db)):
    try:
        return AttendanceLogService(db).update_log(
            log_id=log_id,
            status=payload.status,
            note=payload.note,
            method=payload.method,
            reason=payload.reason,
            actor_id=payload.actor_id,
        )
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.put("/{log_id}")
def update_log(log_id: int, payload: AttendanceLogUpdate, db: Session = Depends(get_db)):
    return patch_log(log_id, payload, db)


@router.get("/{log_id}/audits")
def log_audits(log_id: int, db: Session = Depends(get_db)):
    try:
        return AttendanceLogService(db).audits_for_log(log_id)
    except BusinessRuleError as exc:
        _raise_business_error(exc)
