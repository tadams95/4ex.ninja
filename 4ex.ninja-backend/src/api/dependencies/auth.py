"""
Authentication dependencies for 4ex.ninja API.

Provides authentication dependencies and decorators for protecting endpoints.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from ..auth.jwt_auth import get_current_user, get_current_active_user
from ..auth.models import User
from ..auth.config import auth_settings

logger = logging.getLogger(__name__)

# Security scheme for API key authentication
security = HTTPBearer(auto_error=False)


async def verify_api_key(request: Request) -> bool:
    """
    Verify API key from request headers.

    Args:
        request: FastAPI request object

    Returns:
        True if API key is valid, False otherwise
    """
    api_key = request.headers.get(auth_settings.API_KEY_HEADER)

    if not api_key:
        return False

    # Check if API key is in the list of valid keys
    if auth_settings.VALID_API_KEYS and api_key in auth_settings.VALID_API_KEYS:
        return True

    return False


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """
    Get current user from JWT token (optional).

    Returns None if no valid authentication is provided.
    Used for endpoints that can work with or without authentication.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        user = await get_current_user(credentials)
        return user
    except HTTPException:
        return None


async def require_auth_or_api_key(
    request: Request, current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """
    Require either JWT authentication or valid API key.

    This dependency allows access via either method:
    1. JWT Bearer token in Authorization header
    2. API key in X-API-Key header

    Args:
        request: FastAPI request object
        current_user: Current authenticated user (if any)

    Returns:
        User object (real user for JWT, synthetic user for API key)

    Raises:
        HTTPException: If neither authentication method is valid
    """
    # Check JWT authentication first
    if current_user:
        return current_user

    # Check API key authentication
    if await verify_api_key(request):
        # Create a synthetic user for API key access
        return User(
            id="api-key-user",
            email="api@4ex.ninja",
            username="api",
            is_active=True,
            is_premium=True,  # API keys get premium access
        )

    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either a Bearer token or API key.",
        headers={
            "WWW-Authenticate": "Bearer",
            "X-Required-Headers": auth_settings.API_KEY_HEADER,
        },
    )


async def require_premium_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Require premium user access.

    Args:
        current_user: Current authenticated user

    Returns:
        Premium user object

    Raises:
        HTTPException: If user is not premium
    """
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required for this endpoint",
        )

    return current_user


# Authentication dependency aliases for common use cases
RequireAuth = Depends(get_current_active_user)
OptionalAuth = Depends(get_current_user_optional)
RequireAuthOrApiKey = Depends(require_auth_or_api_key)
RequirePremium = Depends(require_premium_user)
