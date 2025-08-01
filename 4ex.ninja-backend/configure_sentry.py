"""
Sentry Configuration for 4ex.ninja

Initialize Sentry error tracking with your specific DSN.
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

try:
    from infrastructure.monitoring.error_tracking import initialize_error_tracking  # type: ignore
except ImportError:
    print("Warning: Unable to import error_tracking module")
    initialize_error_tracking = None

# Your Sentry DSN from the setup
SENTRY_DSN = "https://255fd05fd3c0d2e90c377b42829e8e5d@o4509766501990400.ingest.us.sentry.io/4509766604029952"


def configure_sentry(environment: str = "development") -> None:
    """Configure Sentry for the application."""

    if initialize_error_tracking is None:
        print("❌ Error: Cannot configure Sentry - module not available")
        return

    initialize_error_tracking(dsn=SENTRY_DSN, environment=environment)

    print(f"✅ Sentry configured for environment: {environment}")
    print(f"🔍 DSN: {SENTRY_DSN[:50]}...")


if __name__ == "__main__":
    # Test configuration
    configure_sentry("development")
