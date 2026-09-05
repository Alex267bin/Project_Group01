from uuid import uuid4
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser, require_role
from app.core.security import hash_password
from app.db.dependencies import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["users"])
AdminUser = Annotated[CurrentUser, Depends(require_role(UserRole.ADMIN))]


def get_user_or_404(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("", response_model=list[UserResponse])
def list_users(_: AdminUser, db: Annotated[Session, Depends(get_db)]):
    return list(db.scalars(select(User).order_by(User.username)).all())


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, _: AdminUser, db: Annotated[Session, Depends(get_db)]):
    return get_user_or_404(db, user_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, _: AdminUser, db: Annotated[Session, Depends(get_db)]):
    user = User(
        user_id=str(uuid4()),
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        email=str(payload.email),
        role=payload.role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username or email already exists") from None
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, payload: UserUpdate, _: AdminUser, db: Annotated[Session, Depends(get_db)]):
    user = get_user_or_404(db, user_id)
    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        data["password_hash"] = hash_password(data.pop("password"))
    for key, value in data.items():
        setattr(user, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username or email already exists") from None
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, _: AdminUser, db: Annotated[Session, Depends(get_db)]):
    user = get_user_or_404(db, user_id)
    db.delete(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User is referenced by another profile") from None
