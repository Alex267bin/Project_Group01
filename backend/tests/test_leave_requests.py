import os
import unittest
from datetime import datetime, timedelta, timezone

os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.api.leave_requests import (
    list_leave_requests,
    list_my_leave_requests,
    review_leave_request,
    submit_leave_request,
)
from app.core.security import hash_password
from app.db.base import Base
from app.models.class_session import ClassSession
from app.models.leave_request import LeaveRequest, LeaveRequestStatus
from app.models.lecturer import Lecturer
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.leave_request import LeaveRequestCreate, LeaveRequestDecision
from app.services.session import activate_session


class LeaveRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)

    def setUp(self) -> None:
        self.db = Session(self.engine)
        self.db.query(LeaveRequest).delete()
        self.db.query(ClassSession).delete()
        self.db.query(Student).delete()
        self.db.query(Lecturer).delete()
        self.db.query(User).delete()
        self.db.commit()

        self.student_user = User(
            user_id="student-user",
            username="student1",
            password_hash=hash_password("unused"),
            full_name="Student",
            email="student@example.com",
            role=UserRole.STUDENT,
        )
        self.admin_user = User(
            user_id="admin-user",
            username="admin1",
            password_hash=hash_password("unused"),
            full_name="Admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        lecturer_user = User(
            user_id="lecturer-user",
            username="lecturer1",
            password_hash=hash_password("unused"),
            full_name="Lecturer",
            email="lecturer@example.com",
            role=UserRole.LECTURER,
        )
        self.student = Student(
            student_code="student-1",
            user_id=self.student_user.user_id,
            class_id="class-1",
        )
        lecturer = Lecturer(
            lecturer_code="lecturer-1",
            user_id=lecturer_user.user_id,
            department="Engineering",
        )
        self.db.add_all([self.student_user, self.admin_user, lecturer_user, self.student, lecturer])
        self.db.commit()
        self.session = activate_session(
            self.db,
            course_name="Software Engineering",
            lecturer_code=lecturer.lecturer_code,
            start_time=datetime.now(timezone.utc) - timedelta(minutes=1),
            end_time=datetime.now(timezone.utc) + timedelta(minutes=30),
        )

    def tearDown(self) -> None:
        self.db.close()

    def test_student_can_submit_and_admin_can_approve(self) -> None:
        request = submit_leave_request(
            LeaveRequestCreate(session_id=self.session.session_id, reason="Medical leave"),
            self.student_user,
            self.db,
        )
        self.assertEqual(request.status, LeaveRequestStatus.PENDING)
        self.assertEqual(request.student_code, self.student.student_code)

        reviewed = review_leave_request(
            request.request_id,
            LeaveRequestDecision(
                status=LeaveRequestStatus.APPROVED,
                review_note="Approved by admin",
            ),
            self.admin_user,
            self.db,
        )
        self.assertEqual(reviewed.status, LeaveRequestStatus.APPROVED)
        self.assertEqual(reviewed.reviewed_by, self.admin_user.user_id)
        self.assertIsNotNone(reviewed.reviewed_at)

    def test_student_can_view_own_requests_and_admin_can_view_all(self) -> None:
        submit_leave_request(
            LeaveRequestCreate(session_id=self.session.session_id, reason="Family matter"),
            self.student_user,
            self.db,
        )

        self.assertEqual(len(list_my_leave_requests(self.student_user, self.db)), 1)
        self.assertEqual(len(list_leave_requests(self.admin_user, self.db)), 1)

    def test_duplicate_request_is_rejected(self) -> None:
        payload = LeaveRequestCreate(session_id=self.session.session_id, reason="Medical leave")
        submit_leave_request(payload, self.student_user, self.db)

        with self.assertRaises(HTTPException) as context:
            submit_leave_request(payload, self.student_user, self.db)

        self.assertEqual(context.exception.status_code, 409)

    def test_missing_session_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as context:
            submit_leave_request(
                LeaveRequestCreate(session_id="missing-session", reason="Reason"),
                self.student_user,
                self.db,
            )

        self.assertEqual(context.exception.status_code, 404)

    def test_only_admin_can_review(self) -> None:
        with self.assertRaises(HTTPException) as context:
            require_role(UserRole.ADMIN)(self.student_user)

        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
