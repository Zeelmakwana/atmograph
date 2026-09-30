from __future__ import annotations

from collections.abc import Generator
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService, decode_token

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_database() -> Generator[Session, None, None]:
    """Provide a database session to FastAPI routes."""
    yield from get_db()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database),
) -> User:
    """
    Extract and validate the current user from JWT token.
    Throws 401 if missing or invalid.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please login again.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload. Please login again.",
        )

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(int(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please register first.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated. Please contact support.",
        )

    return user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional),
    db: Session = Depends(get_database),
) -> User | None:
    """
    Extract the current user if a valid Bearer token is provided.
    Returns None if unauthenticated without raising 401.
    """
    if not credentials:
        return None

    token = credentials.credentials
    if not token:
        return None

    payload = decode_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return None

    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id_int)

    if not user or not user.is_active:
        return None

    return user
