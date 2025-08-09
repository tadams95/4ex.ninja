"""
Authentication package for 4ex.ninja API.

This package provides JWT-based authentication, password hashing,
and security utilities for the trading platform API.
"""

from .jwt_auth import (
    create_access_token,
    verify_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from .models import TokenData, UserInDB, User
from .config import AuthSettings

__all__ = [
    "create_access_token",
    "verify_token",
    "get_current_user",
    "get_password_hash",
    "verify_password",
    "TokenData",
    "UserInDB",
    "User",
    "AuthSettings",
]
