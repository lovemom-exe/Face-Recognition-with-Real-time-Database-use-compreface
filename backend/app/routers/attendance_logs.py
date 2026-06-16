from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..attendance_services import AttendanceLogService, BusinessRuleError
from ..api.deps import get_current_user
from ..database import get_db
from ..models import AttendanceLog, AttendanceSession, ClassCourse, User
from ..serializers import attendance_log_to_dict
from ..services.audit_service import AuditService
from ..services.permission_service import PermissionService

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
    current_user: User = Depends(get_current_user),
):
    query = db.query(AttendanceLog)
    if current_user.role not in {"ADMIN", "STAFF"}:
        assigned_class_ids = [assignment.class_id for assignment in current_user.teacher_assignments]
        query = query.join(AttendanceLog.session).join(AttendanceSession.class_course).filter(
            (ClassCourse.teacher_id == current_user.id) | (ClassCourse.class_id.in_(assigned_class_ids))
        )
    if session_id is not None:
        PermissionService(db).ensure_session(current_user, session_id)
        query = query.filter(AttendanceLog.session_id == session_id)
    if student_id is not None:
        query = query.filter(AttendanceLog.student_id == student_id)
    return [attendance_log_to_dict(item) for item in query.order_by(AttendanceLog.check_in_time.desc()).all()]


@router.post("/manual")
def create_manual_log(payload: ManualAttendanceIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        PermissionService(db).ensure_session(current_user, payload.session_id)
        result = AttendanceLogService(db).manual_attendance(
            session_id=payload.session_id,
            student_id=payload.student_id,
            status=payload.status,
            note=payload.note,
            actor_id=current_user.id,
            camera_id=payload.camera_id,
        )
        AuditService(db).log(
            actor=current_user,
            action="ATTENDANCE_MANUAL",
            resource_type="ATTENDANCE_LOG",
            resource_id=result.get("attendance_log", {}).get("id"),
            new_value=result.get("attendance_log"),
            commit=True,
        )
        return result
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.patch("/{log_id}")
def patch_log(log_id: int, payload: AttendanceLogUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        item = db.get(AttendanceLog, log_id)
        if not item:
            raise HTTPException(status_code=404, detail="Attendance log not found")
        PermissionService(db).ensure_session(current_user, item.session_id)
        result = AttendanceLogService(db).update_log(
            log_id=log_id,
            status=payload.status,
            note=payload.note,
            method=payload.method,
            reason=payload.reason,
            actor_id=current_user.id,
        )
        if result.get("status") != "NO_CHANGES":
            AuditService(db).log(
                actor=current_user,
                action="ATTENDANCE_LOG_UPDATED",
                resource_type="ATTENDANCE_LOG",
                resource_id=log_id,
                new_value=result.get("attendance_log"),
                reason=payload.reason,
                commit=True,
            )
        return result
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.put("/{log_id}")
def update_log(log_id: int, payload: AttendanceLogUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return patch_log(log_id, payload, db, current_user)


@router.get("/{log_id}/audits")
def log_audits(log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        item = db.get(AttendanceLog, log_id)
        if not item:
            raise HTTPException(status_code=404, detail="Attendance log not found")
        PermissionService(db).ensure_session(current_user, item.session_id)
        return AttendanceLogService(db).audits_for_log(log_id)
    except BusinessRuleError as exc:
        _raise_business_error(exc)
