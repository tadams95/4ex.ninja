"""
JWT authentication utilities for 4ex.ninja API.

Provides JWT token creation, verification, and password hashing utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from .config import auth_settings
from .models import TokenData, User, UserInDB

logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(
            to_encode, auth_settings.get_secret_key(), algorithm=auth_settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token",
        )


def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify

    Returns:
        TokenData containing user information

    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, auth_settings.get_secret_key(), algorithms=[auth_settings.ALGORITHM]
        )

        user_id = payload.get("sub")
        email = payload.get("email")

        if user_id is None:
            raise credentials_exception

        token_data = TokenData(user_id=user_id, email=email)
        return token_data

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise credentials_exception


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """
    Get the current authenticated user from JWT token.

    This is a simplified version that creates a User object from the token.
    In a real application, you would fetch the user from a database.

    Args:
        credentials: HTTP authorization credentials from request

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_token(credentials.credentials)

    # Ensure we have valid user data
    if not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In a real application, you would fetch user from database here
    # For now, we'll create a minimal user object from token data
    user = User(
        id=token_data.user_id,
        email=token_data.email or "unknown@example.com",
        username=(token_data.email.split("@")[0] if token_data.email else "unknown"),
        is_active=True,
        is_premium=False,
    )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user (additional check for user status).

    Args:
        current_user: Current user from get_current_user

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return current_user


def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate a user with email and password.

    This is a simplified mock implementation.
    In a real application, you would check against a database.

    Args:
        email: User email
        password: Plain text password

    Returns:
        UserInDB if authentication successful, None otherwise
    """
    # Mock user for demonstration - replace with database lookup
    if email == "demo@4ex.ninja" and password == "demo123":
        return UserInDB(
            id="demo-user-123",
            email=email,
            username="demo",
            is_active=True,
            is_premium=True,
            hashed_password=get_password_hash(password),
        )

    return None
