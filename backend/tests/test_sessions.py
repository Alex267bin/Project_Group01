import base64
import os
import unittest
from datetime import datetime, timedelta, timezone

os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, require_role
from app.api.sessions import activate_class_session
from app.core.security import hash_password
from app.db.base import Base
from app.models.class_session import ClassSession
from app.models.lecturer import Lecturer
from app.models.user import User, UserRole
from app.schemas.session import SessionActivationRequest
from app.services.qr import (
    build_dynamic_qr_payload,
    build_qr_payload,
    generate_dynamic_qr_data_uri,
    generate_qr_data_uri,
)
from app.services.session import (
    activate_session,
    get_current_qr_token,
    generate_unique_session_code,
    get_active_session,
    get_timestamp_bucket,
    validate_dynamic_qr_token,
)


class SessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)

    def setUp(self) -> None:
        self.db = Session(self.engine)
        self.user = User(
            user_id="lecturer-user",
            username="lecturer1",
            password_hash=hash_password("unused"),
            full_name="Test Lecturer",
            email="lecturer1@example.com",
            role=UserRole.LECTURER,
        )
        self.lecturer = Lecturer(
            lecturer_code="lecturer-1",
            user=self.user,
            department="Engineering",
        )
        self.db.add(self.lecturer)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.query(ClassSession).delete()
        self.db.query(Lecturer).delete()
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()

    def test_session_code_format_and_uniqueness(self) -> None:
        first = generate_unique_session_code(self.db)
        second = generate_unique_session_code(self.db)
        self.assertEqual(len(first), 8)
        self.assertTrue(first.isupper() and first.isalnum())
        self.assertNotEqual(first, second)

    def test_qr_data_uri_contains_png(self) -> None:
        payload = build_qr_payload("session-1", "A7K9P2XM")
        data_uri = generate_qr_data_uri(payload)
        self.assertTrue(data_uri.startswith("data:image/png;base64,"))
        self.assertGreater(len(base64.b64decode(data_uri.split(",", 1)[1])), 0)

    def test_dynamic_token_is_stable_and_rotates_by_bucket(self) -> None:
        first_time = datetime(2026, 9, 5, 10, 0, 1, tzinfo=timezone.utc)
        same_bucket_time = first_time + timedelta(seconds=3)
        next_bucket_time = first_time + timedelta(seconds=5)
        first_token, first_bucket = get_current_qr_token(
            "session-1", "A7K9P2XM", first_time
        )
        same_token, same_bucket = get_current_qr_token(
            "session-1", "A7K9P2XM", same_bucket_time
        )
        next_token, next_bucket = get_current_qr_token(
            "session-1", "A7K9P2XM", next_bucket_time
        )
        self.assertEqual(first_token, same_token)
        self.assertEqual(first_bucket, same_bucket)
        self.assertNotEqual(first_token, next_token)
        self.assertNotEqual(first_bucket, next_bucket)

    def test_dynamic_token_validation(self) -> None:
        now = datetime(2026, 9, 5, 10, 0, 1, tzinfo=timezone.utc)
        token, timestamp_bucket = get_current_qr_token(
            "session-1", "A7K9P2XM", now
        )
        self.assertTrue(
            validate_dynamic_qr_token(
                "session-1", "A7K9P2XM", token, timestamp_bucket, now
            )
        )
        self.assertFalse(
            validate_dynamic_qr_token(
                "session-1",
                "A7K9P2XM",
                token,
                timestamp_bucket - 2,
                now,
                clock_skew_buckets=0,
            )
        )

    def test_dynamic_qr_payload_contains_validation_fields(self) -> None:
        payload = build_dynamic_qr_payload("session-1", "A7K9P2XM", "token", 123)
        self.assertEqual(
            set(payload), {"session_id", "session_code", "token", "timestamp_bucket"}
        )
        self.assertTrue(
            generate_dynamic_qr_data_uri(payload).startswith("data:image/png;base64,")
        )

    def test_lecturer_can_activate_session(self) -> None:
        start_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        end_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        response = activate_class_session(
            SessionActivationRequest(
                course_name="Software Engineering",
                start_time=start_time,
                end_time=end_time,
            ),
            self.user,
            self.db,
        )
        session = self.db.get(ClassSession, response.session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session.lecturer_code, "lecturer-1")
        self.assertEqual(len(session.session_code), 8)
        self.assertTrue(response.qr_data_uri.startswith("data:image/png;base64,"))

    def test_non_lecturer_cannot_activate_session(self) -> None:
        for role in (UserRole.STUDENT, UserRole.ADMIN):
            self.user.role = role
            self.db.commit()
            with self.assertRaises(HTTPException) as context:
                require_role(UserRole.LECTURER)(self.user)
            self.assertEqual(context.exception.status_code, 403)

    def test_missing_credentials_are_rejected(self) -> None:
        with self.assertRaises(HTTPException) as context:
            get_current_user(None, self.db)
        self.assertEqual(context.exception.status_code, 401)

    def test_invalid_time_range_is_rejected(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaises(ValueError):
            SessionActivationRequest(
                course_name="Software Engineering",
                start_time=now,
                end_time=now,
            )

        with self.assertRaises(ValueError):
            SessionActivationRequest(
                course_name="Software Engineering",
                start_time=datetime(2026, 9, 5, 12, 0),
                end_time=datetime(2026, 9, 5, 11, 0, tzinfo=timezone.utc),
            )

    def test_active_session_lookup(self) -> None:
        now = datetime.now(timezone.utc)
        session = activate_session(
            self.db,
            course_name="Software Engineering",
            lecturer_code="lecturer-1",
            start_time=now - timedelta(minutes=1),
            end_time=now + timedelta(minutes=1),
        )
        self.assertIs(get_active_session(self.db, session.session_code, now), session)
        self.assertIsNone(
            get_active_session(self.db, session.session_code, now + timedelta(minutes=2))
        )

    def test_lecturer_can_get_own_active_qr(self) -> None:
        now = datetime.now(timezone.utc)
        session = activate_session(
            self.db,
            course_name="Software Engineering",
            lecturer_code="lecturer-1",
            start_time=now - timedelta(minutes=1),
            end_time=now + timedelta(minutes=1),
        )
        from app.api.sessions import get_session_qr

        response = get_session_qr(session.session_id, self.user, self.db)
        self.assertEqual(response.session_id, session.session_id)
        self.assertEqual(response.session_code, session.session_code)
        self.assertTrue(response.qr_data_uri.startswith("data:image/png;base64,"))

    def test_lecturer_cannot_get_another_lecturers_qr(self) -> None:
        other_user = User(
            user_id="other-lecturer-user",
            username="lecturer2",
            password_hash=hash_password("unused"),
            full_name="Other Lecturer",
            email="lecturer2@example.com",
            role=UserRole.LECTURER,
        )
        self.db.add(
            Lecturer(
                lecturer_code="lecturer-2",
                user=other_user,
                department="Science",
            )
        )
        self.db.commit()
        session = activate_session(
            self.db,
            course_name="Physics",
            lecturer_code="lecturer-2",
            start_time=datetime.now(timezone.utc) - timedelta(minutes=1),
            end_time=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
        from app.api.sessions import get_session_qr

        with self.assertRaises(HTTPException) as context:
            get_session_qr(session.session_id, self.user, self.db)
        self.assertEqual(context.exception.status_code, 404)

    def test_inactive_session_cannot_get_qr(self) -> None:
        session = activate_session(
            self.db,
            course_name="Software Engineering",
            lecturer_code="lecturer-1",
            start_time=datetime.now(timezone.utc) - timedelta(minutes=2),
            end_time=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        from app.api.sessions import get_session_qr

        with self.assertRaises(HTTPException) as context:
            get_session_qr(session.session_id, self.user, self.db)
        self.assertEqual(context.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()