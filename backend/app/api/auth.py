from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_access_token
from app.db.dependencies import get_db
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth import authenticate_user


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> LoginResponse:
    user = authenticate_user(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_in = create_access_token(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
    )
    return LoginResponse(
        authenticated=True,
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise authentication_error()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            raise authentication_error()
    except (JWTError, RuntimeError):
        raise authentication_error() from None

    user = db.scalar(select(User).where(User.user_id == user_id))
    if user is None:
        raise authentication_error()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*allowed_roles: UserRole) -> Callable:
    def role_dependency(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_dependency