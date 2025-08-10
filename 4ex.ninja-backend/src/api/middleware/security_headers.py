"""
Security Headers Middleware for FastAPI

Implements comprehensive security headers for production deployment with HTTPS.
This middleware adds essential security headers to protect against common web vulnerabilities.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add comprehensive security headers to all responses.

    Implements OWASP security header recommendations for web applications.
    """

    def __init__(self, app, strict_transport_security: bool = True):
        super().__init__(app)
        self.strict_transport_security = strict_transport_security
        self.is_production = os.getenv("ENVIRONMENT", "development") == "production"

    async def dispatch(self, request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)

        # Basic security headers for all responses
        self._add_basic_security_headers(response)

        # HTTPS-specific headers (only in production with HTTPS)
        if self.strict_transport_security and (
            self.is_production or request.url.scheme == "https"
        ):
            self._add_https_security_headers(response)

        # API-specific headers
        if request.url.path.startswith("/api/"):
            self._add_api_security_headers(response)

        # Authentication endpoint specific headers
        if any(path in request.url.path for path in ["/auth", "/login", "/register"]):
            self._add_auth_security_headers(response)

        return response

    def _add_basic_security_headers(self, response: Response):
        """Add basic security headers that apply to all responses."""

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS Protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (Feature Policy replacement)
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(self), usb=(), interest-cohort=()"
        )

        # Hide server information
        if "Server" in response.headers:
            del response.headers["Server"]

        # Remove FastAPI version header if present
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

    def _add_https_security_headers(self, response: Response):
        """Add HTTPS-specific security headers."""

        # HTTP Strict Transport Security
        # max-age=31536000 (1 year), includeSubDomains, preload
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Expect-CT header for Certificate Transparency
        response.headers["Expect-CT"] = (
            "max-age=86400, enforce, " 'report-uri="https://4ex.ninja/ct-report"'
        )

    def _add_api_security_headers(self, response: Response):
        """Add API-specific security headers."""

        # Content Security Policy for API responses
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; " "frame-ancestors 'none'; " "sandbox"
        )

        # Cache control for API responses
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, private"
            )
            response.headers["Pragma"] = "no-cache"

        # CORS-related security for API
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

    def _add_auth_security_headers(self, response: Response):
        """Add additional security headers for authentication endpoints."""

        # Prevent caching of authentication responses
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, private"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # Additional XSS protection for auth pages
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Clear-Site-Data on logout endpoints
        if "logout" in response.headers.get("X-Request-Path", ""):
            response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS in production.

    Only applies when running behind a reverse proxy that sets proper headers.
    """

    def __init__(self, app, force_https: Optional[bool] = None):
        super().__init__(app)
        self.force_https = (
            force_https
            if force_https is not None
            else (os.getenv("ENVIRONMENT") == "production")
        )

    async def dispatch(self, request: Request, call_next):
        """Redirect HTTP to HTTPS if required."""

        if self.force_https:
            # Check if request came over HTTPS (via reverse proxy headers)
            forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
            is_https = (
                request.url.scheme == "https"
                or forwarded_proto == "https"
                or request.headers.get("X-Forwarded-SSL") == "on"
            )

            if not is_https:
                # Allow health checks and Let's Encrypt challenges over HTTP
                if not (
                    request.url.path.startswith("/health")
                    or request.url.path.startswith("/.well-known/acme-challenge/")
                ):
                    # Redirect to HTTPS
                    https_url = request.url.replace(scheme="https")
                    logger.info(
                        f"Redirecting HTTP request to HTTPS: {request.url} -> {https_url}"
                    )

                    return Response(
                        status_code=301,
                        headers={
                            "Location": str(https_url),
                            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
                        },
                    )

        return await call_next(request)


class SecurityMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring security-related events and potential attacks.
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """Monitor requests for security issues."""

        # Log suspicious request patterns
        self._monitor_request_patterns(request)

        response = await call_next(request)

        # Log security-related responses
        self._monitor_response_patterns(request, response)

        return response

    def _monitor_request_patterns(self, request: Request):
        """Monitor incoming requests for suspicious patterns."""

        # Get client IP safely
        client_ip = "unknown"
        if request.client:
            client_ip = request.client.host

        # Check for common attack patterns in URL
        suspicious_patterns = [
            "../",
            "..\\",
            "/etc/passwd",
            "/proc/",
            "cmd.exe",
            "<script",
            "javascript:",
            "vbscript:",
            "data:",
            "union select",
            "drop table",
            "insert into",
            "%3Cscript",
            "%2e%2e%2f",
            "php://",
            "file://",
        ]

        url_path = str(request.url.path).lower()
        query_string = str(request.url.query).lower()

        for pattern in suspicious_patterns:
            if pattern in url_path or pattern in query_string:
                logger.warning(
                    f"Suspicious request pattern detected: {pattern} "
                    f"from {client_ip} to {request.url.path}"
                )

        # Monitor unusual headers
        suspicious_headers = request.headers.get("User-Agent", "").lower()
        if any(
            bot in suspicious_headers for bot in ["sqlmap", "nikto", "nmap", "dirb"]
        ):
            logger.warning(
                f"Suspicious User-Agent detected: {suspicious_headers} "
                f"from {client_ip}"
            )

        # Monitor for excessive request size
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            logger.warning(
                f"Large request detected: {content_length} bytes "
                f"from {client_ip} to {request.url.path}"
            )

    def _monitor_response_patterns(self, request: Request, response: Response):
        """Monitor responses for security issues."""

        # Get client IP safely
        client_ip = "unknown"
        if request.client:
            client_ip = request.client.host

        # Log failed authentication attempts
        if request.url.path.startswith("/api/v1/auth/") and response.status_code in [
            401,
            403,
        ]:
            logger.warning(
                f"Failed authentication attempt from {client_ip} "
                f"to {request.url.path}"
            )

        # Log rate limiting events
        if response.status_code == 429:
            logger.warning(
                f"Rate limit exceeded by {client_ip} " f"for {request.url.path}"
            )

        # Monitor for potential information disclosure
        if response.status_code == 500:
            logger.error(
                f"Internal server error for request from {client_ip} "
                f"to {request.url.path}"
            )


def create_security_middleware_stack(app):
    """
    Create and configure the complete security middleware stack.

    Args:
        app: FastAPI application instance

    Returns:
        None (middleware is added to the app)
    """

    # Add middleware in reverse order (last added is executed first)

    # 1. Security monitoring (outermost layer)
    app.add_middleware(SecurityMonitoringMiddleware)

    # 2. HTTPS redirect (before security headers)
    app.add_middleware(HTTPSRedirectMiddleware)

    # 3. Security headers (applied to all responses)
    app.add_middleware(SecurityHeadersMiddleware)

    logger.info("Security middleware stack configured successfully")
