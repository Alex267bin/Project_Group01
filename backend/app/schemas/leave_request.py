from datetime import datetime

from pydantic import BaseModel, Field

from app.models.leave_request import LeaveRequestStatus


class LeaveRequestCreate(BaseModel):
    session_id: str = Field(min_length=1, max_length=36)
    reason: str = Field(min_length=1, max_length=2000)


class LeaveRequestDecision(BaseModel):
    status: LeaveRequestStatus
    review_note: str | None = Field(default=None, max_length=2000)


class LeaveRequestResponse(BaseModel):
    model_config = {"from_attributes": True}

    request_id: str
    student_code: str
    session_id: str
    reason: str
    status: LeaveRequestStatus
    submitted_at: datetime
    reviewed_at: datetime | None
    reviewed_by: str | None
    review_note: str | None
