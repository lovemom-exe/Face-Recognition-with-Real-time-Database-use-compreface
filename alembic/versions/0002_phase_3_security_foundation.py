"""phase 3 security foundation

Revision ID: 0002_phase_3_security_foundation
Revises: 0001_phase_1_5
Create Date: 2026-06-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_phase_3_security_foundation"
down_revision = "0001_phase_1_5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("email", sa.String(length=150), nullable=True))
        batch.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        batch.add_column(sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("locked_until", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("last_login_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        batch.create_unique_constraint("uq_users_email", ["email"])
        batch.create_index("idx_users_role", ["role"])
        batch.create_index("idx_users_is_active", ["is_active"])

    with op.batch_alter_table("class_courses") as batch:
        batch.create_index("idx_class_courses_teacher_id", ["teacher_id"])

    op.create_table(
        "teacher_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("study_classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=True),
        sa.Column("semester", sa.String(length=30), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.UniqueConstraint("teacher_id", "class_id", "course_id", "semester", name="uq_teacher_assignment_scope"),
    )
    op.create_index("idx_teacher_assignments_teacher_id", "teacher_assignments", ["teacher_id"])
    op.create_index("idx_teacher_assignments_class_id", "teacher_assignments", ["class_id"])
    op.create_index("idx_teacher_assignments_course_id", "teacher_assignments", ["course_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_role", sa.String(length=30), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=80), nullable=True),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=100), nullable=True),
        sa.Column("user_agent", sa.String(length=300), nullable=True),
        sa.Column("request_id", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])
    op.create_index("idx_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])

    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(length=100), nullable=False, unique=True),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column("value_type", sa.Enum("string", "int", "float", "bool", "json", name="setting_value_type", native_enum=False), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_system_settings_key", "system_settings", ["key"])
    op.create_index("idx_system_settings_updated_at", "system_settings", ["updated_at"])


def downgrade() -> None:
    op.drop_index("idx_system_settings_updated_at", table_name="system_settings")
    op.drop_index("idx_system_settings_key", table_name="system_settings")
    op.drop_table("system_settings")

    op.drop_index("idx_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("idx_audit_logs_resource", table_name="audit_logs")
    op.drop_index("idx_audit_logs_action", table_name="audit_logs")
    op.drop_index("idx_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("idx_teacher_assignments_course_id", table_name="teacher_assignments")
    op.drop_index("idx_teacher_assignments_class_id", table_name="teacher_assignments")
    op.drop_index("idx_teacher_assignments_teacher_id", table_name="teacher_assignments")
    op.drop_table("teacher_assignments")

    with op.batch_alter_table("class_courses") as batch:
        batch.drop_index("idx_class_courses_teacher_id")

    with op.batch_alter_table("users") as batch:
        batch.drop_index("idx_users_is_active")
        batch.drop_index("idx_users_role")
        batch.drop_constraint("uq_users_email", type_="unique")
        batch.drop_column("updated_at")
        batch.drop_column("last_login_at")
        batch.drop_column("locked_until")
        batch.drop_column("failed_login_count")
        batch.drop_column("is_active")
        batch.drop_column("email")
