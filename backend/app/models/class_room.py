from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Class(Base):
    __tablename__ = "classes"

    class_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    class_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.course_id"), nullable=False)
    lecturer_code: Mapped[str] = mapped_column(ForeignKey("lecturers.lecturer_code"), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    semester: Mapped[str] = mapped_column(String(20), nullable=False)
    room: Mapped[str | None] = mapped_column(String(100), nullable=True)

    course: Mapped["Course"] = relationship(back_populates="classes")
    lecturer: Mapped["Lecturer"] = relationship()
