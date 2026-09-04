from pydantic import BaseModel


class StudentCreate(BaseModel):
    student_code: str
    name: str


class AttendanceCreate(BaseModel):
    student_id: int
    session_number: int
    present: bool
    late: bool = False