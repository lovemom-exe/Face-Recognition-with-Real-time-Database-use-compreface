"""phase 1.5 baseline

Revision ID: 0001_phase_1_5
Revises:
Create Date: 2026-06-02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_phase_1_5"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("role", sa.Enum("ADMIN", "TEACHER", name="user_role", native_enum=False), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "DISABLED", name="user_status", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "study_classes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("class_code", sa.String(length=50), nullable=False),
        sa.Column("class_name", sa.String(length=150), nullable=False),
        sa.Column("school_year", sa.String(length=20), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE", "DISABLED", name="class_status", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("class_code"),
    )
    op.create_index("idx_study_classes_school_year", "study_classes", ["school_year"])

    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_code", sa.String(length=50), nullable=False),
        sa.Column("course_name", sa.String(length=150), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "DISABLED", name="course_status", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_code"),
    )

    op.create_table(
        "students_mvp",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_code", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("cohort", sa.String(length=50), nullable=True),
        sa.Column("major", sa.String(length=150), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE", "DISABLED", name="student_status", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["study_classes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_code"),
    )
    op.create_index("idx_students_mvp_class_id", "students_mvp", ["class_id"])
    op.create_index("idx_students_mvp_full_name", "students_mvp", ["full_name"])

    op.create_table(
        "class_courses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=True),
        sa.Column("semester", sa.String(length=30), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "DISABLED", name="class_course_status", native_enum=False), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["study_classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("class_id", "course_id", "semester", name="uq_class_course_semester"),
    )
    op.create_index("idx_class_courses_class_id", "class_courses", ["class_id"])
    op.create_index("idx_class_courses_course_id", "class_courses", ["course_id"])

    op.create_table(
        "cameras",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("camera_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("stream_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE", "INACTIVE", "ERROR", name="camera_status", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("camera_code"),
    )

    op.create_table(
        "face_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("compreface_subject", sa.String(length=150), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "ACTIVE", "RETRAIN_REQUIRED", "DISABLED", name="face_profile_status", native_enum=False), nullable=False),
        sa.Column("last_enrolled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students_mvp.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("compreface_subject"),
        sa.UniqueConstraint("student_id"),
    )
    op.create_index("idx_face_profiles_status", "face_profiles", ["status"])
    op.create_index("idx_face_profiles_subject", "face_profiles", ["compreface_subject"])

    op.create_table(
        "attendance_sessions_mvp",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("class_course_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("session_name", sa.String(length=200), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("late_threshold_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "OPEN", "CLOSED", "LOCKED", "CANCELLED", name="attendance_session_status", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["class_course_id"], ["class_courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_attendance_sessions_mvp_class_course_id", "attendance_sessions_mvp", ["class_course_id"])
    op.create_index("idx_attendance_sessions_mvp_start_time", "attendance_sessions_mvp", ["start_time"])
    op.create_index("idx_attendance_sessions_mvp_status", "attendance_sessions_mvp", ["status"])

    op.create_table(
        "recognition_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("camera_id", sa.Integer(), nullable=True),
        sa.Column("face_profile_id", sa.Integer(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("subject", sa.String(length=150), nullable=True),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("result_type", sa.Enum("MATCH", "UNKNOWN", "LOW_CONFIDENCE", "ERROR", name="recognition_result_type", native_enum=False), nullable=False),
        sa.Column("box_json", sa.Text(), nullable=True),
        sa.Column("image_ref", sa.String(length=500), nullable=True),
        sa.Column("raw_response_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["face_profile_id"], ["face_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["attendance_sessions_mvp.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_recognition_events_camera_id", "recognition_events", ["camera_id"])
    op.create_index("idx_recognition_events_detected_at", "recognition_events", ["detected_at"])
    op.create_index("idx_recognition_events_session_id", "recognition_events", ["session_id"])
    op.create_index("idx_recognition_events_subject_time", "recognition_events", ["subject", "detected_at"])

    op.create_table(
        "attendance_logs_mvp",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("camera_id", sa.Integer(), nullable=True),
        sa.Column("recognition_event_id", sa.Integer(), nullable=True),
        sa.Column("check_in_time", sa.DateTime(), nullable=False),
        sa.Column("status", sa.Enum("ON_TIME", "LATE", "ABSENT", "EXCUSED", "MANUAL", "PENDING_REVIEW", "INVALID", name="attendance_log_status", native_enum=False), nullable=False),
        sa.Column("method", sa.Enum("FACE", "MANUAL", "AUTO_ABSENT", name="attendance_log_method", native_enum=False), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recognition_event_id"], ["recognition_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["attendance_sessions_mvp.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students_mvp.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recognition_event_id"),
        sa.UniqueConstraint("session_id", "student_id", name="uq_attendance_session_student"),
    )
    op.create_index("idx_attendance_logs_mvp_check_in_time", "attendance_logs_mvp", ["check_in_time"])
    op.create_index("idx_attendance_logs_mvp_session_id", "attendance_logs_mvp", ["session_id"])
    op.create_index("idx_attendance_logs_mvp_student_id", "attendance_logs_mvp", ["student_id"])

    op.create_table(
        "attendance_log_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attendance_log_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("old_status", sa.String(length=30), nullable=True),
        sa.Column("new_status", sa.String(length=30), nullable=True),
        sa.Column("old_method", sa.String(length=30), nullable=True),
        sa.Column("new_method", sa.String(length=30), nullable=True),
        sa.Column("old_note", sa.Text(), nullable=True),
        sa.Column("new_note", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.Integer(), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["attendance_log_id"], ["attendance_logs_mvp.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["attendance_sessions_mvp.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students_mvp.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_attendance_log_audits_changed_at", "attendance_log_audits", ["changed_at"])
    op.create_index("idx_attendance_log_audits_log_id", "attendance_log_audits", ["attendance_log_id"])
    op.create_index("idx_attendance_log_audits_session_id", "attendance_log_audits", ["session_id"])
    op.create_index("idx_attendance_log_audits_student_id", "attendance_log_audits", ["student_id"])


def downgrade() -> None:
    op.drop_index("idx_attendance_log_audits_student_id", table_name="attendance_log_audits")
    op.drop_index("idx_attendance_log_audits_session_id", table_name="attendance_log_audits")
    op.drop_index("idx_attendance_log_audits_log_id", table_name="attendance_log_audits")
    op.drop_index("idx_attendance_log_audits_changed_at", table_name="attendance_log_audits")
    op.drop_table("attendance_log_audits")

    op.drop_index("idx_attendance_logs_mvp_student_id", table_name="attendance_logs_mvp")
    op.drop_index("idx_attendance_logs_mvp_session_id", table_name="attendance_logs_mvp")
    op.drop_index("idx_attendance_logs_mvp_check_in_time", table_name="attendance_logs_mvp")
    op.drop_table("attendance_logs_mvp")

    op.drop_index("idx_recognition_events_subject_time", table_name="recognition_events")
    op.drop_index("idx_recognition_events_session_id", table_name="recognition_events")
    op.drop_index("idx_recognition_events_detected_at", table_name="recognition_events")
    op.drop_index("idx_recognition_events_camera_id", table_name="recognition_events")
    op.drop_table("recognition_events")

    op.drop_index("idx_attendance_sessions_mvp_status", table_name="attendance_sessions_mvp")
    op.drop_index("idx_attendance_sessions_mvp_start_time", table_name="attendance_sessions_mvp")
    op.drop_index("idx_attendance_sessions_mvp_class_course_id", table_name="attendance_sessions_mvp")
    op.drop_table("attendance_sessions_mvp")

    op.drop_index("idx_face_profiles_subject", table_name="face_profiles")
    op.drop_index("idx_face_profiles_status", table_name="face_profiles")
    op.drop_table("face_profiles")

    op.drop_table("cameras")

    op.drop_index("idx_class_courses_course_id", table_name="class_courses")
    op.drop_index("idx_class_courses_class_id", table_name="class_courses")
    op.drop_table("class_courses")

    op.drop_index("idx_students_mvp_full_name", table_name="students_mvp")
    op.drop_index("idx_students_mvp_class_id", table_name="students_mvp")
    op.drop_table("students_mvp")

    op.drop_table("courses")

    op.drop_index("idx_study_classes_school_year", table_name="study_classes")
    op.drop_table("study_classes")

    op.drop_table("users")
