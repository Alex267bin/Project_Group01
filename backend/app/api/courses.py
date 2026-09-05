from uuid import uuid4
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser, require_role
from app.db.dependencies import get_db
from app.models.course import Course
from app.models.user import UserRole
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate

router = APIRouter(prefix="/api/v1/courses", tags=["courses"])
AdminUser = Annotated[CurrentUser, Depends(require_role(UserRole.ADMIN))]


def course_or_404(db: Session, course_id: str) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("", response_model=list[CourseResponse])
def list_courses(_: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    return list(db.scalars(select(Course).order_by(Course.course_code)).all())


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: str, _: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    return course_or_404(db, course_id)


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate, _: AdminUser, db: Annotated[Session, Depends(get_db)]):
    course = Course(course_id=str(uuid4()), **payload.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Course code already exists") from None
    db.refresh(course)
    return course


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(course_id: str, payload: CourseUpdate, _: AdminUser, db: Annotated[Session, Depends(get_db)]):
    course = course_or_404(db, course_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Course code already exists") from None
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: str, _: AdminUser, db: Annotated[Session, Depends(get_db)]):
    course = course_or_404(db, course_id)
    db.delete(course)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Course is referenced by a class or session") from None
