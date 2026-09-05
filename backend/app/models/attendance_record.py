from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AttendanceStatus(StrEnum):
    PRESENT = "Present"
    LATE = "Late"
    ABSENT = "Absent"


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    record_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    student_code: Mapped[str | None] = mapped_column(
        ForeignKey("students.student_code"), nullable=True
    )
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("class_sessions.session_id"), nullable=True
    )
    timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[AttendanceStatus | None] = mapped_column(
        Enum(AttendanceStatus, name="attendance_status", native_enum=True),
        nullable=True,
    )

    student: Mapped["Student | None"] = relationship(
        back_populates="attendance_records"
    )
    session: Mapped["ClassSession | None"] = relationship(
        back_populates="attendance_records"
    )