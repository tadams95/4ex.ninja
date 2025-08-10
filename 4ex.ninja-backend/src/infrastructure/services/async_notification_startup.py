"""
Startup script for AsyncNotificationService integration

This script provides initialization code for integrating the AsyncNotificationService
with the existing 4ex.ninja application.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AsyncNotificationStartup:
    """
    Startup helper for AsyncNotificationService.

    This class handles the initialization and lifecycle management
    of the async notification system.
    """

    def __init__(self):
        self.initialized = False
        self.startup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the async notification system."""
        if self.initialized:
            logger.info("AsyncNotificationService already initialized")
            return

        try:
            from infrastructure.services.notification_integration import (
                initialize_async_notifications,
            )

            await initialize_async_notifications()
            self.initialized = True
            logger.info("AsyncNotificationService initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize AsyncNotificationService: {str(e)}")
            # Don't raise - allow application to continue with fallback notifications

    async def shutdown(self):
        """Shutdown the async notification system."""
        if not self.initialized:
            return

        try:
            from infrastructure.services.notification_integration import (
                cleanup_async_notifications,
            )

            await cleanup_async_notifications()
            self.initialized = False
            logger.info("AsyncNotificationService shutdown completed")

        except Exception as e:
            logger.error(f"Error during AsyncNotificationService shutdown: {str(e)}")

    def ensure_started(self):
        """
        Ensure the service is started (for synchronous code).

        This method can be called from synchronous code to ensure
        the notification system is initialized.
        """
        if self.initialized:
            return

        try:
            from infrastructure.services.notification_integration import (
                ensure_async_notifications_started,
            )

            ensure_async_notifications_started()
            self.initialized = True

        except Exception as e:
            logger.error(f"Failed to ensure AsyncNotificationService started: {str(e)}")


# Global startup instance
_async_notification_startup = AsyncNotificationStartup()


def get_async_notification_startup() -> AsyncNotificationStartup:
    """Get the global startup instance."""
    return _async_notification_startup


# Convenience functions
async def startup_async_notifications():
    """Initialize async notifications (async version)."""
    startup = get_async_notification_startup()
    await startup.initialize()


async def shutdown_async_notifications():
    """Shutdown async notifications (async version)."""
    startup = get_async_notification_startup()
    await startup.shutdown()


def ensure_async_notifications():
    """Ensure async notifications are started (sync version)."""
    startup = get_async_notification_startup()
    startup.ensure_started()


# Application lifecycle hooks
async def on_application_startup():
    """Called when the application starts up."""
    logger.info("Initializing AsyncNotificationService on application startup...")
    await startup_async_notifications()


async def on_application_shutdown():
    """Called when the application shuts down."""
    logger.info("Shutting down AsyncNotificationService on application shutdown...")
    await shutdown_async_notifications()


# Strategy lifecycle hooks
def on_strategy_start():
    """Called when a trading strategy starts."""
    logger.info("Ensuring AsyncNotificationService is ready for strategy...")
    ensure_async_notifications()


def on_strategy_stop():
    """Called when a trading strategy stops."""
    # For strategies, we don't shutdown the service as other strategies might be using it
    logger.info("Strategy stopped, AsyncNotificationService remains active")


# Export main functions
__all__ = [
    "AsyncNotificationStartup",
    "get_async_notification_startup",
    "startup_async_notifications",
    "shutdown_async_notifications",
    "ensure_async_notifications",
    "on_application_startup",
    "on_application_shutdown",
    "on_strategy_start",
    "on_strategy_stop",
]
