from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..attendance_services import AttendanceLogService, AttendanceSessionService, BusinessRuleError
from ..api.deps import get_current_user
from ..database import get_db
from ..models import AttendanceLog, AttendanceSession, ClassCourse, User
from ..serializers import attendance_log_to_dict, attendance_session_to_dict
from ..services.permission_service import PermissionService

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


class ManualAttendanceIn(BaseModel):
    student_id: int
    status: str | None = "MANUAL"
    note: str = ""
    actor_id: int | None = None
    camera_id: int | None = None


def _raise_business_error(exc: BusinessRuleError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


def _session_scope_query(db: Session, current_user: User):
    query = db.query(AttendanceSession)
    if current_user.role in {"ADMIN", "STAFF"}:
        return query
    assigned_class_ids = [assignment.class_id for assignment in current_user.teacher_assignments]
    return query.join(AttendanceSession.class_course).filter(
        (ClassCourse.teacher_id == current_user.id) | (ClassCourse.class_id.in_(assigned_class_ids))
    )


@router.get("")
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [
        attendance_session_to_dict(item)
        for item in _session_scope_query(db, current_user).order_by(AttendanceSession.start_time.desc()).all()
    ]


@router.get("/open")
def list_open_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [
        attendance_session_to_dict(item)
        for item in _session_scope_query(db, current_user)
        .filter(AttendanceSession.status == "OPEN")
        .order_by(AttendanceSession.start_time.desc())
        .all()
    ]


@router.post("")
def create_session(payload: AttendanceSessionIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    PermissionService(db).ensure_class_course(current_user, payload.class_course_id)
    data = payload.model_dump()
    data["created_by"] = current_user.id
    item = AttendanceSession(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return attendance_session_to_dict(item)


@router.get("/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.get(AttendanceSession, session_id)
    if not item:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    PermissionService(db).ensure_class_course(current_user, item.class_course_id)
    return attendance_session_to_dict(item)


@router.put("/{session_id}")
def update_session(session_id: int, payload: AttendanceSessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.get(AttendanceSession, session_id)
    if not item:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    PermissionService(db).ensure_class_course(current_user, item.class_course_id)
    updates = payload.model_dump(exclude_unset=True)
    next_status = updates.pop("status", None)
    if next_status is not None and next_status != item.status:
        raise HTTPException(status_code=400, detail="Vui lòng dùng endpoint lifecycle để đổi trạng thái buổi điểm danh.")
    for key, value in updates.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return attendance_session_to_dict(item)


@router.post("/{session_id}/open")
def open_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        PermissionService(db).ensure_session(current_user, session_id)
        return AttendanceSessionService(db).open(session_id)
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.post("/{session_id}/close")
def close_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        PermissionService(db).ensure_session(current_user, session_id)
        return AttendanceSessionService(db).close(session_id)
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.post("/{session_id}/lock")
def lock_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        PermissionService(db).ensure_session(current_user, session_id)
        return AttendanceSessionService(db).lock(session_id)
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.post("/{session_id}/reopen")
def reopen_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        PermissionService(db).ensure_session(current_user, session_id)
        return AttendanceSessionService(db).reopen(session_id)
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.post("/{session_id}/cancel")
def cancel_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        PermissionService(db).ensure_session(current_user, session_id)
        return AttendanceSessionService(db).cancel(session_id)
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.get("/{session_id}/results")
def session_results(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.get(AttendanceSession, session_id)
    if not item:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    PermissionService(db).ensure_class_course(current_user, item.class_course_id)
    return {
        "session": attendance_session_to_dict(item),
        "attendance_logs": [attendance_log_to_dict(log) for log in item.attendance_logs],
    }


@router.get("/{session_id}/roster")
def session_roster(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        PermissionService(db).ensure_session(current_user, session_id)
        return AttendanceSessionService(db).roster(session_id)
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.post("/{session_id}/manual-attendance")
def manual_attendance(session_id: int, payload: ManualAttendanceIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        PermissionService(db).ensure_session(current_user, session_id)
        return AttendanceLogService(db).manual_attendance(
            session_id=session_id,
            student_id=payload.student_id,
            status=payload.status,
            note=payload.note,
            actor_id=current_user.id,
            camera_id=payload.camera_id,
        )
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.get("/{session_id}/audits")
def session_audits(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        PermissionService(db).ensure_session(current_user, session_id)
        return AttendanceSessionService(db).audits(session_id)
    except BusinessRuleError as exc:
        _raise_business_error(exc)
