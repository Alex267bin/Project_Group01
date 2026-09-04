from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import engine, get_db, Base
from schemas import StudentCreate, AttendanceCreate


# Tạo các bảng database nếu chưa có
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Student Attendance Statistics API",
    description="Attendance statistics and absence alert system",
    version="1.0.0"
)


# =========================
# 1. TẠO SINH VIÊN
# =========================

@app.post("/students")
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db)
):
    existing_student = (
        db.query(models.Student)
        .filter(
            models.Student.student_code == student.student_code
        )
        .first()
    )

    if existing_student:
        raise HTTPException(
            status_code=400,
            detail="Student code already exists"
        )

    new_student = models.Student(
        student_code=student.student_code,
        name=student.name
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return {
        "message": "Student created successfully",
        "student": {
            "id": new_student.id,
            "student_code": new_student.student_code,
            "name": new_student.name
        }
    }


# =========================
# 2. GHI NHẬN ĐIỂM DANH
# =========================

@app.post("/attendance")
def create_attendance(
    attendance: AttendanceCreate,
    db: Session = Depends(get_db)
):
    student = (
        db.query(models.Student)
        .filter(
            models.Student.id == attendance.student_id
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    new_attendance = models.Attendance(
        student_id=attendance.student_id,
        session_number=attendance.session_number,
        present=attendance.present,
        late=attendance.late
    )

    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)

    return {
        "message": "Attendance recorded successfully",
        "attendance_id": new_attendance.id
    }


# =========================
# 3. THỐNG KÊ ĐIỂM DANH
# =========================

@app.get("/attendance/{student_id}/statistics")
def get_attendance_statistics(
    student_id: int,
    db: Session = Depends(get_db)
):
    student = (
        db.query(models.Student)
        .filter(
            models.Student.id == student_id
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    records = (
        db.query(models.Attendance)
        .filter(
            models.Attendance.student_id == student_id
        )
        .all()
    )

    total_sessions = len(records)

    present_count = sum(
        1 for record in records
        if record.present
    )

    absent_count = total_sessions - present_count

    late_count = sum(
        1 for record in records
        if record.late
    )

    if total_sessions > 0:
        attendance_rate = (
            present_count / total_sessions
        ) * 100

        absence_rate = (
            absent_count / total_sessions
        ) * 100
    else:
        attendance_rate = 0
        absence_rate = 0

    return {
        "student_id": student.id,
        "student_code": student.student_code,
        "student_name": student.name,
        "total_sessions": total_sessions,
        "present": present_count,
        "absent": absent_count,
        "late": late_count,
        "attendance_rate": round(attendance_rate, 2),
        "absence_rate": round(absence_rate, 2)
    }


# =========================
# 4. CẢNH BÁO NGHỈ > 20%
# =========================

@app.get("/attendance/{student_id}/alert")
def check_absence_alert(
    student_id: int,
    db: Session = Depends(get_db)
):
    student = (
        db.query(models.Student)
        .filter(
            models.Student.id == student_id
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    records = (
        db.query(models.Attendance)
        .filter(
            models.Attendance.student_id == student_id
        )
        .all()
    )

    total_sessions = len(records)

    if total_sessions == 0:
        return {
            "student_id": student.id,
            "student_name": student.name,
            "total_sessions": 0,
            "absent": 0,
            "absence_rate": 0,
            "alert": False,
            "message": "No attendance records found"
        }

    absent_count = sum(
        1 for record in records
        if not record.present
    )

    absence_rate = (
        absent_count / total_sessions
    ) * 100

    # Cảnh báo khi nghỉ HƠN 20%
    alert = absence_rate > 20

    if alert:
        message = (
            "WARNING: Student absence rate "
            "exceeds 20%"
        )
    else:
        message = (
            "Student absence rate is within "
            "the allowed limit"
        )

    return {
        "student_id": student.id,
        "student_name": student.name,
        "total_sessions": total_sessions,
        "absent": absent_count,
        "absence_rate": round(absence_rate, 2),
        "alert": alert,
        "message": message
    }