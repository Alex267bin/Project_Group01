from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.attendance_record import AttendanceRecord, AttendanceStatus


def get_student_statistics(
    db: Session,
    student: Student,
):
    sessions = db.execute(
        text(
            """
            SELECT
                session_id,
                course_name,
                start_time,
                end_time
            FROM class_sessions
            WHERE class_id = :class_id
            ORDER BY start_time
            """
        ),
        {"class_id": student.class_id},
    ).mappings().all()

    total_sessions = 0
    present_count = 0
    late_count = 0
    absent_count = 0

    details = []

    for session in sessions:
        # Chỉ tính những buổi đã kết thúc
        if session["end_time"] is not None:
            from datetime import datetime

            if session["end_time"] > datetime.now():
                continue

        total_sessions += 1

        record = db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.student_code == student.student_code,
                AttendanceRecord.session_id == session["session_id"],
            )
        )

        if record is None:
            status = AttendanceStatus.ABSENT
        else:
            status = record.status or AttendanceStatus.ABSENT

        if status == AttendanceStatus.PRESENT:
            present_count += 1
        elif status == AttendanceStatus.LATE:
            late_count += 1
        else:
            absent_count += 1

        details.append(
            {
                "session_id": session["session_id"],
                "course_name": session["course_name"],
                "start_time": session["start_time"],
                "end_time": session["end_time"],
                "status": status,
            }
        )

    absence_rate = (
        (absent_count / total_sessions) * 100
        if total_sessions > 0
        else 0
    )

    return {
        "student_code": student.student_code,
        "class_id": student.class_id,
        "total_sessions": total_sessions,
        "present": present_count,
        "late": late_count,
        "absent": absent_count,
        "absence_rate": round(absence_rate, 2),
        "absence_alert": absence_rate > 20,
        "details": details,
    }