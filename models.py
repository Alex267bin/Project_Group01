from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False
    )

    session_number = Column(Integer, nullable=False)

    present = Column(Boolean, default=False)

    late = Column(Boolean, default=False)