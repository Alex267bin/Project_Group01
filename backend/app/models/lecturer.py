from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Lecturer(Base):
    __tablename__ = "lecturers"

    lecturer_code: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.user_id"), unique=True, nullable=False
    )
    department: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped["User"] = relationship(back_populates="lecturer")
    class_sessions: Mapped[list["ClassSession"]] = relationship(
        back_populates="lecturer"
    )