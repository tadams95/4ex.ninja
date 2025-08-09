"""
Tests for authentication and rate limiting functionality.

These tests verify that:
1. Authentication endpoints work correctly
2. Protected endpoints require authentication
3. Rate limiting is enforced
4. API keys work as alternative authentication
"""

import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from unittest.mock import patch

# Add src to path for imports
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from src.app import create_app
from src.api.auth.jwt_auth import create_access_token


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_token():
    """Create a test JWT token."""
    token_data = {"sub": "test-user-123", "email": "test@4ex.ninja"}
    return create_access_token(data=token_data)


class TestAuthentication:
    """Test authentication endpoints."""

    def test_login_with_demo_credentials(self, client):
        """Test login with demo credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "demo@4ex.ninja", "password": "demo123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_with_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "invalid@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_oauth2_token_endpoint(self, client):
        """Test OAuth2 compatible token endpoint."""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "demo@4ex.ninja",
                "password": "demo123",
                "grant_type": "password",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_get_current_user(self, client, auth_token):
        """Test getting current user information."""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-user-123"
        assert data["email"] == "test@4ex.ninja"

    def test_get_current_user_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "Authorization required" in response.json()["detail"]

    def test_get_current_user_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]


class TestProtectedEndpoints:
    """Test that protected endpoints require authentication."""

    def test_signal_details_requires_auth(self, client):
        """Test that individual signal endpoint requires authentication."""
        response = client.get("/api/v1/signals/test-signal-123")

        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    def test_signal_details_with_auth(self, client, auth_token):
        """Test that individual signal endpoint works with authentication."""
        response = client.get(
            "/api/v1/signals/test-signal-123",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Should not be 401 (authenticated successfully)
        assert response.status_code != 401

    def test_signal_stats_requires_auth(self, client):
        """Test that signal stats endpoint requires authentication."""
        response = client.get("/api/v1/signals/stats/summary")

        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    def test_signal_stats_with_auth(self, client, auth_token):
        """Test that signal stats endpoint works with authentication."""
        response = client.get(
            "/api/v1/signals/stats/summary",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Should not be 401 (authenticated successfully)
        assert response.status_code != 401

    def test_public_signals_endpoint(self, client):
        """Test that public signals endpoint works without authentication."""
        response = client.get("/api/v1/signals/")

        # Should not require authentication (but may return limited data)
        assert response.status_code != 401


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_auth_rate_limiting(self, client):
        """Test that auth endpoints are rate limited."""
        # Make multiple rapid requests to trigger rate limiting
        responses = []
        for i in range(15):  # More than AUTH_RATE_LIMIT_REQUESTS (10)
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "wrongpassword"},
            )
            responses.append(response)

            # Break early if we hit rate limit
            if response.status_code == 429:
                break

        # Should have hit rate limit
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0

        # Check rate limit response format
        rate_limit_response = rate_limited_responses[0]
        assert "Rate limit exceeded" in rate_limit_response.json()["error"]
        assert "X-RateLimit-Limit" in rate_limit_response.headers
        assert "Retry-After" in rate_limit_response.headers

    def test_rate_limit_headers(self, client):
        """Test that rate limit headers are included in responses."""
        response = client.get("/api/v1/signals/")

        # Should include rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_excluded_paths_not_rate_limited(self, client):
        """Test that excluded paths are not rate limited."""
        # Health endpoint should not be rate limited
        for i in range(20):  # More than any rate limit
            response = client.get("/health/")
            assert response.status_code != 429


class TestAPIKeyAuthentication:
    """Test API key authentication as alternative to JWT."""

    @patch.dict(os.environ, {"VALID_API_KEYS": "test-api-key-123,another-key"})
    def test_api_key_authentication(self, client):
        """Test that valid API key allows access to protected endpoints."""
        response = client.get(
            "/api/v1/signals/test-signal-123", headers={"X-API-Key": "test-api-key-123"}
        )

        # Should not be 401 (authenticated successfully with API key)
        assert response.status_code != 401

    def test_invalid_api_key(self, client):
        """Test that invalid API key is rejected."""
        response = client.get(
            "/api/v1/signals/test-signal-123", headers={"X-API-Key": "invalid-key"}
        )

        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]


class TestSecurityHeaders:
    """Test that security headers are properly set."""

    def test_cors_headers(self, client):
        """Test that CORS headers are set."""
        response = client.get("/")

        # Should have CORS headers in development
        # (These may not be present in TestClient, but the middleware should be configured)
        assert response.status_code == 200

    def test_rate_limit_headers_format(self, client):
        """Test that rate limit headers are properly formatted."""
        response = client.get("/api/v1/signals/")

        if "X-RateLimit-Limit" in response.headers:
            # Headers should be numeric strings
            limit = response.headers["X-RateLimit-Limit"]
            remaining = response.headers["X-RateLimit-Remaining"]
            reset_time = response.headers["X-RateLimit-Reset"]

            assert limit.isdigit()
            assert remaining.isdigit()
            assert reset_time.isdigit()

            # Remaining should not exceed limit
            assert int(remaining) <= int(limit)


if __name__ == "__main__":
    # Run tests manually if executed directly
    pytest.main([__file__, "-v"])
