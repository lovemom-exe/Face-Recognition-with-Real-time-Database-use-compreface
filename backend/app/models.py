from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now_utc() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(Enum("ADMIN", "TEACHER", name="user_role", native_enum=False), nullable=False, default="TEACHER")
    status: Mapped[str] = mapped_column(Enum("ACTIVE", "DISABLED", name="user_status", native_enum=False), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_utc)


class StudyClass(Base):
    __tablename__ = "study_classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    class_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    class_name: Mapped[str] = mapped_column(String(150), nullable=False)
    school_year: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(Enum("ACTIVE", "DISABLED", name="class_status", native_enum=False), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_utc)

    students: Mapped[list["Student"]] = relationship(back_populates="study_class")
    class_courses: Mapped[list["ClassCourse"]] = relationship(back_populates="study_class")

    __table_args__ = (Index("idx_study_classes_school_year", "school_year"),)


class Student(Base):
    __tablename__ = "students_mvp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    class_id: Mapped[int | None] = mapped_column(ForeignKey("study_classes.id", ondelete="SET NULL"))
    email: Mapped[str | None] = mapped_column(String(150))
    cohort: Mapped[str | None] = mapped_column(String(50))
    major: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(Enum("ACTIVE", "DISABLED", name="student_status", native_enum=False), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    study_class: Mapped[StudyClass | None] = relationship(back_populates="students")
    face_profile: Mapped["FaceProfile | None"] = relationship(back_populates="student", uselist=False)
    attendance_logs: Mapped[list["AttendanceLog"]] = relationship(back_populates="student")

    __table_args__ = (
        Index("idx_students_mvp_class_id", "class_id"),
        Index("idx_students_mvp_full_name", "full_name"),
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    course_name: Mapped[str] = mapped_column(String(150), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(Enum("ACTIVE", "DISABLED", name="course_status", native_enum=False), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_utc)

    class_courses: Mapped[list["ClassCourse"]] = relationship(back_populates="course")


class ClassCourse(Base):
    __tablename__ = "class_courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("study_classes.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    semester: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    status: Mapped[str] = mapped_column(Enum("ACTIVE", "DISABLED", name="class_course_status", native_enum=False), nullable=False, default="ACTIVE")

    study_class: Mapped[StudyClass] = relationship(back_populates="class_courses")
    course: Mapped[Course] = relationship(back_populates="class_courses")
    sessions: Mapped[list["AttendanceSession"]] = relationship(back_populates="class_course")

    __table_args__ = (
        UniqueConstraint("class_id", "course_id", "semester", name="uq_class_course_semester"),
        Index("idx_class_courses_class_id", "class_id"),
        Index("idx_class_courses_course_id", "course_id"),
    )


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions_mvp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    class_course_id: Mapped[int] = mapped_column(ForeignKey("class_courses.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    session_name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    late_threshold_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    status: Mapped[str] = mapped_column(
        Enum("DRAFT", "OPEN", "CLOSED", "LOCKED", "CANCELLED", name="attendance_session_status", native_enum=False),
        nullable=False,
        default="DRAFT",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_utc)

    class_course: Mapped[ClassCourse] = relationship(back_populates="sessions")
    attendance_logs: Mapped[list["AttendanceLog"]] = relationship(back_populates="session")
    recognition_events: Mapped[list["RecognitionEvent"]] = relationship(back_populates="session")

    __table_args__ = (
        Index("idx_attendance_sessions_mvp_class_course_id", "class_course_id"),
        Index("idx_attendance_sessions_mvp_start_time", "start_time"),
        Index("idx_attendance_sessions_mvp_status", "status"),
    )


class FaceProfile(Base):
    __tablename__ = "face_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students_mvp.id", ondelete="CASCADE"), nullable=False, unique=True)
    compreface_subject: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        Enum("PENDING", "ACTIVE", "RETRAIN_REQUIRED", "DISABLED", name="face_profile_status", native_enum=False),
        nullable=False,
        default="PENDING",
    )
    last_enrolled_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_utc)

    student: Mapped[Student] = relationship(back_populates="face_profile")
    recognition_events: Mapped[list["RecognitionEvent"]] = relationship(back_populates="face_profile")

    __table_args__ = (
        Index("idx_face_profiles_subject", "compreface_subject"),
        Index("idx_face_profiles_status", "status"),
    )


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    stream_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(Enum("ACTIVE", "INACTIVE", "ERROR", name="camera_status", native_enum=False), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_utc)

    recognition_events: Mapped[list["RecognitionEvent"]] = relationship(back_populates="camera")
    attendance_logs: Mapped[list["AttendanceLog"]] = relationship(back_populates="camera")


class RecognitionEvent(Base):
    __tablename__ = "recognition_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("attendance_sessions_mvp.id", ondelete="SET NULL"))
    camera_id: Mapped[int | None] = mapped_column(ForeignKey("cameras.id", ondelete="SET NULL"))
    face_profile_id: Mapped[int | None] = mapped_column(ForeignKey("face_profiles.id", ondelete="SET NULL"))
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_utc)
    subject: Mapped[str | None] = mapped_column(String(150))
    similarity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    result_type: Mapped[str] = mapped_column(
        Enum("MATCH", "UNKNOWN", "LOW_CONFIDENCE", "ERROR", name="recognition_result_type", native_enum=False),
        nullable=False,
        default="UNKNOWN",
    )
    box_json: Mapped[str | None] = mapped_column(Text)
    image_ref: Mapped[str | None] = mapped_column(String(500))
    raw_response_json: Mapped[str | None] = mapped_column(Text)

    session: Mapped[AttendanceSession | None] = relationship(back_populates="recognition_events")
    camera: Mapped[Camera | None] = relationship(back_populates="recognition_events")
    face_profile: Mapped[FaceProfile | None] = relationship(back_populates="recognition_events")
    attendance_log: Mapped["AttendanceLog | None"] = relationship(back_populates="recognition_event", uselist=False)

    __table_args__ = (
        Index("idx_recognition_events_session_id", "session_id"),
        Index("idx_recognition_events_camera_id", "camera_id"),
        Index("idx_recognition_events_detected_at", "detected_at"),
        Index("idx_recognition_events_subject_time", "subject", "detected_at"),
    )


class AttendanceLog(Base):
    __tablename__ = "attendance_logs_mvp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("attendance_sessions_mvp.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students_mvp.id", ondelete="CASCADE"), nullable=False)
    camera_id: Mapped[int | None] = mapped_column(ForeignKey("cameras.id", ondelete="SET NULL"))
    recognition_event_id: Mapped[int | None] = mapped_column(ForeignKey("recognition_events.id", ondelete="SET NULL"), unique=True)
    check_in_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_utc)
    status: Mapped[str] = mapped_column(
        Enum(
            "ON_TIME",
            "LATE",
            "ABSENT",
            "EXCUSED",
            "MANUAL",
            "PENDING_REVIEW",
            "INVALID",
            name="attendance_log_status",
            native_enum=False,
        ),
        nullable=False,
        default="ON_TIME",
    )
    method: Mapped[str] = mapped_column(
        Enum("FACE", "MANUAL", "AUTO_ABSENT", name="attendance_log_method", native_enum=False),
        nullable=False,
        default="FACE",
    )
    similarity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")

    session: Mapped[AttendanceSession] = relationship(back_populates="attendance_logs")
    student: Mapped[Student] = relationship(back_populates="attendance_logs")
    camera: Mapped[Camera | None] = relationship(back_populates="attendance_logs")
    recognition_event: Mapped[RecognitionEvent | None] = relationship(back_populates="attendance_log")
    audits: Mapped[list["AttendanceLogAudit"]] = relationship(back_populates="attendance_log")

    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_attendance_session_student"),
        Index("idx_attendance_logs_mvp_student_id", "student_id"),
        Index("idx_attendance_logs_mvp_session_id", "session_id"),
        Index("idx_attendance_logs_mvp_check_in_time", "check_in_time"),
    )


class AttendanceLogAudit(Base):
    __tablename__ = "attendance_log_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attendance_log_id: Mapped[int] = mapped_column(ForeignKey("attendance_logs_mvp.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[int] = mapped_column(ForeignKey("attendance_sessions_mvp.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students_mvp.id", ondelete="CASCADE"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str | None] = mapped_column(String(30))
    old_method: Mapped[str | None] = mapped_column(String(30))
    new_method: Mapped[str | None] = mapped_column(String(30))
    old_note: Mapped[str | None] = mapped_column(Text)
    new_note: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_utc)

    attendance_log: Mapped[AttendanceLog] = relationship(back_populates="audits")
    session: Mapped[AttendanceSession] = relationship()
    student: Mapped[Student] = relationship()

    __table_args__ = (
        Index("idx_attendance_log_audits_log_id", "attendance_log_id"),
        Index("idx_attendance_log_audits_session_id", "session_id"),
        Index("idx_attendance_log_audits_student_id", "student_id"),
        Index("idx_attendance_log_audits_changed_at", "changed_at"),
    )
