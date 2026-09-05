from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LeaveRequestStatus(StrEnum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    student_code: Mapped[str] = mapped_column(
        ForeignKey("students.student_code"), nullable=False
    )
    session_id: Mapped[str] = mapped_column(
        ForeignKey("class_sessions.session_id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[LeaveRequestStatus] = mapped_column(
        Enum(LeaveRequestStatus, name="leave_request_status", native_enum=True),
        nullable=False,
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.user_id"), nullable=True
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    student: Mapped["Student"] = relationship()
    session: Mapped["ClassSession"] = relationship()
    reviewer: Mapped["User | None"] = relationship()
