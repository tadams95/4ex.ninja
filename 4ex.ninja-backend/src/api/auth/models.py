"""
Authentication models for 4ex.ninja API.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """User model for API responses."""

    id: str
    email: str
    username: Optional[str] = None
    is_active: bool = True
    is_premium: bool = False


class UserInDB(User):
    """User model with hashed password for database storage."""

    hashed_password: str


class UserCreate(BaseModel):
    """User creation model."""

    email: EmailStr
    username: Optional[str] = None
    password: str


class UserLogin(BaseModel):
    """User login model."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data model for JWT payload."""

    user_id: Optional[str] = None
    email: Optional[str] = None
