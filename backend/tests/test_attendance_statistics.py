import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.attendance_record import AttendanceRecord, AttendanceStatus
from app.models.class_room import Class
from app.models.class_session import ClassSession
from app.models.course import Course
from app.models.lecturer import Lecturer
from app.models.student import Student
from app.models.user import User, UserRole
from app.services.attendance_statistics import get_student_statistics


class AttendanceStatisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)

    def setUp(self) -> None:
        self.db = Session(self.engine)
        lecturer_user = User(
            user_id="lecturer-user",
            username="lecturer",
            password_hash="unused",
            full_name="Lecturer",
            email="lecturer@example.com",
            role=UserRole.LECTURER,
        )
        lecturer = Lecturer(
            lecturer_code="lecturer-1",
            user=lecturer_user,
            department="Engineering",
        )
        course = Course(
            course_id="course-1",
            course_code="CS101",
            name="Computer Science",
            credits=3,
        )
        class_room = Class(
            class_id="class-1",
            class_code="CS101-A",
            course=course,
            lecturer=lecturer,
            academic_year="2026",
            semester="1",
        )
        student_user = User(
            user_id="student-user",
            username="student",
            password_hash="unused",
            full_name="Student",
            email="student@example.com",
            role=UserRole.STUDENT,
        )
        self.student = Student(
            student_code="student-1",
            user=student_user,
            class_id=class_room.class_id,
        )
        now = datetime.now()
        self.completed_present = ClassSession(
            session_id="session-present",
            class_id=class_room.class_id,
            course_id=course.course_id,
            course_name="Computer Science",
            lecturer_code=lecturer.lecturer_code,
            start_time=now - timedelta(hours=3),
            end_time=now - timedelta(hours=2),
            session_code="PRESENT",
        )
        self.completed_late = ClassSession(
            session_id="session-late",
            class_id=class_room.class_id,
            course_id=course.course_id,
            course_name="Computer Science",
            lecturer_code=lecturer.lecturer_code,
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            session_code="LATE",
        )
        self.completed_absent = ClassSession(
            session_id="session-absent",
            class_id=class_room.class_id,
            course_id=course.course_id,
            course_name="Computer Science",
            lecturer_code=lecturer.lecturer_code,
            start_time=now - timedelta(hours=1),
            end_time=now - timedelta(minutes=30),
            session_code="ABSENT",
        )
        self.incomplete = ClassSession(
            session_id="session-incomplete",
            class_id=class_room.class_id,
            course_id=course.course_id,
            course_name="Computer Science",
            lecturer_code=lecturer.lecturer_code,
            start_time=now,
            end_time=now + timedelta(hours=1),
            session_code="INCOMPLETE",
        )
        self.other_class_session = ClassSession(
            session_id="session-other-class",
            class_id="class-2",
            course_id=course.course_id,
            course_name="Computer Science",
            lecturer_code=lecturer.lecturer_code,
            start_time=now - timedelta(hours=1),
            end_time=now - timedelta(minutes=45),
            session_code="OTHER",
        )
        self.db.add_all(
            [
                class_room,
                self.student,
                self.completed_present,
                self.completed_late,
                self.completed_absent,
                self.incomplete,
                self.other_class_session,
            ]
        )
        self.db.add_all(
            [
                AttendanceRecord(
                    record_id="record-present",
                    student_code=self.student.student_code,
                    session_id=self.completed_present.session_id,
                    status=AttendanceStatus.PRESENT,
                ),
                AttendanceRecord(
                    record_id="record-late",
                    student_code=self.student.student_code,
                    session_id=self.completed_late.session_id,
                    status=AttendanceStatus.LATE,
                ),
            ]
        )
        self.db.commit()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_statistics_follow_student_class_and_count_missing_record_as_absent(self) -> None:
        statistics = get_student_statistics(self.db, self.student)

        self.assertEqual(statistics["total_sessions"], 3)
        self.assertEqual(statistics["present"], 1)
        self.assertEqual(statistics["late"], 1)
        self.assertEqual(statistics["absent"], 1)
        self.assertAlmostEqual(statistics["absence_rate"], 33.33, places=2)
        self.assertTrue(statistics["absence_alert"])
        self.assertEqual(
            [detail["session_id"] for detail in statistics["details"]],
            ["session-present", "session-late", "session-absent"],
        )
        self.assertEqual(
            self.db.scalar(
                select(func.count()).select_from(AttendanceRecord).where(
                    AttendanceRecord.student_code == self.student.student_code
                )
            ),
            2,
        )


if __name__ == "__main__":
    unittest.main()
