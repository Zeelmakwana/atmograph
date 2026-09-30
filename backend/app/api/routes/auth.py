from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_database
from app.models.user import User
from app.services.auth_service import AuthService, decode_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

security = HTTPBearer()


# ============================================================
# REQUEST SCHEMAS
# ============================================================


class RegisterRequest(BaseModel):
    email: str
    password: str
    company_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    company_name: str


class AuthResponse(BaseModel):
    success: bool
    user: UserResponse | None = None
    token: str | None = None
    error: str | None = None


# ============================================================
# PUBLIC ROUTES (NO AUTH REQUIRED)
# ============================================================


@router.post("/register", response_model=AuthResponse)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_database),
) -> dict[str, Any]:
    """
    Register a new user account.

    Returns:
        - success: True if registration succeeded
        - user: User details (id, email, company_name)
        - token: JWT token for immediate login
        - error: Error message if registration failed
    """
    auth_service = AuthService(db)

    result = auth_service.register_user(
        email=request.email,
        password=request.password,
        company_name=request.company_name,
    )

    return result


@router.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_database),
) -> dict[str, Any]:
    """
    Login an existing user.

    Returns:
        - success: True if login succeeded
        - user: User details (id, email, company_name)
        - token: JWT token for authentication
        - error: Error message if login failed
    """
    auth_service = AuthService(db)

    result = auth_service.login_user(
        email=request.email,
        password=request.password,
    )

    return result


# ============================================================
# PROTECTED ROUTES (AUTH REQUIRED)
# ============================================================


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get the current logged-in user's profile.

    Requires Authorization header with Bearer token.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "company_name": current_user.company_name,
    }


@router.delete("/account")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
) -> dict[str, Any]:
    """
    Delete the current user's account and all their data.

    This is irreversible and removes all supply chain data.
    """
    auth_service = AuthService(db)

    result = auth_service.delete_user(current_user.id)

    return result
