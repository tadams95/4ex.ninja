"""
Authentication routes for 4ex.ninja API.

Provides login, registration, and token management endpoints.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import logging

from ..auth.jwt_auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)
from ..auth.models import Token, User, UserCreate, UserLogin
from ..auth.config import auth_settings
from ..middleware.rate_limiting import create_rate_limit_dependency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Create rate limiting dependencies for auth endpoints
auth_rate_limit = create_rate_limit_dependency(
    auth_settings.AUTH_RATE_LIMIT_REQUESTS, auth_settings.AUTH_RATE_LIMIT_WINDOW
)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), _: None = Depends(auth_rate_limit)
):
    """
    OAuth2 compatible token login endpoint.

    Creates an access token for valid user credentials.
    """
    try:
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.warning(f"Authentication failed for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(
            minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email},
            expires_delta=access_token_expires,
        )

        logger.info(f"User {user.email} authenticated successfully")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


@router.post("/login", response_model=Token)
async def login(user_login: UserLogin, _: None = Depends(auth_rate_limit)):
    """
    Login endpoint using JSON payload.

    Creates an access token for valid user credentials.
    """
    try:
        user = authenticate_user(user_login.email, user_login.password)
        if not user:
            logger.warning(f"Login failed for user: {user_login.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        access_token_expires = timedelta(
            minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email},
            expires_delta=access_token_expires,
        )

        logger.info(f"User {user.email} logged in successfully")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


@router.post("/register", response_model=Token)
async def register(user_create: UserCreate, _: None = Depends(auth_rate_limit)):
    """
    User registration endpoint.

    Creates a new user account and returns an access token.
    Note: This is a simplified implementation for demonstration.
    """
    try:
        # In a real application, you would:
        # 1. Check if user already exists
        # 2. Validate email format (already done by Pydantic)
        # 3. Validate password strength
        # 4. Store user in database
        # 5. Send email verification

        # For demo purposes, we'll just create a token
        if user_create.email == "demo@4ex.ninja":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
            )

        # Create new user (simplified)
        hashed_password = get_password_hash(user_create.password)
        new_user_id = f"user-{hash(user_create.email) % 1000000}"

        access_token_expires = timedelta(
            minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": new_user_id, "email": user_create.email},
            expires_delta=access_token_expires,
        )

        logger.info(f"New user registered: {user_create.email}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration service error",
        )


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.

    Returns the authenticated user's profile information.
    """
    return current_user


@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """
    Refresh access token.

    Creates a new access token for the authenticated user.
    """
    try:
        access_token_expires = timedelta(
            minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": current_user.id, "email": current_user.email},
            expires_delta=access_token_expires,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )
