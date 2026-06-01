from __future__ import annotations

from datetime import datetime
from typing import Any


def dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def study_class_to_dict(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "class_code": item.class_code,
        "class_name": item.class_name,
        "school_year": item.school_year,
        "status": item.status,
        "created_at": dt(item.created_at),
    }


def student_to_dict(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "student_code": item.student_code,
        "full_name": item.full_name,
        "class_id": item.class_id,
        "class_name": item.study_class.class_name if item.study_class else None,
        "email": item.email,
        "cohort": item.cohort,
        "major": item.major,
        "status": item.status,
        "face_profile": face_profile_to_dict(item.face_profile) if item.face_profile else None,
        "created_at": dt(item.created_at),
        "updated_at": dt(item.updated_at),
    }


def course_to_dict(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "course_code": item.course_code,
        "course_name": item.course_name,
        "credits": item.credits,
        "status": item.status,
        "created_at": dt(item.created_at),
    }


def class_course_to_dict(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "class_id": item.class_id,
        "course_id": item.course_id,
        "teacher_id": item.teacher_id,
        "semester": item.semester,
        "status": item.status,
        "class": study_class_to_dict(item.study_class) if item.study_class else None,
        "course": course_to_dict(item.course) if item.course else None,
    }


def attendance_session_to_dict(item: Any) -> dict[str, Any]:
    class_course = item.class_course
    study_class = class_course.study_class if class_course else None
    course = class_course.course if class_course else None
    return {
        "id": item.id,
        "class_course_id": item.class_course_id,
        "class_course": class_course_to_dict(class_course) if class_course else None,
        "class_id": study_class.id if study_class else None,
        "class_code": study_class.class_code if study_class else None,
        "class_name": study_class.class_name if study_class else None,
        "course_id": course.id if course else None,
        "course_code": course.course_code if course else None,
        "course_name": course.course_name if course else None,
        "created_by": item.created_by,
        "session_name": item.session_name,
        "start_time": dt(item.start_time),
        "end_time": dt(item.end_time),
        "late_threshold_minutes": item.late_threshold_minutes,
        "status": item.status,
        "created_at": dt(item.created_at),
    }


def face_profile_to_dict(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "student_id": item.student_id,
        "compreface_subject": item.compreface_subject,
        "sample_count": item.sample_count,
        "status": item.status,
        "last_enrolled_at": dt(item.last_enrolled_at),
        "created_at": dt(item.created_at),
    }


def camera_to_dict(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "camera_code": item.camera_code,
        "name": item.name,
        "location": item.location,
        "stream_url": item.stream_url,
        "status": item.status,
        "created_at": dt(item.created_at),
    }


def recognition_event_to_dict(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "session_id": item.session_id,
        "camera_id": item.camera_id,
        "face_profile_id": item.face_profile_id,
        "detected_at": dt(item.detected_at),
        "subject": item.subject,
        "similarity": item.similarity,
        "result_type": item.result_type,
        "box_json": item.box_json,
        "image_ref": item.image_ref,
    }


def attendance_log_to_dict(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "session_id": item.session_id,
        "student_id": item.student_id,
        "student_name": item.student.full_name if item.student else None,
        "camera_id": item.camera_id,
        "recognition_event_id": item.recognition_event_id,
        "check_in_time": dt(item.check_in_time),
        "status": item.status,
        "method": getattr(item, "method", None) or "FACE",
        "similarity": item.similarity,
        "note": item.note,
    }


def attendance_log_audit_to_dict(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "attendance_log_id": item.attendance_log_id,
        "session_id": item.session_id,
        "student_id": item.student_id,
        "old_status": item.old_status,
        "new_status": item.new_status,
        "old_method": item.old_method,
        "new_method": item.new_method,
        "old_note": item.old_note,
        "new_note": item.new_note,
        "reason": item.reason,
        "changed_by": item.changed_by,
        "changed_at": dt(item.changed_at),
    }
