"""Create the initial attendance system schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = sa.Enum("Student", "Lecturer", "Admin", name="user_role")
    attendance_status = sa.Enum(
        "Present", "Late", "Absent", name="attendance_status"
    )
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    attendance_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "students",
        sa.Column("student_code", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("class_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("student_code"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "lecturers",
        sa.Column("lecturer_code", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("department", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("lecturer_code"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "class_sessions",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("course_name", sa.String(length=255), nullable=False),
        sa.Column("lecturer_code", sa.String(length=36), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("session_code", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["lecturer_code"], ["lecturers.lecturer_code"]),
        sa.PrimaryKeyConstraint("session_id"),
        sa.UniqueConstraint("session_code"),
    )
    op.create_table(
        "attendance_records",
        sa.Column("record_id", sa.String(length=36), nullable=False),
        sa.Column("student_code", sa.String(length=36), nullable=True),
        sa.Column("session_id", sa.String(length=36), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("status", attendance_status, nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["class_sessions.session_id"]),
        sa.ForeignKeyConstraint(["student_code"], ["students.student_code"]),
        sa.PrimaryKeyConstraint("record_id"),
    )


def downgrade() -> None:
    op.drop_table("attendance_records")
    op.drop_table("class_sessions")
    op.drop_table("lecturers")
    op.drop_table("students")
    op.drop_table("users")
    bind = op.get_bind()
    sa.Enum(name="attendance_status").drop(bind, checkfirst=True)
    sa.Enum(name="user_role").drop(bind, checkfirst=True)