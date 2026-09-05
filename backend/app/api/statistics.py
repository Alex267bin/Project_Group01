from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser
from app.db.dependencies import get_db
from app.models.student import Student
from app.services.attendance_statistics import get_student_statistics


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