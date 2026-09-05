"""Add course/class CRUD tables and link sessions."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_courses_classes_sessions"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("course_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("credits", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("course_id"),
        sa.UniqueConstraint("course_code"),
    )

    op.create_table(
        "classes",
        sa.Column("class_id", sa.String(length=36), nullable=False),
        sa.Column("class_code", sa.String(length=50), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("lecturer_code", sa.String(length=36), nullable=False),
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("semester", sa.String(length=20), nullable=False),
        sa.Column("room", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.course_id"]),
        sa.ForeignKeyConstraint(["lecturer_code"], ["lecturers.lecturer_code"]),
        sa.PrimaryKeyConstraint("class_id"),
        sa.UniqueConstraint("class_code"),
    )

    op.add_column("class_sessions", sa.Column("class_id", sa.String(length=36), nullable=True))
    op.add_column("class_sessions", sa.Column("course_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_class_sessions_class_id",
        "class_sessions",
        "classes",
        ["class_id"],
        ["class_id"],
    )
    op.create_foreign_key(
        "fk_class_sessions_course_id",
        "class_sessions",
        "courses",
        ["course_id"],
        ["course_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_class_sessions_course_id", "class_sessions", type_="foreignkey")
    op.drop_constraint("fk_class_sessions_class_id", "class_sessions", type_="foreignkey")
    op.drop_column("class_sessions", "course_id")
    op.drop_column("class_sessions", "class_id")
    op.drop_table("classes")
    op.drop_table("courses")
