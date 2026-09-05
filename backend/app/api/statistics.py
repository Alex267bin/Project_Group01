from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser
from app.db.dependencies import get_db
from app.models.student import Student
from app.services.attendance_statistics import get_student_statistics
from app.services.excel_report import build_attendance_report


router = APIRouter(
    prefix="/api/v1/statistics",
    tags=["statistics"],
)


@router.get("/me")
def get_my_statistics(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    student = db.scalar(
        select(Student).where(
            Student.user_id == current_user.user_id
        )
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found",
        )

    return get_student_statistics(
        db=db,
        student=student,
    )

@router.get("/me/export")
def export_my_statistics(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    student = db.scalar(
        select(Student).where(
            Student.user_id == current_user.user_id
        )
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found",
        )

    statistics = get_student_statistics(db=db, student=student)
    report = build_attendance_report(
        statistics,
        student_name=student.user.full_name,
    )
    filename = f"attendance_report_{student.student_code}.xlsx"

    return StreamingResponse(
        report,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
