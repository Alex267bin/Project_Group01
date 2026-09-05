from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser, require_role
from app.db.dependencies import get_db
from app.models.class_session import ClassSession
from app.models.lecturer import Lecturer
from app.models.user import UserRole
from app.schemas.session import (
    SessionActivationRequest,
    SessionActivationResponse,
    SessionQRResponse,
)
from app.services.qr import (
    build_dynamic_qr_payload,
    generate_dynamic_qr_data_uri,
)
from app.services.session import (
    activate_session,
    get_active_session,
    get_current_qr_token,
    utc_now,
)


router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post(
    "/activate",
    response_model=SessionActivationResponse,
    status_code=status.HTTP_201_CREATED,
)
def activate_class_session(
    payload: SessionActivationRequest,
    current_user: Annotated[
        CurrentUser, Depends(require_role(UserRole.LECTURER))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> SessionActivationResponse:
    lecturer = db.scalar(select(Lecturer).where(Lecturer.user_id == current_user.user_id))
    if lecturer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecturer profile not found",
        )

    session = activate_session(
        db,
        course_name=payload.course_name,
        lecturer_code=lecturer.lecturer_code,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    token, timestamp_bucket = get_current_qr_token(
        session.session_id, session.session_code
    )
    qr_payload = build_dynamic_qr_payload(
        session.session_id,
        session.session_code,
        token,
        timestamp_bucket,
    )
    return SessionActivationResponse(
        session_id=session.session_id,
        course_name=session.course_name,
        lecturer_code=session.lecturer_code,
        start_time=session.start_time,
        end_time=session.end_time,
        session_code=session.session_code,
        qr_data_uri=generate_dynamic_qr_data_uri(qr_payload),
    )


@router.get("/{session_id}/qr", response_model=SessionQRResponse)
def get_session_qr(
    session_id: str,
    current_user: Annotated[
        CurrentUser, Depends(require_role(UserRole.LECTURER))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> SessionQRResponse:
    lecturer = db.scalar(select(Lecturer).where(Lecturer.user_id == current_user.user_id))
    if lecturer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecturer profile not found",
        )

    session = db.scalar(
        select(ClassSession).where(
            ClassSession.session_id == session_id,
            ClassSession.lecturer_code == lecturer.lecturer_code,
        )
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    current_time = utc_now()
    if get_active_session(db, session.session_code, current_time) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active",
        )

    token, timestamp_bucket = get_current_qr_token(
        session.session_id, session.session_code, current_time
    )
    qr_payload = build_dynamic_qr_payload(
        session.session_id,
        session.session_code,
        token,
        timestamp_bucket,
    )
    return SessionQRResponse(
        session_id=session.session_id,
        session_code=session.session_code,
        token=token,
        timestamp_bucket=timestamp_bucket,
        qr_data_uri=generate_dynamic_qr_data_uri(qr_payload),
    )