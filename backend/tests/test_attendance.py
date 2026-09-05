import os
import unittest
from datetime import datetime, timedelta, timezone

os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.base import Base
from app.models.attendance_record import AttendanceRecord, AttendanceStatus
from app.models.class_session import ClassSession
from app.models.student import Student
from app.models.user import User, UserRole
from app.services.attendance import record_attendance_by_qr
from app.services.session import activate_session, get_current_qr_token


class AttendanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)

    def setUp(self) -> None:
        self.db = Session(self.engine)
        self.db.query(AttendanceRecord).delete()
        self.db.query(ClassSession).delete()
        self.db.query(Student).delete()
        self.db.query(User).delete()
        self.db.commit()

        user = User(
            user_id="student-user",
            username="student1",
            password_hash=hash_password("unused"),
            full_name="Test Student",
            email="student1@example.com",
            role=UserRole.STUDENT,
        )
        self.student = Student(
            student_code="student-1",
            user_id=user.user_id,
            class_id="class-1",
        )
        self.db.add_all([user, self.student])
        self.db.commit()

        self.now = datetime(2026, 9, 5, 10, 20, tzinfo=timezone.utc)
        self.session = activate_session(
            self.db,
            course_name="Software Engineering",
            lecturer_code="lecturer-1",
            start_time=self.now - timedelta(minutes=10),
            end_time=self.now + timedelta(minutes=20),
        )

    def tearDown(self) -> None:
        self.db.close()

    def scan_payload(self, *, at: datetime | None = None) -> dict[str, object]:
        scan_time = at or self.now
        token, timestamp_bucket = get_current_qr_token(
            self.session.session_id,
            self.session.session_code,
            scan_time,
        )
        return {
            "session_id": self.session.session_id,
            "session_code": self.session.session_code,
            "token": token,
            "timestamp_bucket": timestamp_bucket,
        }

    def scan(self, *, at: datetime | None = None, **overrides: object) -> AttendanceRecord:
        payload = self.scan_payload(at=at)
        payload.update(overrides)
        return record_attendance_by_qr(
            self.db,
            student=self.student,
            now=at or self.now,
            **payload,
        )

    def test_valid_qr_creates_present_attendance(self) -> None:
        record = self.scan(at=self.now - timedelta(minutes=5))

        self.assertEqual(record.status, AttendanceStatus.PRESENT)
        self.assertEqual(record.student_code, self.student.student_code)
        self.assertEqual(record.session_id, self.session.session_id)
        self.assertEqual(record.timestamp, (self.now - timedelta(minutes=5)).replace(tzinfo=None))

    def test_invalid_qr_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as context:
            self.scan(token="invalid-token")

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Invalid or expired QR code")

    def test_expired_qr_is_rejected(self) -> None:
        token, timestamp_bucket = get_current_qr_token(
            self.session.session_id,
            self.session.session_code,
            self.now - timedelta(seconds=15),
        )

        with self.assertRaises(HTTPException) as context:
            self.scan(token=token, timestamp_bucket=timestamp_bucket)

        self.assertEqual(context.exception.status_code, 400)

    def test_duplicate_attendance_is_rejected(self) -> None:
        self.scan(at=self.now - timedelta(minutes=5))

        with self.assertRaises(HTTPException) as context:
            self.scan(at=self.now - timedelta(minutes=5))

        self.assertEqual(context.exception.status_code, 409)

    def test_scan_after_grace_period_is_late(self) -> None:
        late_time = self.session.start_time.replace(tzinfo=timezone.utc) + timedelta(minutes=16)

        record = self.scan(at=late_time)

        self.assertEqual(record.status, AttendanceStatus.LATE)


if __name__ == "__main__":
    unittest.main()
