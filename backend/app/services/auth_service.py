from __future__ import annotations

import bcrypt
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.models.user import User


# JWT settings
SECRET_KEY = "atmograph-secret-key-change-in-production-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt directly."""
    # Ensure password is max 72 bytes for bcrypt
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


class AuthService:
    """Authentication service for user registration, login, and management."""

    def __init__(self, db: Session):
        self.db = db

    def register_user(self, email: str, password: str, company_name: str) -> dict[str, Any]:
        """
        Register a new user.

        Returns a dict with success status and user or error message.
        """
        # Check if email already exists
        existing = self.db.query(User).filter(User.email == email).first()

        if existing:
            return {
                "success": False,
                "error": "Email already registered. Please login instead.",
            }

        # Create new user
        hashed_password = hash_password(password)

        new_user = User(
            email=email,
            password_hash=hashed_password,
            company_name=company_name,
            is_active=True,
        )

        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        # Create access token
        token = create_access_token(
            data={
                "sub": str(new_user.id),
                "email": new_user.email,
                "company_name": new_user.company_name,
            }
        )

        return {
            "success": True,
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "company_name": new_user.company_name,
            },
            "token": token,
        }

    def login_user(self, email: str, password: str) -> dict[str, Any]:
        """
        Login a user.

        Returns a dict with success status and user + token, or error message.
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == email).first()

        if not user:
            return {
                "success": False,
                "error": "Invalid email or password.",
            }

        # Verify password
        if not verify_password(password, user.password_hash):
            return {
                "success": False,
                "error": "Invalid email or password.",
            }

        # Check if user is active
        if not user.is_active:
            return {
                "success": False,
                "error": "Account is deactivated. Please contact support.",
            }

        # Create access token
        token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "company_name": user.company_name,
            }
        )

        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "company_name": user.company_name,
            },
            "token": token,
        }

    def get_user_by_id(self, user_id: int) -> User | None:
        """Get a user by their ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> User | None:
        """Get a user by their email."""
        return self.db.query(User).filter(User.email == email).first()

    def delete_user(self, user_id: int) -> dict[str, Any]:
        """
        Delete a user and all their data.

        This cascades to all user's supply chain data.
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return {
                "success": False,
                "error": "User not found.",
            }

        self.db.delete(user)
        self.db.commit()

        return {
            "success": True,
            "message": "Account deleted successfully.",
        }
