"""
Database Operation Error Handling Module

This module provides comprehensive error handling for database operations,
including connection pool management, retry logic, transaction rollback,
and data validation.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
import random

# Set up logging
logger = logging.getLogger(__name__)

# Import MongoDB specific modules with fallback
try:
    from pymongo.errors import (
        PyMongoError as _PyMongoError,
        ConnectionFailure as _ConnectionFailure,
        ServerSelectionTimeoutError as _ServerSelectionTimeoutError,
        DuplicateKeyError as _DuplicateKeyError,
        BulkWriteError as _BulkWriteError,
        WriteError as _WriteError,
        WriteConcernError as _WriteConcernError,
        OperationFailure as _OperationFailure,
        InvalidOperation as _InvalidOperation,
        NetworkTimeout as _NetworkTimeout,
        AutoReconnect as _AutoReconnect,
    )
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection  # type: ignore

    PYMONGO_AVAILABLE = True

    # Use actual pymongo exceptions
    PyMongoError = _PyMongoError  # type: ignore
    ConnectionFailure = _ConnectionFailure  # type: ignore
    ServerSelectionTimeoutError = _ServerSelectionTimeoutError  # type: ignore
    DuplicateKeyError = _DuplicateKeyError  # type: ignore
    BulkWriteError = _BulkWriteError  # type: ignore
    WriteError = _WriteError  # type: ignore
    WriteConcernError = _WriteConcernError  # type: ignore
    OperationFailure = _OperationFailure  # type: ignore
    InvalidOperation = _InvalidOperation  # type: ignore
    NetworkTimeout = _NetworkTimeout  # type: ignore
    AutoReconnect = _AutoReconnect  # type: ignore

except ImportError:
    # Fallback classes for when pymongo/motor is not installed
    PYMONGO_AVAILABLE = False

    class PyMongoError(Exception):
        pass

    class ConnectionFailure(PyMongoError):
        pass

    class ServerSelectionTimeoutError(PyMongoError):
        pass

    class DuplicateKeyError(PyMongoError):
        pass

    class BulkWriteError(PyMongoError):
        pass

    class WriteError(PyMongoError):
        pass

    class WriteConcernError(PyMongoError):
        pass

    class OperationFailure(PyMongoError):
        pass

    class InvalidOperation(PyMongoError):
        pass

    class NetworkTimeout(PyMongoError):
        pass

    class AutoReconnect(PyMongoError):
        pass

    AsyncIOMotorClient = None  # type: ignore
    AsyncIOMotorDatabase = None  # type: ignore
    AsyncIOMotorCollection = None  # type: ignore


class DatabaseErrorType(Enum):
    """Enumeration of database error types."""

    CONNECTION_FAILURE = "connection_failure"
    TIMEOUT = "timeout"
    DUPLICATE_KEY = "duplicate_key"
    WRITE_CONCERN = "write_concern"
    BULK_WRITE_ERROR = "bulk_write_error"
    OPERATION_FAILURE = "operation_failure"
    INVALID_OPERATION = "invalid_operation"
    NETWORK_ERROR = "network_error"
    AUTO_RECONNECT = "auto_reconnect"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    DATA_VALIDATION = "data_validation"
    CONSTRAINT_VIOLATION = "constraint_violation"


class DatabaseErrorSeverity(Enum):
    """Enumeration of database error severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DatabaseError:
    """Represents a database operation error with context."""

    error_type: DatabaseErrorType
    severity: DatabaseErrorSeverity
    message: str
    timestamp: datetime
    context: Dict[str, Any]
    collection: Optional[str] = None
    operation: Optional[str] = None
    retry_count: int = 0
    recovery_attempted: bool = False
    recovery_successful: bool = False


class ConnectionPoolManager:
    """Manages MongoDB connection pool with health monitoring and recovery."""

    def __init__(
        self, connection_string: str, pool_size: int = 10, max_pool_size: int = 50
    ):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.max_pool_size = max_pool_size
        self.client: Optional[Any] = None  # AsyncIOMotorClient when available
        self.database: Optional[Any] = None  # AsyncIOMotorDatabase when available
        self.connection_failures = 0
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds
        self.max_connection_failures = 5
        self.connection_timeout = 10  # seconds
        self.server_selection_timeout = 5  # seconds

    async def initialize(self, database_name: str) -> bool:
        """Initialize the connection pool."""
        try:
            if AsyncIOMotorClient is None:
                logger.error("Motor/PyMongo not available")
                return False

            self.client = AsyncIOMotorClient(
                self.connection_string,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.pool_size,
                connectTimeoutMS=self.connection_timeout * 1000,
                serverSelectionTimeoutMS=self.server_selection_timeout * 1000,
                retryWrites=True,
                retryReads=True,
            )

            # Test connection
            if self.client:
                await self.client.admin.command("ping")  # type: ignore
                self.database = self.client[database_name]  # type: ignore

            logger.info(f"Database connection pool initialized: {database_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {str(e)}")
            self.connection_failures += 1
            return False

    async def get_database(
        self,
    ) -> Optional[Any]:  # AsyncIOMotorDatabase when available
        """Get database connection with health check."""
        if not await self.is_healthy():
            if not await self.reconnect():
                return None

        return self.database

    async def is_healthy(self) -> bool:
        """Check if database connection is healthy."""
        current_time = time.time()

        # Skip frequent health checks
        if current_time - self.last_health_check < self.health_check_interval:
            return self.database is not None

        self.last_health_check = current_time

        if not self.client or not self.database:
            return False

        try:
            # Simple ping to check connectivity
            await self.client.admin.command("ping")
            self.connection_failures = 0  # Reset failure count on success
            return True

        except Exception as e:
            logger.warning(f"Database health check failed: {str(e)}")
            self.connection_failures += 1
            return False

    async def reconnect(self) -> bool:
        """Attempt to reconnect to database."""
        if self.connection_failures >= self.max_connection_failures:
            logger.error(
                "Maximum connection failures reached, not attempting reconnect"
            )
            return False

        try:
            if self.client:
                self.client.close()

            # Re-initialize connection
            return await self.initialize(
                self.database.name if self.database else "default"
            )

        except Exception as e:
            logger.error(f"Reconnection failed: {str(e)}")
            return False

    async def close(self):
        """Close database connections."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None


class DatabaseErrorHandler:
    """Centralized error handling for database operations."""

    def __init__(self, connection_pool: ConnectionPoolManager):
        self.connection_pool = connection_pool
        self.error_history: List[DatabaseError] = []
        self.max_retry_attempts = 3
        self.retry_backoff_base = 1.0
        self.retry_backoff_multiplier = 2.0
        self.max_backoff_delay = 30.0

        # Error type to retry mapping
        self.retryable_errors = {
            DatabaseErrorType.CONNECTION_FAILURE,
            DatabaseErrorType.TIMEOUT,
            DatabaseErrorType.NETWORK_ERROR,
            DatabaseErrorType.AUTO_RECONNECT,
        }

    async def handle_error(self, error: DatabaseError) -> bool:
        """
        Handle a database error with appropriate recovery strategy.

        Args:
            error: The DatabaseError to handle

        Returns:
            bool: True if error was recovered successfully, False otherwise
        """
        logger.error(f"Database error: {error.error_type.value} - {error.message}")

        # Add to error history
        self.error_history.append(error)

        # Determine if error is retryable
        if error.error_type not in self.retryable_errors:
            logger.info(f"Error type {error.error_type.value} is not retryable")
            return False

        # Check retry limit
        if error.retry_count >= self.max_retry_attempts:
            logger.error(f"Maximum retry attempts ({self.max_retry_attempts}) reached")
            return False

        # Attempt recovery
        return await self._attempt_recovery(error)

    async def _attempt_recovery(self, error: DatabaseError) -> bool:
        """Attempt to recover from database error."""
        error.recovery_attempted = True

        try:
            # Calculate backoff delay
            delay = min(
                self.retry_backoff_base
                * (self.retry_backoff_multiplier**error.retry_count),
                self.max_backoff_delay,
            )

            # Add jitter to prevent thundering herd
            jitter = random.uniform(0.1, 0.3) * delay
            delay += jitter

            logger.info(
                f"Attempting recovery after {delay:.2f} seconds (attempt {error.retry_count + 1})"
            )
            await asyncio.sleep(delay)

            # Perform recovery based on error type
            recovery_success = False

            if error.error_type in [
                DatabaseErrorType.CONNECTION_FAILURE,
                DatabaseErrorType.NETWORK_ERROR,
            ]:
                recovery_success = await self._recover_connection_failure(error)

            elif error.error_type == DatabaseErrorType.TIMEOUT:
                recovery_success = await self._recover_timeout(error)

            elif error.error_type == DatabaseErrorType.AUTO_RECONNECT:
                recovery_success = await self._recover_auto_reconnect(error)

            else:
                # Generic retry for other retryable errors
                recovery_success = True

            error.recovery_successful = recovery_success
            return recovery_success

        except Exception as e:
            logger.error(f"Recovery attempt failed: {str(e)}")
            return False

    async def _recover_connection_failure(self, error: DatabaseError) -> bool:
        """Recover from connection failure."""
        logger.info("Attempting to recover from connection failure")
        return await self.connection_pool.reconnect()

    async def _recover_timeout(self, error: DatabaseError) -> bool:
        """Recover from timeout error."""
        logger.info("Attempting to recover from timeout")

        # Check if connection is still healthy
        if not await self.connection_pool.is_healthy():
            return await self.connection_pool.reconnect()

        return True

    async def _recover_auto_reconnect(self, error: DatabaseError) -> bool:
        """Recover from auto-reconnect event."""
        logger.info("Handling auto-reconnect event")

        # Wait for auto-reconnect to complete
        await asyncio.sleep(1.0)
        return await self.connection_pool.is_healthy()

    def classify_error(self, exception: Exception) -> DatabaseError:
        """Classify an exception into a DatabaseError."""
        error_type = DatabaseErrorType.OPERATION_FAILURE
        severity = DatabaseErrorSeverity.MEDIUM

        # Classify by exception type
        if isinstance(exception, ConnectionFailure):
            error_type = DatabaseErrorType.CONNECTION_FAILURE
            severity = DatabaseErrorSeverity.HIGH

        elif isinstance(exception, ServerSelectionTimeoutError):
            error_type = DatabaseErrorType.TIMEOUT
            severity = DatabaseErrorSeverity.HIGH

        elif isinstance(exception, NetworkTimeout):
            error_type = DatabaseErrorType.NETWORK_ERROR
            severity = DatabaseErrorSeverity.MEDIUM

        elif isinstance(exception, AutoReconnect):
            error_type = DatabaseErrorType.AUTO_RECONNECT
            severity = DatabaseErrorSeverity.MEDIUM

        elif isinstance(exception, DuplicateKeyError):
            error_type = DatabaseErrorType.DUPLICATE_KEY
            severity = DatabaseErrorSeverity.LOW

        elif isinstance(exception, BulkWriteError):
            error_type = DatabaseErrorType.BULK_WRITE_ERROR
            severity = DatabaseErrorSeverity.MEDIUM

        elif isinstance(exception, WriteConcernError):
            error_type = DatabaseErrorType.WRITE_CONCERN
            severity = DatabaseErrorSeverity.HIGH

        elif isinstance(exception, InvalidOperation):
            error_type = DatabaseErrorType.INVALID_OPERATION
            severity = DatabaseErrorSeverity.MEDIUM

        return DatabaseError(
            error_type=error_type,
            severity=severity,
            message=str(exception),
            timestamp=datetime.now(timezone.utc),
            context={"exception_type": type(exception).__name__},
        )

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get database error statistics."""
        if not self.error_history:
            return {}

        total_errors = len(self.error_history)
        error_by_type = {}
        error_by_severity = {}
        recovery_success_rate = 0

        for error in self.error_history:
            # Count by type
            error_type = error.error_type.value
            error_by_type[error_type] = error_by_type.get(error_type, 0) + 1

            # Count by severity
            severity = error.severity.value
            error_by_severity[severity] = error_by_severity.get(severity, 0) + 1

            # Count recovery attempts
            if error.recovery_attempted and error.recovery_successful:
                recovery_success_rate += 1

        if recovery_success_rate > 0:
            recovery_success_rate = recovery_success_rate / total_errors * 100

        return {
            "total_errors": total_errors,
            "errors_by_type": error_by_type,
            "errors_by_severity": error_by_severity,
            "recovery_success_rate": recovery_success_rate,
            "connection_failures": self.connection_pool.connection_failures,
        }


def database_operation(operation_name: str, collection_name: Optional[str] = None):
    """
    Decorator for database operations to handle errors gracefully.

    Args:
        operation_name: Name of the database operation
        collection_name: Name of the collection being operated on
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to get error handler from first argument (usually self)
            error_handler = getattr(
                args[0] if args else None, "_db_error_handler", None
            )

            if not error_handler:
                # Create default error handler if not available
                logger.warning("No database error handler found, using default")
                # Cannot handle without proper setup
                return await func(*args, **kwargs)

            max_attempts = 3

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)

                except PyMongoError as e:
                    db_error = error_handler.classify_error(e)
                    db_error.operation = operation_name
                    db_error.collection = collection_name
                    db_error.retry_count = attempt

                    # For last attempt, don't try to recover
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Database operation {operation_name} failed after {max_attempts} attempts"
                        )
                        raise

                    # Attempt recovery
                    recovery_success = await error_handler.handle_error(db_error)

                    if not recovery_success:
                        logger.error(
                            f"Recovery failed for {operation_name}, attempt {attempt + 1}"
                        )
                        # Continue to next attempt anyway
                        continue

                    logger.info(
                        f"Recovery successful for {operation_name}, retrying..."
                    )
                    # Continue to retry

                except Exception as e:
                    # Non-database errors should be handled by calling code
                    logger.error(f"Non-database error in {operation_name}: {str(e)}")
                    raise

            # Should not reach here
            raise RuntimeError(
                f"Database operation {operation_name} failed after all recovery attempts"
            )

        return wrapper

    return decorator


class TransactionManager:
    """Manages database transactions with rollback capability."""

    def __init__(
        self, database: Any, error_handler: DatabaseErrorHandler
    ):  # AsyncIOMotorDatabase when available
        self.database = database
        self.error_handler = error_handler
        self.session = None
        self.transaction_active = False

    async def __aenter__(self):
        """Start a database transaction."""
        try:
            if AsyncIOMotorClient is None:
                raise RuntimeError("Motor not available for transactions")

            self.session = await self.database.client.start_session()
            await self.session.start_transaction()
            self.transaction_active = True

            logger.debug("Database transaction started")
            return self

        except Exception as e:
            error = DatabaseError(
                error_type=DatabaseErrorType.TRANSACTION_ROLLBACK,
                severity=DatabaseErrorSeverity.HIGH,
                message=f"Failed to start transaction: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                context={"operation": "start_transaction"},
            )

            await self.error_handler.handle_error(error)
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End database transaction with commit or rollback."""
        try:
            if self.session and self.transaction_active:
                if exc_type is None:
                    # No exception, commit transaction
                    await self.session.commit_transaction()
                    logger.debug("Database transaction committed")
                else:
                    # Exception occurred, rollback transaction
                    await self.session.abort_transaction()
                    logger.warning(
                        f"Database transaction rolled back due to: {exc_val}"
                    )

                    # Log rollback error
                    error = DatabaseError(
                        error_type=DatabaseErrorType.TRANSACTION_ROLLBACK,
                        severity=DatabaseErrorSeverity.MEDIUM,
                        message=f"Transaction rolled back: {str(exc_val)}",
                        timestamp=datetime.now(timezone.utc),
                        context={
                            "operation": "rollback",
                            "exception_type": (
                                type(exc_val).__name__ if exc_val else None
                            ),
                        },
                    )
                    await self.error_handler.handle_error(error)

                self.transaction_active = False

        except Exception as e:
            logger.error(f"Error during transaction cleanup: {str(e)}")

        finally:
            if self.session:
                await self.session.end_session()
                self.session = None


# Data validation functions


def validate_document(document: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate document against a simple schema.

    Args:
        document: Document to validate
        schema: Schema definition with field types and requirements

    Returns:
        List[str]: List of validation errors
    """
    errors = []

    # Check required fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in document:
            errors.append(f"Missing required field: {field}")

    # Check field types
    field_types = schema.get("types", {})
    for field, expected_type in field_types.items():
        if field in document:
            value = document[field]

            if expected_type == "string" and not isinstance(value, str):
                errors.append(
                    f"Field {field} must be string, got {type(value).__name__}"
                )

            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(
                    f"Field {field} must be number, got {type(value).__name__}"
                )

            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(
                    f"Field {field} must be boolean, got {type(value).__name__}"
                )

            elif expected_type == "array" and not isinstance(value, list):
                errors.append(
                    f"Field {field} must be array, got {type(value).__name__}"
                )

            elif expected_type == "object" and not isinstance(value, dict):
                errors.append(
                    f"Field {field} must be object, got {type(value).__name__}"
                )

    # Check field constraints
    constraints = schema.get("constraints", {})
    for field, constraint in constraints.items():
        if field in document:
            value = document[field]

            if "min_length" in constraint and isinstance(value, str):
                if len(value) < constraint["min_length"]:
                    errors.append(
                        f"Field {field} must be at least {constraint['min_length']} characters"
                    )

            if "max_length" in constraint and isinstance(value, str):
                if len(value) > constraint["max_length"]:
                    errors.append(
                        f"Field {field} must be at most {constraint['max_length']} characters"
                    )

            if "min_value" in constraint and isinstance(value, (int, float)):
                if value < constraint["min_value"]:
                    errors.append(
                        f"Field {field} must be at least {constraint['min_value']}"
                    )

            if "max_value" in constraint and isinstance(value, (int, float)):
                if value > constraint["max_value"]:
                    errors.append(
                        f"Field {field} must be at most {constraint['max_value']}"
                    )

            if "allowed_values" in constraint:
                if value not in constraint["allowed_values"]:
                    errors.append(
                        f"Field {field} must be one of {constraint['allowed_values']}"
                    )

    return errors


def check_constraint_violations(
    document: Dict[str, Any], collection_name: str
) -> List[str]:
    """
    Check for potential constraint violations before database insertion.

    Args:
        document: Document to check
        collection_name: Name of the collection

    Returns:
        List[str]: List of constraint violations
    """
    violations = []

    # Common constraints for trading platform
    if collection_name == "signals":
        # Signal-specific constraints
        if "entry_price" in document and "stop_loss" in document:
            if document["entry_price"] == document["stop_loss"]:
                violations.append("Entry price cannot equal stop loss")

        if "action" in document and document["action"] not in ["BUY", "SELL"]:
            violations.append("Action must be BUY or SELL")

        if "pair" in document:
            # Basic forex pair validation
            pair = document["pair"]
            if not isinstance(pair, str) or len(pair) != 7 or pair[3] != "_":
                violations.append("Invalid currency pair format")

    elif collection_name == "market_data":
        # Market data constraints
        if all(field in document for field in ["open", "high", "low", "close"]):
            o, h, l, c = (
                document["open"],
                document["high"],
                document["low"],
                document["close"],
            )

            if not (l <= o <= h and l <= c <= h):
                violations.append("Invalid OHLC relationship")

        if "volume" in document and document["volume"] < 0:
            violations.append("Volume cannot be negative")

    elif collection_name == "users":
        # User-specific constraints
        if "email" in document:
            email = document["email"]
            if "@" not in email or "." not in email:
                violations.append("Invalid email format")

        if "subscription_tier" in document:
            tier = document["subscription_tier"]
            if tier not in ["free", "premium", "enterprise"]:
                violations.append("Invalid subscription tier")

    return violations
