from uuid import uuid4
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser, require_role
from app.db.dependencies import get_db
from app.models.class_room import Class
from app.models.course import Course
from app.models.lecturer import Lecturer
from app.models.user import UserRole
from app.schemas.class_ import ClassCreate, ClassResponse, ClassUpdate

router = APIRouter(prefix="/api/v1/classes", tags=["classes"])
AdminUser = Annotated[CurrentUser, Depends(require_role(UserRole.ADMIN))]
LecturerOrAdmin = Annotated[CurrentUser, Depends(require_role(UserRole.ADMIN, UserRole.LECTURER))]


def class_or_404(db: Session, class_id: str) -> Class:
    item = db.get(Class, class_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return item


def validate_refs(db: Session, course_id: str, lecturer_code: str) -> None:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if db.get(Lecturer, lecturer_code) is None:
        raise HTTPException(status_code=404, detail="Lecturer not found")


@router.get("", response_model=list[ClassResponse])
def list_classes(_: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    return list(db.scalars(select(Class).order_by(Class.class_code)).all())


@router.get("/{class_id}", response_model=ClassResponse)
def get_class(class_id: str, _: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    return class_or_404(db, class_id)


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(payload: ClassCreate, _: AdminUser, db: Annotated[Session, Depends(get_db)]):
    validate_refs(db, payload.course_id, payload.lecturer_code)
    item = Class(class_id=str(uuid4()), **payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Class code already exists") from None
    db.refresh(item)
    return item


@router.put("/{class_id}", response_model=ClassResponse)
def update_class(class_id: str, payload: ClassUpdate, current_user: LecturerOrAdmin, db: Annotated[Session, Depends(get_db)]):
    item = class_or_404(db, class_id)
    if current_user.role is UserRole.LECTURER and item.lecturer_code != current_user.lecturer.lecturer_code:
        raise HTTPException(status_code=403, detail="You can update only your own classes")
    data = payload.model_dump(exclude_unset=True)
    course_id = data.get("course_id", item.course_id)
    lecturer_code = data.get("lecturer_code", item.lecturer_code)
    validate_refs(db, course_id, lecturer_code)
    if current_user.role is UserRole.LECTURER:
        lecturer_code = current_user.lecturer.lecturer_code
        data["lecturer_code"] = lecturer_code
    for key, value in data.items():
        setattr(item, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Class code already exists") from None
    db.refresh(item)
    return item


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(class_id: str, current_user: LecturerOrAdmin, db: Annotated[Session, Depends(get_db)]):
    item = class_or_404(db, class_id)
    if current_user.role is UserRole.LECTURER and item.lecturer_code != current_user.lecturer.lecturer_code:
        raise HTTPException(status_code=403, detail="You can delete only your own classes")
    db.delete(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Class is referenced by students or sessions") from None
