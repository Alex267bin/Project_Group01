from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser, require_role
from app.db.dependencies import get_db
from app.models.class_session import ClassSession
from app.models.leave_request import LeaveRequest, LeaveRequestStatus
from app.models.student import Student
from app.models.user import UserRole
from app.schemas.leave_request import (
    LeaveRequestCreate,
    LeaveRequestDecision,
    LeaveRequestResponse,
)

router = APIRouter(prefix="/api/v1/leave-requests", tags=["leave requests"])
StudentUser = Annotated[CurrentUser, Depends(require_role(UserRole.STUDENT))]
AdminUser = Annotated[CurrentUser, Depends(require_role(UserRole.ADMIN))]


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_student(db: Session, current_user) -> Student:
    student = db.scalar(select(Student).where(Student.user_id == current_user.user_id))
    if student is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student


def get_request_or_404(db: Session, request_id: str) -> LeaveRequest:
    leave_request = db.get(LeaveRequest, request_id)
    if leave_request is None:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return leave_request


@router.post("", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def submit_leave_request(
    payload: LeaveRequestCreate,
    current_user: StudentUser,
    db: Annotated[Session, Depends(get_db)],
):
    student = get_student(db, current_user)
    if db.get(ClassSession, payload.session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

    existing = db.scalar(
        select(LeaveRequest).where(
            LeaveRequest.student_code == student.student_code,
            LeaveRequest.session_id == payload.session_id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Leave request already exists for this session",
        )

    leave_request = LeaveRequest(
        request_id=str(uuid4()),
        student_code=student.student_code,
        session_id=payload.session_id,
        reason=payload.reason,
        status=LeaveRequestStatus.PENDING,
        submitted_at=utc_now_naive(),
    )
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    return leave_request


@router.get("/me", response_model=list[LeaveRequestResponse])
def list_my_leave_requests(
    current_user: StudentUser,
    db: Annotated[Session, Depends(get_db)],
):
    student = get_student(db, current_user)
    return list(
        db.scalars(
            select(LeaveRequest)
            .where(LeaveRequest.student_code == student.student_code)
            .order_by(LeaveRequest.submitted_at.desc())
        ).all()
    )


@router.get("", response_model=list[LeaveRequestResponse])
def list_leave_requests(
    _: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    return list(
        db.scalars(select(LeaveRequest).order_by(LeaveRequest.submitted_at.desc())).all()
    )


@router.patch("/{request_id}", response_model=LeaveRequestResponse)
def review_leave_request(
    request_id: str,
    payload: LeaveRequestDecision,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    leave_request = get_request_or_404(db, request_id)
    if payload.status is LeaveRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A leave request can only be approved or rejected",
        )
    if leave_request.status is not LeaveRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Leave request has already been reviewed",
        )

    leave_request.status = payload.status
    leave_request.reviewed_by = current_user.user_id
    leave_request.reviewed_at = utc_now_naive()
    leave_request.review_note = payload.review_note
    db.commit()
    db.refresh(leave_request)
    return leave_request
