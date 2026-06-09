from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from .attendance_services import AttendanceLogService, BusinessRuleError
from .compreface_client import CompreFaceClient, CompreFaceClientError
from .config import settings
from .models import (
    AttendanceLog,
    AttendanceSession,
    FaceProfile,
    RecognitionEvent,
    Student,
)
from .serializers import attendance_log_to_dict, recognition_event_to_dict, student_to_dict


def slugify_subject(value: str, prefix: str = "student_") -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    return f"{prefix}{normalized}"


class FaceProfileService:
    def __init__(self, db: Session, compreface: CompreFaceClient | None = None) -> None:
        self.db = db
        self.compreface = compreface or CompreFaceClient()

    def ensure_profile(self, student: Student, subject: str | None = None) -> FaceProfile:
        existing = self.db.query(FaceProfile).filter(FaceProfile.student_id == student.id).first()
        if existing:
            return existing

        compreface_subject = subject or slugify_subject(student.student_code)
        self.compreface.create_subject(compreface_subject)
        profile = FaceProfile(
            student_id=student.id,
            compreface_subject=compreface_subject,
            status="PENDING",
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def upload_examples(self, profile: FaceProfile, files: list[tuple[str, bytes]]) -> FaceProfile:
        uploaded = 0
        for file_name, content in files:
            self.compreface.upload_face_bytes(profile.compreface_subject, file_name, content)
            uploaded += 1

        profile.sample_count += uploaded
        profile.last_enrolled_at = datetime.utcnow()
        if profile.sample_count > 0:
            profile.status = "ACTIVE"

        self.db.commit()
        self.db.refresh(profile)
        return profile


class RecognitionService:
    def __init__(self, db: Session, compreface: CompreFaceClient | None = None) -> None:
        self.db = db
        self.compreface = compreface or CompreFaceClient()

    def recognize_and_log(
        self,
        *,
        file_name: str,
        content: bytes,
        session_id: int | None = None,
        camera_id: int | None = None,
        threshold: float | None = None,
    ) -> dict[str, Any]:
        threshold = settings.recognition_threshold if threshold is None else threshold
        session_error = self._recognition_session_error(session_id, camera_id)
        if session_error:
            return session_error

        try:
            response = self.compreface.recognize_bytes(file_name, content)
        except CompreFaceClientError as exc:
            event = self._create_event(
                session_id=session_id,
                camera_id=camera_id,
                result_type="ERROR",
                raw_response={"error": str(exc)},
            )
            return {
                "events": [event],
                "attendance_logs": [],
                "detections": [self._detection_payload(event, None, None, "AI_SERVICE_ERROR")],
                **self._primary_response(event, None, None, "AI_SERVICE_ERROR"),
            }

        results = response.get("result", []) if isinstance(response, dict) else []
        if not results:
            event = self._create_event(
                session_id=session_id,
                camera_id=camera_id,
                result_type="UNKNOWN",
                raw_response=response,
            )
            return {
                "events": [event],
                "attendance_logs": [],
                "detections": [self._detection_payload(event, None, None, "UNKNOWN")],
                **self._primary_response(event, None, None, "UNKNOWN"),
            }

        events: list[RecognitionEvent] = []
        detections: list[dict[str, Any]] = []
        for face in results:
            detection = self._handle_face_result(face, response, session_id, camera_id, threshold)
            events.append(detection["event_model"])
            detections.append(detection["payload"])

        primary = detections[0] if detections else None
        return {
            "events": events,
            "attendance_logs": [],
            "detections": detections,
            **(self._primary_response_from_detection(primary) if primary else {}),
        }

    def confirm_attendance(
        self,
        *,
        recognition_event_id: int | None,
        session_id: int | None = None,
        student_id: int | None = None,
        camera_id: int | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        event = self.db.get(RecognitionEvent, recognition_event_id) if recognition_event_id else None
        if recognition_event_id and not event:
            return {"confirmed": False, "status": "EVENT_NOT_FOUND", "message": "Không tìm thấy sự kiện nhận diện."}
        if event and session_id and event.session_id and event.session_id != session_id:
            return {
                "confirmed": False,
                "status": "EVENT_SESSION_MISMATCH",
                "message": "Sự kiện nhận diện không thuộc buổi điểm danh đã chọn.",
            }

        resolved_session_id = session_id or (event.session_id if event else None)
        if not resolved_session_id:
            return {"confirmed": False, "status": "NO_SESSION_SELECTED", "message": "Chưa chọn buổi điểm danh."}

        resolved_student_id = student_id
        if event and event.face_profile:
            event_student_id = event.face_profile.student_id
            if resolved_student_id and resolved_student_id != event_student_id:
                return {
                    "confirmed": False,
                    "status": "STUDENT_EVENT_MISMATCH",
                    "message": "Sinh viên xác nhận không khớp với subject nhận diện.",
                }
            resolved_student_id = resolved_student_id or event_student_id
        if not resolved_student_id:
            return {"confirmed": False, "status": "UNMAPPED_SUBJECT", "message": "Subject chưa được map với sinh viên trong hệ thống."}

        try:
            return AttendanceLogService(self.db).confirm_from_recognition(
                session_id=resolved_session_id,
                student_id=resolved_student_id,
                recognition_event=event,
                camera_id=camera_id,
                note=note,
            )
        except BusinessRuleError as exc:
            return {"confirmed": False, **exc.as_dict()}

    def reject_recognition(self, recognition_event_id: int) -> dict[str, Any]:
        event = self.db.get(RecognitionEvent, recognition_event_id)
        if not event:
            return {"rejected": False, "message": "Không tìm thấy sự kiện nhận diện."}
        return {
            "rejected": True,
            "message": "Đã bỏ qua kết quả nhận diện, không ghi điểm danh chính thức.",
            "event": recognition_event_to_dict(event),
        }

    def _handle_face_result(
        self,
        face: dict[str, Any],
        raw_response: Any,
        session_id: int | None,
        camera_id: int | None,
        threshold: float,
    ) -> dict[str, Any]:
        subjects = face.get("subjects", [])
        best = subjects[0] if subjects else {}
        subject = best.get("subject")
        similarity = float(best.get("similarity") or 0.0)
        face_profile = None
        student = None
        in_class = None
        attendance_log = None
        status = "UNKNOWN"
        result_type = "UNKNOWN"

        if subject and similarity < threshold:
            result_type = "LOW_CONFIDENCE"
            status = "LOW_CONFIDENCE"
            face_profile = self._find_active_profile(subject)
            student = face_profile.student if face_profile else None
            in_class = self._student_in_session_class(session_id, student) if student else None
        elif subject:
            face_profile = self._find_active_profile(subject)
            result_type = "MATCH"
            if not face_profile:
                status = "UNMAPPED_SUBJECT"
            else:
                student = face_profile.student
                in_class = self._student_in_session_class(session_id, student) if student else None
                if in_class is True:
                    attendance_log = self._existing_attendance_log(session_id, student.id)
                    status = "ALREADY_ATTENDED" if attendance_log else "MATCHED_IN_CLASS"
                elif in_class is False:
                    status = "MATCHED_OUT_OF_CLASS"
                else:
                    status = "NO_SESSION_SELECTED"

        event = self._create_event(
            session_id=session_id,
            camera_id=camera_id,
            face_profile_id=face_profile.id if face_profile else None,
            subject=subject,
            similarity=similarity,
            result_type=result_type,
            box=face.get("box"),
            raw_response=raw_response,
        )
        return {
            "event_model": event,
            "payload": self._detection_payload(event, student, in_class, status, attendance_log),
        }

    def _find_active_profile(self, subject: str) -> FaceProfile | None:
        return (
            self.db.query(FaceProfile)
            .filter(FaceProfile.compreface_subject == subject, FaceProfile.status == "ACTIVE")
            .first()
        )

    def _existing_attendance_log(self, session_id: int | None, student_id: int) -> AttendanceLog | None:
        if not session_id:
            return None
        return (
            self.db.query(AttendanceLog)
            .filter(AttendanceLog.session_id == session_id, AttendanceLog.student_id == student_id)
            .first()
        )

    def _recognition_session_error(self, session_id: int | None, camera_id: int | None) -> dict[str, Any] | None:
        if not session_id:
            return self._empty_response("NO_SESSION_SELECTED", None, camera_id)
        session = self.db.get(AttendanceSession, session_id)
        if not session:
            return self._empty_response("SESSION_NOT_FOUND", session_id, camera_id)
        if session.status != "OPEN":
            return self._empty_response("SESSION_NOT_OPEN", session_id, camera_id)
        return None

    def _empty_response(self, status: str, session_id: int | None, camera_id: int | None) -> dict[str, Any]:
        context = self._session_context(session_id)
        return {
            "events": [],
            "attendance_logs": [],
            "detections": [],
            "recognized": False,
            "similarity": None,
            "subject": None,
            "student_id": None,
            "student_code": None,
            "student_name": None,
            "class_id": context.get("class_id"),
            "class_name": context.get("class_name"),
            "course_name": context.get("course_name"),
            "session_id": session_id,
            "camera_id": camera_id,
            "belongs_to_session_class": None,
            "status": status,
            "message": self._message_for_status(status),
            "event_id": None,
        }

    def _student_in_session_class(self, session_id: int | None, student: Student | None) -> bool | None:
        if not session_id or not student:
            return None
        session = self.db.get(AttendanceSession, session_id)
        if not session or not session.class_course:
            return None
        return student.class_id == session.class_course.class_id

    def _detection_payload(
        self,
        event: RecognitionEvent,
        student: Student | None,
        in_class: bool | None,
        status: str,
        log: AttendanceLog | None = None,
    ) -> dict[str, Any]:
        context = self._session_context(event.session_id)
        return {
            "event": recognition_event_to_dict(event),
            "student": student_to_dict(student) if student else None,
            "in_class": in_class,
            "decision": status,
            "status": status,
            "message": self._message_for_status(status),
            "recognized": status not in {"UNKNOWN", "AI_SERVICE_ERROR", "NO_SESSION_SELECTED", "SESSION_NOT_FOUND", "SESSION_NOT_OPEN"},
            "event_id": event.id,
            "similarity": event.similarity,
            "subject": event.subject,
            "student_id": student.id if student else None,
            "student_code": student.student_code if student else None,
            "student_name": student.full_name if student else None,
            "class_id": student.class_id if student else context.get("class_id"),
            "class_name": student.study_class.class_name if student and student.study_class else context.get("class_name"),
            "course_name": context.get("course_name"),
            "session_id": event.session_id,
            "belongs_to_session_class": in_class,
            "attendance_log": attendance_log_to_dict(log) if log else None,
        }

    def _primary_response(self, event: RecognitionEvent, student: Student | None, in_class: bool | None, status: str) -> dict[str, Any]:
        return self._primary_response_from_detection(self._detection_payload(event, student, in_class, status))

    def _primary_response_from_detection(self, detection: dict[str, Any]) -> dict[str, Any]:
        return {
            "recognized": detection["recognized"],
            "similarity": detection["similarity"],
            "subject": detection["subject"],
            "student_id": detection["student_id"],
            "student_code": detection["student_code"],
            "student_name": detection["student_name"],
            "class_id": detection["class_id"],
            "class_name": detection["class_name"],
            "course_name": detection["course_name"],
            "session_id": detection["session_id"],
            "belongs_to_session_class": detection["belongs_to_session_class"],
            "status": detection["status"],
            "message": detection["message"],
            "event_id": detection["event_id"],
        }

    def _session_context(self, session_id: int | None) -> dict[str, Any]:
        if not session_id:
            return {}
        session = self.db.get(AttendanceSession, session_id)
        if not session or not session.class_course:
            return {}
        return {
            "class_id": session.class_course.class_id,
            "class_name": session.class_course.study_class.class_name if session.class_course.study_class else None,
            "course_name": session.class_course.course.course_name if session.class_course.course else None,
        }

    def _message_for_status(self, status: str) -> str:
        messages = {
            "MATCHED_IN_CLASS": "Nhận diện được sinh viên thuộc lớp. Vui lòng xác nhận để ghi điểm danh.",
            "MATCHED_OUT_OF_CLASS": "Sinh viên không thuộc lớp của buổi điểm danh này.",
            "UNMAPPED_SUBJECT": "Subject chưa được map hồ sơ khuôn mặt.",
            "LOW_CONFIDENCE": "Độ tin cậy thấp, cần kiểm tra lại.",
            "UNKNOWN": "Không nhận diện được khuôn mặt.",
            "NO_SESSION_SELECTED": "Chưa chọn buổi điểm danh.",
            "SESSION_NOT_FOUND": "Không tìm thấy buổi điểm danh.",
            "SESSION_NOT_OPEN": "Buổi điểm danh chưa được mở hoặc đã đóng.",
            "ALREADY_ATTENDED": "Sinh viên đã được điểm danh trong buổi này.",
            "AI_SERVICE_ERROR": "Không kết nối được CompreFace.",
        }
        return messages.get(status, "Cần kiểm tra lại kết quả nhận diện.")

    def _create_event(
        self,
        *,
        session_id: int | None = None,
        camera_id: int | None = None,
        face_profile_id: int | None = None,
        subject: str | None = None,
        similarity: float = 0.0,
        result_type: str,
        box: dict[str, Any] | None = None,
        raw_response: Any | None = None,
    ) -> RecognitionEvent:
        event = RecognitionEvent(
            session_id=session_id,
            camera_id=camera_id,
            face_profile_id=face_profile_id,
            subject=subject,
            similarity=similarity,
            result_type=result_type,
            box_json=json.dumps(box, ensure_ascii=False) if box else None,
            raw_response_json=json.dumps(raw_response, ensure_ascii=False) if raw_response else None,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
