"""
Authentication configuration for 4ex.ninja API.
"""

import os
from typing import Optional


class AuthSettings:
    """Authentication configuration settings."""

    # JWT Configuration
    SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "4ex-ninja-super-secret-key-change-in-production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # Rate Limiting Configuration
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour

    # Auth rate limiting (more restrictive)
    AUTH_RATE_LIMIT_REQUESTS: int = int(os.getenv("AUTH_RATE_LIMIT_REQUESTS", "10"))
    AUTH_RATE_LIMIT_WINDOW: int = int(
        os.getenv("AUTH_RATE_LIMIT_WINDOW", "900")
    )  # 15 minutes

    # API Key Configuration (for simple API access)
    API_KEY_HEADER: str = "X-API-Key"
    VALID_API_KEYS: set = set(filter(None, os.getenv("VALID_API_KEYS", "").split(",")))

    @classmethod
    def get_secret_key(cls) -> str:
        """Get the JWT secret key, ensuring it's set in production."""
        if (
            os.getenv("ENVIRONMENT") == "production"
            and cls.SECRET_KEY == "4ex-ninja-super-secret-key-change-in-production"
        ):
            raise ValueError("JWT_SECRET_KEY must be set in production environment")
        return cls.SECRET_KEY


# Create a global instance
auth_settings = AuthSettings()
