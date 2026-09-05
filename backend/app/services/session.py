import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_jwt_secret_key
from app.models.class_session import ClassSession


SESSION_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
SESSION_CODE_LENGTH = 8
DYNAMIC_QR_INTERVAL_SECONDS = 5


def generate_unique_session_code(db: Session) -> str:
    while True:
        session_code = "".join(
            secrets.choice(SESSION_CODE_ALPHABET)
            for _ in range(SESSION_CODE_LENGTH)
        )
        exists = db.scalar(
            select(ClassSession.session_id).where(
                ClassSession.session_code == session_code
            )
        )
        if exists is None:
            return session_code


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def get_timestamp_bucket(
    now: datetime | None = None,
) -> int:
    return int(as_utc(now or utc_now()).timestamp()) // DYNAMIC_QR_INTERVAL_SECONDS


def get_current_qr_token(
    session_id: str,
    session_code: str,
    now: datetime | None = None,
) -> tuple[str, int]:
    timestamp_bucket = get_timestamp_bucket(now)
    message = f"{session_id}:{session_code}:{timestamp_bucket}".encode("utf-8")
    token = hmac.new(
        get_jwt_secret_key().encode("utf-8"), message, hashlib.sha256
    ).hexdigest()
    return token, timestamp_bucket


def validate_dynamic_qr_token(
    session_id: str,
    session_code: str,
    token: str,
    timestamp_bucket: int,
    now: datetime | None = None,
    clock_skew_buckets: int = 1,
) -> bool:
    current_bucket = get_timestamp_bucket(now)
    if abs(timestamp_bucket - current_bucket) > clock_skew_buckets:
        return False

    expected_token, _ = get_current_qr_token(
        session_id,
        session_code,
        datetime.fromtimestamp(
            timestamp_bucket * DYNAMIC_QR_INTERVAL_SECONDS, tz=timezone.utc
        ),
    )
    return hmac.compare_digest(token, expected_token)


def get_active_session(
    db: Session, session_code: str, now: datetime | None = None
) -> ClassSession | None:
    session = db.scalar(
        select(ClassSession).where(ClassSession.session_code == session_code)
    )
    if session is None or session.start_time is None or session.end_time is None:
        return None

    current_time = as_utc(now or utc_now())
    if as_utc(session.start_time) <= current_time <= as_utc(session.end_time):
        return session
    return None


def activate_session(
    db: Session,
    *,
    course_name: str,
    lecturer_code: str,
    start_time: datetime,
    end_time: datetime,
) -> ClassSession:
    session = ClassSession(
        session_id=str(uuid4()),
        course_name=course_name,
        lecturer_code=lecturer_code,
        start_time=as_utc(start_time).replace(tzinfo=None),
        end_time=as_utc(end_time).replace(tzinfo=None),
        session_code=generate_unique_session_code(db),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session