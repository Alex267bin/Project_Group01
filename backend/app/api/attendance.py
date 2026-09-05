from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser, require_role
from app.db.dependencies import get_db
from app.models.attendance_record import AttendanceRecord
from app.models.class_session import ClassSession
from app.models.lecturer import Lecturer
from app.models.student import Student
from app.models.user import UserRole
from app.schemas.attendance import AttendanceHistoryItem, AttendanceQRRequest, AttendanceResponse, AttendanceStatusUpdate
from app.services.attendance import record_attendance_by_qr

router = APIRouter(prefix="/api/v1/attendance", tags=["attendance"])


def record_or_404(db: Session, record_id: str) -> AttendanceRecord:
    record = db.get(AttendanceRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record


def lecturer_can_manage_session(current_user: CurrentUser, session: ClassSession, db: Session) -> bool:
    if current_user.role is UserRole.ADMIN:
        return True
    lecturer = db.scalar(select(Lecturer).where(Lecturer.user_id == current_user.user_id))
    return lecturer is not None and lecturer.lecturer_code == session.lecturer_code


@router.post("/scan", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def scan_qr_for_attendance(
    payload: AttendanceQRRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(UserRole.STUDENT))],
    db: Annotated[Session, Depends(get_db)],
) -> AttendanceRecord:
    student = db.scalar(select(Student).where(Student.user_id == current_user.user_id))
    if student is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return record_attendance_by_qr(
        db,
        student=student,
        session_id=payload.session_id,
        session_code=payload.session_code,
        token=payload.token,
        timestamp_bucket=payload.timestamp_bucket,
    )


@router.get("/me", response_model=list[AttendanceHistoryItem])
def get_my_attendance(
    current_user: Annotated[CurrentUser, Depends(require_role(UserRole.STUDENT))],
    db: Annotated[Session, Depends(get_db)],
):
    student = db.scalar(select(Student).where(Student.user_id == current_user.user_id))
    if student is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    rows = db.execute(
        select(AttendanceRecord, ClassSession.course_name)
        .join(ClassSession, AttendanceRecord.session_id == ClassSession.session_id)
        .where(AttendanceRecord.student_code == student.student_code)
        .order_by(AttendanceRecord.timestamp.desc())
    ).all()
    return [
        AttendanceHistoryItem(
            record_id=record.record_id,
            student_code=record.student_code,
            session_id=record.session_id,
            course_name=course_name,
            timestamp=record.timestamp,
            status=record.status,
        )
        for record, course_name in rows
    ]


@router.get("/sessions/{session_id}", response_model=list[AttendanceHistoryItem])
def get_session_attendance(
    session_id: str,
    current_user: Annotated[CurrentUser, Depends(require_role(UserRole.LECTURER, UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    session = db.get(ClassSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not lecturer_can_manage_session(current_user, session, db):
        raise HTTPException(status_code=403, detail="You can access only your own session records")
    rows = db.scalars(
        select(AttendanceRecord)
        .where(AttendanceRecord.session_id == session_id)
        .order_by(AttendanceRecord.timestamp.asc())
    ).all()
    return [
        AttendanceHistoryItem(
            record_id=record.record_id,
            student_code=record.student_code,
            session_id=record.session_id,
            course_name=session.course_name,
            timestamp=record.timestamp,
            status=record.status,
        )
        for record in rows
    ]


@router.get("/records/{record_id}", response_model=AttendanceResponse)
def get_attendance_record(
    record_id: str,
    current_user: Annotated[CurrentUser, Depends(require_role(UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    record = record_or_404(db, record_id)
    if current_user.role is UserRole.STUDENT:
        student = db.scalar(select(Student).where(Student.user_id == current_user.user_id))
        if student is None or record.student_code != student.student_code:
            raise HTTPException(status_code=403, detail="You can view only your own attendance record")
    elif record.session_id:
        session = db.get(ClassSession, record.session_id)
        if session is None or not lecturer_can_manage_session(current_user, session, db):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    return record


@router.put("/records/{record_id}", response_model=AttendanceResponse)
def update_attendance_record(
    record_id: str,
    payload: AttendanceStatusUpdate,
    current_user: Annotated[CurrentUser, Depends(require_role(UserRole.LECTURER, UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    record = record_or_404(db, record_id)
    if record.session_id is None:
        raise HTTPException(status_code=400, detail="Attendance record has no session")
    session = db.get(ClassSession, record.session_id)
    if session is None or not lecturer_can_manage_session(current_user, session, db):
        raise HTTPException(status_code=403, detail="You can update only your own session records")
    record.status = payload.status
    db.commit()
    db.refresh(record)
    return record


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance_record(
    record_id: str,
    current_user: Annotated[CurrentUser, Depends(require_role(UserRole.LECTURER, UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    record = record_or_404(db, record_id)
    if record.session_id is None:
        raise HTTPException(status_code=400, detail="Attendance record has no session")
    session = db.get(ClassSession, record.session_id)
    if session is None or not lecturer_can_manage_session(current_user, session, db):
        raise HTTPException(status_code=403, detail="You can delete only your own session records")
    db.delete(record)
    db.commit()
