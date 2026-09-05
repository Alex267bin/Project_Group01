from datetime import datetime

from pydantic import BaseModel, Field

from app.models.attendance_record import AttendanceStatus


class AttendanceQRRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=36)
    session_code: str = Field(min_length=1, max_length=255)
    token: str = Field(min_length=1)
    timestamp_bucket: int


class AttendanceResponse(BaseModel):
    record_id: str
    student_code: str | None
    session_id: str | None
    timestamp: datetime | None
    status: AttendanceStatus | None


class AttendanceStatusUpdate(BaseModel):
    status: AttendanceStatus


class AttendanceHistoryItem(BaseModel):
    record_id: str
    student_code: str | None
    session_id: str | None
    course_name: str
    timestamp: datetime | None
    status: AttendanceStatus | None
