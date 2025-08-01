"""
Error Tracking and Monitoring

Sentry-based error tracking with categorization and context.
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

# Try to import Sentry, but make it optional
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


class ErrorCategory(Enum):
    """Categories for error classification."""

    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    BUSINESS_LOGIC_ERROR = "business_logic_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"


class ErrorSeverity(Enum):
    """Error severity levels."""

    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class SentryErrorTracker:
    """Enhanced error tracking with Sentry integration."""

    def __init__(self, dsn: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.dsn = dsn
        self._initialized = False

        if dsn and SENTRY_AVAILABLE:
            self.initialize(dsn)

    def initialize(self, dsn: str, environment: str = "development") -> None:
        """Initialize Sentry SDK with configuration."""
        if not SENTRY_AVAILABLE:
            self.logger.warning("Sentry SDK not available")
            return

        try:
            sentry_sdk.init(
                dsn=dsn,
                environment=environment,
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                send_default_pii=True,  # Include request headers and IP for users
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
                ],
            )
            self._initialized = True
            self.logger.info("Sentry error tracking initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Sentry: {e}")
            self._initialized = False

    def capture_error(
        self,
        exception: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Capture an exception with enhanced context."""

        if not self._initialized:
            self.logger.error(f"Sentry not initialized. Error: {exception}")
            return None

        try:
            # Set scope with additional context
            with sentry_sdk.push_scope() as scope:
                # Set error category and severity
                scope.set_tag("error_category", category.value)
                scope.set_level(severity.value)

                # Add extra context
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)

                # Capture the exception
                event_id = sentry_sdk.capture_exception(exception)

                self.logger.info(f"Exception captured in Sentry: {event_id}")
                return event_id

        except Exception as e:
            self.logger.error(f"Failed to capture exception in Sentry: {e}")
            return None

    def capture_api_error(
        self,
        exception: Exception,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
    ) -> Optional[str]:
        """Capture API-related errors."""
        return self.capture_error(
            exception=exception,
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.ERROR,
            context={"endpoint": endpoint, "method": method, "user_id": user_id},
        )

    def capture_database_error(
        self, exception: Exception, operation: str, collection: Optional[str] = None
    ) -> Optional[str]:
        """Capture database-related errors."""
        return self.capture_error(
            exception=exception,
            category=ErrorCategory.DATABASE_ERROR,
            severity=ErrorSeverity.ERROR,
            context={"operation": operation, "collection": collection},
        )

    def capture_business_logic_error(
        self,
        exception: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Capture business logic errors."""
        return self.capture_error(
            exception=exception,
            category=ErrorCategory.BUSINESS_LOGIC_ERROR,
            severity=ErrorSeverity.WARNING,
            context={"operation": operation, **(context or {})},
        )

    def capture_external_service_error(
        self, exception: Exception, service: str, endpoint: str
    ) -> Optional[str]:
        """Capture external service errors."""
        return self.capture_error(
            exception=exception,
            category=ErrorCategory.EXTERNAL_SERVICE_ERROR,
            severity=ErrorSeverity.ERROR,
            context={"service": service, "endpoint": endpoint},
        )

    def is_initialized(self) -> bool:
        """Check if Sentry is initialized."""
        return self._initialized


# Global error tracker instance
error_tracker = SentryErrorTracker()


def initialize_error_tracking(dsn: str, environment: str = "development") -> None:
    """Initialize global error tracking."""
    error_tracker.initialize(dsn, environment)
