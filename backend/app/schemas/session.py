from datetime import datetime, timezone

from pydantic import BaseModel, model_validator


class SessionActivationRequest(BaseModel):
    course_name: str
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_time_range(self) -> "SessionActivationRequest":
        self.start_time = self._as_utc(self.start_time)
        self.end_time = self._as_utc(self.end_time)
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class SessionActivationResponse(BaseModel):
    session_id: str
    course_name: str
    lecturer_code: str
    start_time: datetime
    end_time: datetime
    session_code: str
    qr_data_uri: str


class SessionQRResponse(BaseModel):
    session_id: str
    session_code: str
    token: str
    timestamp_bucket: int
    qr_data_uri: str