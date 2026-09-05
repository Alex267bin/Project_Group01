"""Add student leave requests and admin review state."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_leave_requests"
down_revision: Union[str, None] = "0002_courses_classes_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    leave_request_status = sa.Enum(
        "Pending", "Approved", "Rejected", name="leave_request_status"
    )
    bind = op.get_bind()
    leave_request_status.create(bind, checkfirst=True)

    op.create_table(
        "leave_requests",
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("student_code", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", leave_request_status, nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=36), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["student_code"], ["students.student_code"]),
        sa.ForeignKeyConstraint(["session_id"], ["class_sessions.session_id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("request_id"),
    )


def downgrade() -> None:
    op.drop_table("leave_requests")
    bind = op.get_bind()
    sa.Enum(name="leave_request_status").drop(bind, checkfirst=True)