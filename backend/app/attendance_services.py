from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import (
    AttendanceLog,
    AttendanceLogAudit,
    AttendanceSession,
    Student,
)
from .serializers import (
    attendance_log_audit_to_dict,
    attendance_log_to_dict,
    attendance_session_to_dict,
    dt,
    student_to_dict,
)


SESSION_DRAFT = "DRAFT"
SESSION_OPEN = "OPEN"
SESSION_CLOSED = "CLOSED"
SESSION_LOCKED = "LOCKED"
SESSION_CANCELLED = "CANCELLED"

ATTENDANCE_ON_TIME = "ON_TIME"
ATTENDANCE_LATE = "LATE"
ATTENDANCE_ABSENT = "ABSENT"
ATTENDANCE_EXCUSED = "EXCUSED"
ATTENDANCE_MANUAL = "MANUAL"
ATTENDANCE_PENDING_REVIEW = "PENDING_REVIEW"
ATTENDANCE_INVALID = "INVALID"

METHOD_FACE = "FACE"
METHOD_MANUAL = "MANUAL"
METHOD_AUTO_ABSENT = "AUTO_ABSENT"
METHOD_NONE = "NONE"

VALID_ATTENDANCE_STATUSES = {
    ATTENDANCE_ON_TIME,
    ATTENDANCE_LATE,
    ATTENDANCE_ABSENT,
    ATTENDANCE_EXCUSED,
    ATTENDANCE_MANUAL,
    ATTENDANCE_PENDING_REVIEW,
    ATTENDANCE_INVALID,
}
VALID_ATTENDANCE_METHODS = {METHOD_FACE, METHOD_MANUAL, METHOD_AUTO_ABSENT}
EDITABLE_SESSION_STATUSES = {SESSION_OPEN, SESSION_CLOSED}


class BusinessRuleError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def as_dict(self) -> dict[str, Any]:
        return {"ok": False, "status": self.code, "message": self.message, **self.payload}


def attendance_status_for(session: AttendanceSession, at_time: datetime) -> str:
    deadline = session.start_time + timedelta(minutes=session.late_threshold_minutes)
    return ATTENDANCE_LATE if at_time > deadline else ATTENDANCE_ON_TIME


class AttendanceSessionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def open(self, session_id: int) -> dict[str, Any]:
        session = self._get_session(session_id)
        if session.status not in {SESSION_DRAFT, SESSION_CLOSED}:
            raise BusinessRuleError("INVALID_SESSION_TRANSITION", "Chỉ buổi DRAFT hoặc CLOSED mới được mở.")
        session.status = SESSION_OPEN
        session.end_time = None
        self._commit()
        self.db.refresh(session)
        return {"ok": True, "message": "Đã mở buổi điểm danh.", "session": attendance_session_to_dict(session)}

    def close(self, session_id: int) -> dict[str, Any]:
        session = self._get_session(session_id)
        if session.status == SESSION_CLOSED:
            return {
                "ok": True,
                "message": "Buổi điểm danh đã đóng, không tạo thêm log vắng.",
                "session": attendance_session_to_dict(session),
                "summary": self.summary(session, created_absent_logs=0),
            }
        if session.status in {SESSION_LOCKED, SESSION_CANCELLED}:
            raise BusinessRuleError("SESSION_NOT_EDITABLE", "Buổi điểm danh đã bị khóa hoặc đã hủy, không thể đóng.")
        if session.status != SESSION_OPEN:
            raise BusinessRuleError("SESSION_NOT_OPEN", "Chỉ buổi đang OPEN mới được đóng.")

        created_absent_logs = self._add_missing_absent_logs(session)
        session.status = SESSION_CLOSED
        session.end_time = session.end_time or datetime.utcnow()
        self._commit()
        self.db.refresh(session)
        return {
            "ok": True,
            "message": "Đã đóng buổi điểm danh.",
            "session": attendance_session_to_dict(session),
            "summary": self.summary(session, created_absent_logs=created_absent_logs),
        }

    def lock(self, session_id: int) -> dict[str, Any]:
        session = self._get_session(session_id)
        if session.status != SESSION_CLOSED:
            raise BusinessRuleError("INVALID_SESSION_TRANSITION", "Chỉ buổi CLOSED mới được khóa.")
        session.status = SESSION_LOCKED
        self._commit()
        self.db.refresh(session)
        return {"ok": True, "message": "Đã khóa buổi điểm danh.", "session": attendance_session_to_dict(session)}

    def reopen(self, session_id: int) -> dict[str, Any]:
        session = self._get_session(session_id)
        if session.status != SESSION_CLOSED:
            raise BusinessRuleError("INVALID_SESSION_TRANSITION", "Chỉ buổi CLOSED mới được mở lại.")
        session.status = SESSION_OPEN
        session.end_time = None
        self._commit()
        self.db.refresh(session)
        return {"ok": True, "message": "Đã mở lại buổi điểm danh.", "session": attendance_session_to_dict(session)}

    def cancel(self, session_id: int) -> dict[str, Any]:
        session = self._get_session(session_id)
        if session.status == SESSION_LOCKED:
            raise BusinessRuleError("SESSION_LOCKED", "Buổi điểm danh đã khóa, không thể hủy.")
        if session.status == SESSION_CANCELLED:
            return {"ok": True, "message": "Buổi điểm danh đã được hủy.", "session": attendance_session_to_dict(session)}
        log_count = self.db.query(AttendanceLog).filter(AttendanceLog.session_id == session.id).count()
        if log_count:
            raise BusinessRuleError("SESSION_HAS_ATTENDANCE_LOGS", "Buổi điểm danh đã có log, không thể hủy.")
        session.status = SESSION_CANCELLED
        self._commit()
        self.db.refresh(session)
        return {"ok": True, "message": "Đã hủy buổi điểm danh.", "session": attendance_session_to_dict(session)}

    def roster(self, session_id: int) -> dict[str, Any]:
        session = self._get_session(session_id)
        students = self._session_students(session)
        logs = {
            log.student_id: log
            for log in self.db.query(AttendanceLog).filter(AttendanceLog.session_id == session.id).all()
        }
        return {
            "session": attendance_session_to_dict(session),
            "students": [self._roster_item(student, logs.get(student.id)) for student in students],
            "summary": self.summary(session),
        }

    def audits(self, session_id: int) -> dict[str, Any]:
        session = self._get_session(session_id)
        audits = (
            self.db.query(AttendanceLogAudit)
            .filter(AttendanceLogAudit.session_id == session.id)
            .order_by(AttendanceLogAudit.changed_at.desc())
            .all()
        )
        return {"session": attendance_session_to_dict(session), "audits": [attendance_log_audit_to_dict(item) for item in audits]}

    def summary(self, session: AttendanceSession, created_absent_logs: int = 0) -> dict[str, Any]:
        total_students = len(self._session_students(session))
        logs = self.db.query(AttendanceLog).filter(AttendanceLog.session_id == session.id).all()
        counts = {status: 0 for status in VALID_ATTENDANCE_STATUSES}
        method_counts = {method: 0 for method in VALID_ATTENDANCE_METHODS}
        for log in logs:
            counts[log.status] = counts.get(log.status, 0) + 1
            method = getattr(log, "method", None) or METHOD_FACE
            method_counts[method] = method_counts.get(method, 0) + 1
        return {
            "total_students": total_students,
            "total_logs": len(logs),
            "created_absent_logs": created_absent_logs,
            "on_time": counts.get(ATTENDANCE_ON_TIME, 0),
            "late": counts.get(ATTENDANCE_LATE, 0),
            "absent": counts.get(ATTENDANCE_ABSENT, 0),
            "excused": counts.get(ATTENDANCE_EXCUSED, 0),
            "manual": counts.get(ATTENDANCE_MANUAL, 0),
            "pending_review": counts.get(ATTENDANCE_PENDING_REVIEW, 0),
            "invalid": counts.get(ATTENDANCE_INVALID, 0),
            "not_recorded": max(total_students - len(logs), 0),
            "methods": method_counts,
        }

    def _add_missing_absent_logs(self, session: AttendanceSession) -> int:
        students = self._session_students(session)
        existing_student_ids = {
            row[0]
            for row in self.db.query(AttendanceLog.student_id).filter(AttendanceLog.session_id == session.id).all()
        }
        created = 0
        for student in students:
            if student.id in existing_student_ids:
                continue
            self.db.add(
                AttendanceLog(
                    session_id=session.id,
                    student_id=student.id,
                    status=ATTENDANCE_ABSENT,
                    method=METHOD_AUTO_ABSENT,
                    similarity=0.0,
                    note="Tự động đánh vắng khi đóng buổi điểm danh",
                )
            )
            created += 1
        return created

    def _session_students(self, session: AttendanceSession) -> list[Student]:
        if not session.class_course:
            raise BusinessRuleError("SESSION_CLASS_NOT_FOUND", "Buổi điểm danh chưa gắn với lớp học hợp lệ.")
        return (
            self.db.query(Student)
            .filter(Student.class_id == session.class_course.class_id, Student.status == "ACTIVE")
            .order_by(Student.full_name)
            .all()
        )

    def _roster_item(self, student: Student, log: AttendanceLog | None) -> dict[str, Any]:
        if not log:
            return {
                "student_id": student.id,
                "student_code": student.student_code,
                "full_name": student.full_name,
                "class_id": student.class_id,
                "class_name": student.study_class.class_name if student.study_class else None,
                "attendance_log_id": None,
                "attendance_status": "NOT_RECORDED",
                "check_in_time": None,
                "similarity": 0.0,
                "method": METHOD_NONE,
                "note": "",
                "recognition_event_id": None,
                "student": student_to_dict(student),
                "attendance_log": None,
            }
        log_payload = attendance_log_to_dict(log)
        return {
            "student_id": student.id,
            "student_code": student.student_code,
            "full_name": student.full_name,
            "class_id": student.class_id,
            "class_name": student.study_class.class_name if student.study_class else None,
            "attendance_log_id": log.id,
            "attendance_status": log.status,
            "check_in_time": dt(log.check_in_time),
            "similarity": log.similarity,
            "method": getattr(log, "method", None) or METHOD_FACE,
            "note": log.note,
            "recognition_event_id": log.recognition_event_id,
            "student": student_to_dict(student),
            "attendance_log": log_payload,
        }

    def _get_session(self, session_id: int) -> AttendanceSession:
        session = self.db.get(AttendanceSession, session_id)
        if not session:
            raise BusinessRuleError("SESSION_NOT_FOUND", "Không tìm thấy buổi điểm danh.", status_code=404)
        return session

    def _commit(self) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise


class AttendanceLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def confirm_from_recognition(
        self,
        *,
        session_id: int,
        student_id: int,
        recognition_event: Any | None = None,
        camera_id: int | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        session = self._get_session(session_id)
        if session.status != SESSION_OPEN:
            raise BusinessRuleError("SESSION_NOT_OPEN", "Buổi điểm danh chưa được mở hoặc đã đóng.")

        student = self._get_student(student_id)
        self._ensure_student_in_session(student, session)

        existing = self._existing_log(session.id, student.id)
        if existing:
            return self._already_attended(existing, student)

        now = datetime.utcnow()
        log = AttendanceLog(
            session_id=session.id,
            student_id=student.id,
            camera_id=camera_id or (recognition_event.camera_id if recognition_event else None),
            recognition_event_id=recognition_event.id if recognition_event else None,
            check_in_time=now,
            status=attendance_status_for(session, now),
            method=METHOD_FACE,
            similarity=recognition_event.similarity if recognition_event else 0.0,
            note=note or "Giảng viên xác nhận từ trạm camera",
        )
        self.db.add(log)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = self._existing_log(session.id, student.id)
            if existing:
                return self._already_attended(existing, student)
            raise BusinessRuleError("ATTENDANCE_LOG_CONFLICT", "Không thể ghi điểm danh do dữ liệu bị trùng.", status_code=409)
        self.db.refresh(log)
        return {
            "confirmed": True,
            "status": "CONFIRMED",
            "message": "Đã xác nhận điểm danh.",
            "attendance_log": attendance_log_to_dict(log),
            "student": student_to_dict(student),
        }

    def manual_attendance(
        self,
        *,
        session_id: int,
        student_id: int,
        status: str | None = None,
        note: str = "",
        actor_id: int | None = None,
        camera_id: int | None = None,
    ) -> dict[str, Any]:
        session = self._get_session(session_id)
        self._ensure_session_editable(session)
        student = self._get_student(student_id)
        self._ensure_student_in_session(student, session)
        normalized_status = self._normalize_status(status or ATTENDANCE_MANUAL)

        existing = self._existing_log(session.id, student.id)
        if existing:
            if camera_id is not None:
                existing.camera_id = camera_id
            existing.similarity = 0.0
            audit, changed = self._apply_log_update(
                existing,
                status=normalized_status,
                note=note,
                method=METHOD_MANUAL,
                reason="Cập nhật điểm danh thủ công",
                actor_id=actor_id,
            )
            self._commit()
            self.db.refresh(existing)
            if audit:
                self.db.refresh(audit)
            return {
                "ok": True,
                "status": "UPDATED" if changed else "NO_CHANGES",
                "message": "Đã cập nhật điểm danh thủ công." if changed else "Không có thay đổi điểm danh.",
                "attendance_log": attendance_log_to_dict(existing),
                "student": student_to_dict(student),
                "audit": attendance_log_audit_to_dict(audit) if audit else None,
            }

        log = AttendanceLog(
            session_id=session.id,
            student_id=student.id,
            camera_id=camera_id,
            status=normalized_status,
            method=METHOD_MANUAL,
            similarity=0.0,
            note=note,
        )
        self.db.add(log)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = self._existing_log(session.id, student.id)
            if existing:
                return self.manual_attendance(
                    session_id=session.id,
                    student_id=student.id,
                    status=normalized_status,
                    note=note,
                    actor_id=actor_id,
                    camera_id=camera_id,
                )
            raise BusinessRuleError("ATTENDANCE_LOG_CONFLICT", "Không thể ghi điểm danh thủ công do dữ liệu bị trùng.", status_code=409)
        self.db.refresh(log)
        return {
            "ok": True,
            "status": "CREATED",
            "message": "Đã tạo điểm danh thủ công.",
            "attendance_log": attendance_log_to_dict(log),
            "student": student_to_dict(student),
            "audit": None,
        }

    def update_log(
        self,
        *,
        log_id: int,
        status: str | None = None,
        note: str | None = None,
        method: str | None = None,
        reason: str | None = None,
        actor_id: int | None = None,
    ) -> dict[str, Any]:
        log = self.db.get(AttendanceLog, log_id)
        if not log:
            raise BusinessRuleError("ATTENDANCE_LOG_NOT_FOUND", "Không tìm thấy log điểm danh.", status_code=404)
        self._ensure_session_editable(log.session)
        normalized_status = self._normalize_status(status) if status is not None else None
        normalized_method = self._normalize_method(method) if method is not None else None
        audit, changed = self._apply_log_update(
            log,
            status=normalized_status,
            note=note,
            method=normalized_method,
            reason=reason,
            actor_id=actor_id,
        )
        if not changed:
            return {
                "ok": True,
                "status": "NO_CHANGES",
                "message": "Không có thay đổi điểm danh.",
                "attendance_log": attendance_log_to_dict(log),
                "audit": None,
            }
        self._commit()
        self.db.refresh(log)
        if audit:
            self.db.refresh(audit)
        return {
            "ok": True,
            "status": "UPDATED",
            "message": "Đã cập nhật log điểm danh.",
            "attendance_log": attendance_log_to_dict(log),
            "audit": attendance_log_audit_to_dict(audit) if audit else None,
        }

    def audits_for_log(self, log_id: int) -> dict[str, Any]:
        log = self.db.get(AttendanceLog, log_id)
        if not log:
            raise BusinessRuleError("ATTENDANCE_LOG_NOT_FOUND", "Không tìm thấy log điểm danh.", status_code=404)
        audits = (
            self.db.query(AttendanceLogAudit)
            .filter(AttendanceLogAudit.attendance_log_id == log.id)
            .order_by(AttendanceLogAudit.changed_at.desc())
            .all()
        )
        return {"attendance_log": attendance_log_to_dict(log), "audits": [attendance_log_audit_to_dict(item) for item in audits]}

    def _apply_log_update(
        self,
        log: AttendanceLog,
        *,
        status: str | None,
        note: str | None,
        method: str | None,
        reason: str | None,
        actor_id: int | None,
    ) -> tuple[AttendanceLogAudit | None, bool]:
        old_status = log.status
        old_note = log.note
        old_method = getattr(log, "method", None) or METHOD_FACE

        next_status = status if status is not None else old_status
        next_note = note if note is not None else old_note
        next_method = method if method is not None else old_method

        changed = (old_status != next_status) or (old_note != next_note) or (old_method != next_method)
        if not changed:
            return None, False
        if log.session and log.session.status == SESSION_CLOSED and not (reason or "").strip():
            raise BusinessRuleError("REASON_REQUIRED", "Can nhap ly do khi sua log cua buoi da dong.", status_code=400)

        log.status = next_status
        log.note = next_note
        log.method = next_method
        audit = AttendanceLogAudit(
            attendance_log_id=log.id,
            session_id=log.session_id,
            student_id=log.student_id,
            old_status=old_status,
            new_status=next_status,
            old_method=old_method,
            new_method=next_method,
            old_note=old_note,
            new_note=next_note,
            reason=reason,
            changed_by=actor_id,
        )
        self.db.add(audit)
        return audit, True

    def _already_attended(self, log: AttendanceLog, student: Student) -> dict[str, Any]:
        return {
            "confirmed": True,
            "status": "ALREADY_ATTENDED",
            "message": "Sinh viên đã được điểm danh trong buổi này.",
            "attendance_log": attendance_log_to_dict(log),
            "student": student_to_dict(student),
        }

    def _get_session(self, session_id: int) -> AttendanceSession:
        session = self.db.get(AttendanceSession, session_id)
        if not session:
            raise BusinessRuleError("SESSION_NOT_FOUND", "Không tìm thấy buổi điểm danh.", status_code=404)
        return session

    def _get_student(self, student_id: int) -> Student:
        student = self.db.get(Student, student_id)
        if not student:
            raise BusinessRuleError("STUDENT_NOT_FOUND", "Không tìm thấy sinh viên.", status_code=404)
        return student

    def _ensure_student_in_session(self, student: Student, session: AttendanceSession) -> None:
        if not session.class_course or student.class_id != session.class_course.class_id:
            raise BusinessRuleError(
                "MATCHED_OUT_OF_CLASS",
                "Sinh viên không thuộc lớp của buổi điểm danh này.",
                payload={"student": student_to_dict(student)},
            )

    def _ensure_session_editable(self, session: AttendanceSession | None) -> None:
        if not session:
            raise BusinessRuleError("SESSION_NOT_FOUND", "Không tìm thấy buổi điểm danh.", status_code=404)
        if session.status not in EDITABLE_SESSION_STATUSES:
            raise BusinessRuleError("SESSION_NOT_EDITABLE", "Chỉ được chỉnh sửa điểm danh khi buổi OPEN hoặc CLOSED.")

    def _existing_log(self, session_id: int, student_id: int) -> AttendanceLog | None:
        return (
            self.db.query(AttendanceLog)
            .filter(AttendanceLog.session_id == session_id, AttendanceLog.student_id == student_id)
            .first()
        )

    def _normalize_status(self, status: str) -> str:
        normalized = status.upper()
        if normalized not in VALID_ATTENDANCE_STATUSES:
            raise BusinessRuleError("INVALID_ATTENDANCE_STATUS", f"Trạng thái điểm danh không hợp lệ: {status}.")
        return normalized

    def _normalize_method(self, method: str) -> str:
        normalized = method.upper()
        if normalized == METHOD_NONE:
            raise BusinessRuleError("INVALID_ATTENDANCE_METHOD", "Method NONE chỉ dùng cho roster response, không lưu attendance log.")
        if normalized not in VALID_ATTENDANCE_METHODS:
            raise BusinessRuleError("INVALID_ATTENDANCE_METHOD", f"Phương thức điểm danh không hợp lệ: {method}.")
        return normalized

    def _commit(self) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
