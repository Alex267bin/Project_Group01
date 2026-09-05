from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendance_record import AttendanceRecord, AttendanceStatus
from app.models.class_session import ClassSession
from app.models.student import Student
from app.services.session import (
    get_active_session,
    utc_now,
    validate_dynamic_qr_token,
)


def record_attendance_by_qr(
    db: Session,
    *,
    student: Student,
    session_id: str,
    session_code: str,
    token: str,
    timestamp_bucket: int,
    now: datetime | None = None,
) -> AttendanceRecord:
    """Create one attendance record from Khang's existing dynamic QR flow."""
    current_time = now or utc_now()

    session = db.scalar(
        select(ClassSession).where(
            ClassSession.session_id == session_id,
            ClassSession.session_code == session_code,
        )
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    active_session = get_active_session(db, session_code, current_time)
    if active_session is None or active_session.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active",
        )

    if not validate_dynamic_qr_token(
        session_id,
        session_code,
        token,
        timestamp_bucket,
        current_time,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired QR code",
        )

    existing = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.student_code == student.student_code,
            AttendanceRecord.session_id == session_id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already recorded for this session",
        )

    record = AttendanceRecord(
        record_id=str(uuid4()),
        student_code=student.student_code,
        session_id=session_id,
        timestamp=current_time.replace(tzinfo=None),
        status=AttendanceStatus.PRESENT,
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record
