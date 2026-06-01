from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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


def attendance_status_for(session: AttendanceSession, at_time: datetime) -> str:
    deadline = session.start_time + timedelta(minutes=session.late_threshold_minutes)
    return "LATE" if at_time > deadline else "ON_TIME"


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
            subjects = face.get("subjects", [])
            best = subjects[0] if subjects else {}
            subject = best.get("subject")
            similarity = float(best.get("similarity") or 0.0)
            face_profile = None
            student = None
            in_class = None
            status = "UNKNOWN"
            result_type = "UNKNOWN"

            if not subject:
                status = "UNKNOWN"
            elif similarity < threshold:
                result_type = "LOW_CONFIDENCE"
                status = "LOW_CONFIDENCE"
                face_profile = self.db.query(FaceProfile).filter(
                    FaceProfile.compreface_subject == subject,
                    FaceProfile.status == "ACTIVE",
                ).first()
                student = face_profile.student if face_profile else None
                in_class = self._student_in_session_class(session_id, student) if student else None
            else:
                face_profile = self.db.query(FaceProfile).filter(
                    FaceProfile.compreface_subject == subject,
                    FaceProfile.status == "ACTIVE",
                ).first()
                result_type = "MATCH"
                if not face_profile:
                    status = "UNMAPPED_SUBJECT"
                else:
                    student = face_profile.student
                    in_class = self._student_in_session_class(session_id, student) if student else None
                    if in_class is True:
                        status = "MATCHED_IN_CLASS"
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
                raw_response=response,
            )
            events.append(event)

            detections.append(self._detection_payload(event, student, in_class, status))

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
    ) -> dict[str, Any]:
        event = self.db.get(RecognitionEvent, recognition_event_id) if recognition_event_id else None
        resolved_session_id = session_id or (event.session_id if event else None)
        if not resolved_session_id:
            return {"confirmed": False, "status": "NO_SESSION_SELECTED", "message": "Chưa chọn buổi điểm danh."}

        session = self.db.get(AttendanceSession, resolved_session_id)
        if not session:
            return {"confirmed": False, "status": "SESSION_NOT_FOUND", "message": "Không tìm thấy buổi điểm danh."}
        if session.status != "OPEN":
            return {"confirmed": False, "status": "SESSION_NOT_OPEN", "message": "Buổi điểm danh chưa được mở hoặc đã đóng."}

        resolved_student_id = student_id
        if not resolved_student_id and event and event.face_profile:
            resolved_student_id = event.face_profile.student_id
        if not resolved_student_id:
            return {"confirmed": False, "status": "UNMAPPED_SUBJECT", "message": "Subject chưa được map với sinh viên trong hệ thống."}

        student = self.db.get(Student, resolved_student_id)
        if not student:
            return {"confirmed": False, "status": "STUDENT_NOT_FOUND", "message": "Không tìm thấy sinh viên."}
        if student.class_id != session.class_course.class_id:
            return {
                "confirmed": False,
                "status": "MATCHED_OUT_OF_CLASS",
                "message": "Sinh viên không thuộc lớp của buổi điểm danh này.",
                "student": student_to_dict(student),
            }

        existing = self.db.query(AttendanceLog).filter(
            AttendanceLog.session_id == session.id,
            AttendanceLog.student_id == student.id,
        ).first()
        if existing:
            return {
                "confirmed": True,
                "status": "ALREADY_ATTENDED",
                "message": "Sinh viên đã được điểm danh.",
                "attendance_log": attendance_log_to_dict(existing),
                "student": student_to_dict(student),
            }

        now = datetime.utcnow()
        log = AttendanceLog(
            session_id=session.id,
            student_id=student.id,
            camera_id=camera_id or (event.camera_id if event else None),
            recognition_event_id=event.id if event else None,
            check_in_time=now,
            status=attendance_status_for(session, now),
            similarity=event.similarity if event else 0.0,
            note="Giảng viên xác nhận từ trạm camera",
        )
        self.db.add(log)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = self.db.query(AttendanceLog).filter(
                AttendanceLog.session_id == session.id,
                AttendanceLog.student_id == student.id,
            ).first()
            if existing:
                return {
                    "confirmed": True,
                    "status": "ALREADY_ATTENDED",
                    "message": "Sinh viên đã được điểm danh.",
                    "attendance_log": attendance_log_to_dict(existing),
                    "student": student_to_dict(student),
                }
            raise
        self.db.refresh(log)
        return {
            "confirmed": True,
            "status": "CONFIRMED",
            "message": "Đã xác nhận điểm danh.",
            "attendance_log": attendance_log_to_dict(log),
            "student": student_to_dict(student),
        }

    def reject_recognition(self, recognition_event_id: int) -> dict[str, Any]:
        event = self.db.get(RecognitionEvent, recognition_event_id)
        if not event:
            return {"rejected": False, "message": "Không tìm thấy sự kiện nhận diện."}
        return {
            "rejected": True,
            "message": "Đã bỏ qua kết quả nhận diện, không ghi điểm danh chính thức.",
            "event": recognition_event_to_dict(event),
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
            "recognized": status not in {"UNKNOWN", "AI_SERVICE_ERROR"},
            "event_id": event.id,
            "similarity": event.similarity,
            "subject": event.subject,
            "student_id": student.id if student else None,
            "student_code": student.student_code if student else None,
            "student_name": student.full_name if student else None,
            "class_id": student.class_id if student else None,
            "class_name": student.study_class.class_name if student and student.study_class else None,
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

    def _create_attendance_log(
        self,
        *,
        session_id: int,
        camera_id: int | None,
        student_id: int,
        recognition_event_id: int,
        similarity: float,
    ) -> AttendanceLog | None:
        session = self.db.get(AttendanceSession, session_id)
        if not session or session.status != "OPEN":
            return None

        existing = self.db.query(AttendanceLog).filter(
            AttendanceLog.session_id == session_id,
            AttendanceLog.student_id == student_id,
        ).first()
        if existing:
            return None

        now = datetime.utcnow()
        log = AttendanceLog(
            session_id=session_id,
            student_id=student_id,
            camera_id=camera_id,
            recognition_event_id=recognition_event_id,
            check_in_time=now,
            status=attendance_status_for(session, now),
            similarity=similarity,
        )
        self.db.add(log)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            return None
        self.db.refresh(log)
        return log
