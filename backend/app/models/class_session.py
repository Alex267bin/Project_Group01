from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.class_room import Class
from app.models.course import Course


class ClassSession(Base):
    __tablename__ = "class_sessions"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    class_id: Mapped[str | None] = mapped_column(
        ForeignKey("classes.class_id"), nullable=True
    )
    course_id: Mapped[str | None] = mapped_column(
        ForeignKey("courses.course_id"), nullable=True
    )
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)
    lecturer_code: Mapped[str] = mapped_column(
        ForeignKey("lecturers.lecturer_code"), nullable=False
    )
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    session_code: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    lecturer: Mapped["Lecturer"] = relationship(back_populates="class_sessions")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="session"
    )