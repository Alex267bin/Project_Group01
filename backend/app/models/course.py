from sqlalchemy import Integer, String, Text
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Course(Base):
    __tablename__ = "courses"

    course_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    course_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    classes: Mapped[list["Class"]] = relationship(back_populates="course")
