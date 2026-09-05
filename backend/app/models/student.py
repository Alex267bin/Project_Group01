from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Student(Base):
    __tablename__ = "students"

    student_code: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.user_id"), unique=True, nullable=False
    )
    class_id: Mapped[str] = mapped_column(String(36), nullable=False)

    user: Mapped["User"] = relationship(back_populates="student")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="student"
    )