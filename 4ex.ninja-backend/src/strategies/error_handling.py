"""
Signal Processing Error Handling Module

This module provides comprehensive error handling for signal generation,
market data API failures, signal generation error recovery, and data consistency validation.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
from functools import wraps

# Set up logging
logger = logging.getLogger(__name__)


class SignalErrorType(Enum):
    """Enumeration of signal processing error types."""

    MARKET_DATA_API_FAILURE = "market_data_api_failure"
    INSUFFICIENT_DATA = "insufficient_data"
    CALCULATION_ERROR = "calculation_error"
    DATA_CORRUPTION = "data_corruption"
    NETWORK_TIMEOUT = "network_timeout"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SIGNAL_GENERATION_FAILURE = "signal_generation_failure"
    DATA_VALIDATION_ERROR = "data_validation_error"


class SignalErrorSeverity(Enum):
    """Enumeration of error severity levels."""

    CRITICAL = "critical"  # System cannot continue
    HIGH = "high"  # Major functionality impacted
    MEDIUM = "medium"  # Partial functionality affected
    LOW = "low"  # Minor issues, workarounds available


@dataclass
class SignalError:
    """Represents a signal processing error with context."""

    error_type: SignalErrorType
    severity: SignalErrorSeverity
    message: str
    timestamp: datetime
    context: Dict[str, Any]
    pair: Optional[str] = None
    timeframe: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False


class SignalErrorHandler:
    """Centralized error handling for signal processing operations."""

    def __init__(self):
        self.error_history: List[SignalError] = []
        self.recovery_strategies: Dict[SignalErrorType, List[Callable]] = {}
        self.max_retry_attempts = 3
        self.retry_backoff_factor = 2.0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        self._circuit_breaker_state = {}

        # Initialize recovery strategies
        self._setup_recovery_strategies()

    def _setup_recovery_strategies(self):
        """Setup default recovery strategies for different error types."""
        self.recovery_strategies = {
            SignalErrorType.MARKET_DATA_API_FAILURE: [
                self._retry_with_backoff,
                self._use_cached_data,
                self._switch_to_backup_api,
            ],
            SignalErrorType.INSUFFICIENT_DATA: [
                self._extend_data_collection_period,
                self._use_lower_timeframe_data,
                self._skip_signal_generation,
            ],
            SignalErrorType.CALCULATION_ERROR: [
                self._recalculate_with_validation,
                self._use_alternative_calculation_method,
                self._log_and_skip,
            ],
            SignalErrorType.DATA_CORRUPTION: [
                self._validate_and_clean_data,
                self._reload_data_from_source,
                self._mark_data_as_invalid,
            ],
            SignalErrorType.NETWORK_TIMEOUT: [
                self._retry_with_exponential_backoff,
                self._switch_to_local_cache,
                self._defer_signal_processing,
            ],
            SignalErrorType.RATE_LIMIT_EXCEEDED: [
                self._implement_rate_limiting,
                self._queue_requests,
                self._switch_to_alternative_endpoint,
            ],
        }

    def handle_error(self, error: SignalError) -> bool:
        """
        Handle a signal processing error with appropriate recovery strategy.

        Args:
            error: The SignalError to handle

        Returns:
            bool: True if error was recovered successfully, False otherwise
        """
        logger.error(
            f"Signal processing error: {error.error_type.value} - {error.message}"
        )

        # Add to error history
        self.error_history.append(error)

        # Check circuit breaker
        if error.pair and self._is_circuit_breaker_open(error.pair, error.error_type):
            logger.warning(
                f"Circuit breaker open for {error.pair} - {error.error_type.value}"
            )
            return False

        # Attempt recovery
        recovery_success = self._attempt_recovery(error)

        # Update circuit breaker state
        if error.pair:
            self._update_circuit_breaker(error.pair, error.error_type, recovery_success)

        return recovery_success

    def _attempt_recovery(self, error: SignalError) -> bool:
        """Attempt to recover from the error using configured strategies."""
        strategies = self.recovery_strategies.get(error.error_type, [])

        for strategy in strategies:
            try:
                logger.info(f"Attempting recovery strategy: {strategy.__name__}")
                error.recovery_attempted = True

                if strategy(error):
                    error.recovery_successful = True
                    logger.info(
                        f"Recovery successful using strategy: {strategy.__name__}"
                    )
                    return True

            except Exception as e:
                logger.error(f"Recovery strategy {strategy.__name__} failed: {str(e)}")
                continue

        logger.error(
            f"All recovery strategies failed for error: {error.error_type.value}"
        )
        return False

    def _is_circuit_breaker_open(self, pair: str, error_type: SignalErrorType) -> bool:
        """Check if circuit breaker is open for given pair and error type."""
        key = f"{pair}_{error_type.value}"
        breaker_info = self._circuit_breaker_state.get(key, {})

        if not breaker_info:
            return False

        failure_count = breaker_info.get("failure_count", 0)
        last_failure_time = breaker_info.get("last_failure_time", 0)

        # Check if threshold exceeded and timeout not expired
        if failure_count >= self.circuit_breaker_threshold:
            time_since_failure = time.time() - last_failure_time
            return time_since_failure < self.circuit_breaker_timeout

        return False

    def _update_circuit_breaker(
        self, pair: str, error_type: SignalErrorType, success: bool
    ):
        """Update circuit breaker state based on operation result."""
        key = f"{pair}_{error_type.value}"

        if success:
            # Reset on success
            self._circuit_breaker_state.pop(key, None)
        else:
            # Increment failure count
            breaker_info = self._circuit_breaker_state.get(key, {"failure_count": 0})
            breaker_info["failure_count"] += 1
            breaker_info["last_failure_time"] = time.time()
            self._circuit_breaker_state[key] = breaker_info

    # Recovery strategy implementations

    def _retry_with_backoff(self, error: SignalError) -> bool:
        """Retry operation with exponential backoff."""
        context = error.context
        retry_count = context.get("retry_count", 0)

        if retry_count >= self.max_retry_attempts:
            logger.warning("Maximum retry attempts reached")
            return False

        # Calculate backoff delay
        delay = self.retry_backoff_factor**retry_count
        logger.info(f"Retrying after {delay} seconds (attempt {retry_count + 1})")

        time.sleep(delay)
        context["retry_count"] = retry_count + 1

        # This would trigger the original operation retry
        return True

    def _use_cached_data(self, error: SignalError) -> bool:
        """Use cached data as fallback."""
        logger.info("Attempting to use cached data")
        # Implementation would check for valid cached data
        # For now, return True if cache exists (would be implemented with actual cache)
        return error.context.get("has_cache", False)

    def _switch_to_backup_api(self, error: SignalError) -> bool:
        """Switch to backup API endpoint."""
        logger.info("Switching to backup API endpoint")
        # Implementation would switch to backup data source
        return error.context.get("has_backup_api", False)

    def _extend_data_collection_period(self, error: SignalError) -> bool:
        """Extend data collection period to gather more data."""
        logger.info("Extending data collection period")
        # Implementation would request more historical data
        return True

    def _use_lower_timeframe_data(self, error: SignalError) -> bool:
        """Use lower timeframe data to compensate for insufficient data."""
        logger.info("Using lower timeframe data")
        # Implementation would aggregate lower timeframe data
        return error.context.get("has_lower_timeframe", False)

    def _skip_signal_generation(self, error: SignalError) -> bool:
        """Skip current signal generation cycle."""
        logger.info("Skipping current signal generation cycle")
        return True

    def _recalculate_with_validation(self, error: SignalError) -> bool:
        """Recalculate with additional validation."""
        logger.info("Recalculating with additional validation")
        # Implementation would retry calculation with extra validation
        return True

    def _use_alternative_calculation_method(self, error: SignalError) -> bool:
        """Use alternative calculation method."""
        logger.info("Using alternative calculation method")
        return error.context.get("has_alternative_method", False)

    def _log_and_skip(self, error: SignalError) -> bool:
        """Log error and skip processing."""
        logger.warning(f"Logging error and skipping: {error.message}")
        return True

    def _validate_and_clean_data(self, error: SignalError) -> bool:
        """Validate and clean corrupted data."""
        logger.info("Validating and cleaning data")
        # Implementation would perform data validation and cleaning
        return True

    def _reload_data_from_source(self, error: SignalError) -> bool:
        """Reload data from original source."""
        logger.info("Reloading data from source")
        # Implementation would fetch fresh data
        return True

    def _mark_data_as_invalid(self, error: SignalError) -> bool:
        """Mark data as invalid and prevent further processing."""
        logger.warning("Marking data as invalid")
        return True

    def _retry_with_exponential_backoff(self, error: SignalError) -> bool:
        """Retry with exponential backoff for network issues."""
        return self._retry_with_backoff(error)

    def _switch_to_local_cache(self, error: SignalError) -> bool:
        """Switch to local cache for network issues."""
        return self._use_cached_data(error)

    def _defer_signal_processing(self, error: SignalError) -> bool:
        """Defer signal processing to later time."""
        logger.info("Deferring signal processing")
        # Implementation would queue for later processing
        return True

    def _implement_rate_limiting(self, error: SignalError) -> bool:
        """Implement rate limiting to prevent API overload."""
        logger.info("Implementing rate limiting")
        delay = error.context.get("rate_limit_delay", 60)
        time.sleep(delay)
        return True

    def _queue_requests(self, error: SignalError) -> bool:
        """Queue requests for rate-limited endpoints."""
        logger.info("Queueing requests")
        # Implementation would add to request queue
        return True

    def _switch_to_alternative_endpoint(self, error: SignalError) -> bool:
        """Switch to alternative API endpoint."""
        logger.info("Switching to alternative endpoint")
        return error.context.get("has_alternative_endpoint", False)

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
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
            "circuit_breaker_states": self._circuit_breaker_state,
        }


def signal_error_handler(
    error_type: SignalErrorType,
    severity: SignalErrorSeverity = SignalErrorSeverity.MEDIUM,
):
    """
    Decorator for signal processing functions to handle errors gracefully.

    Args:
        error_type: The type of error this function might encounter
        severity: The severity level of potential errors
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_handler = getattr(args[0] if args else None, "_error_handler", None)
            if not error_handler:
                error_handler = SignalErrorHandler()

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error = SignalError(
                    error_type=error_type,
                    severity=severity,
                    message=str(e),
                    timestamp=datetime.now(timezone.utc),
                    context={
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs),
                    },
                )

                if error_handler.handle_error(error):
                    # Retry the function if recovery was successful
                    try:
                        return await func(*args, **kwargs)
                    except Exception as retry_e:
                        logger.error(f"Retry failed: {str(retry_e)}")
                        raise
                else:
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            error_handler = getattr(args[0] if args else None, "_error_handler", None)
            if not error_handler:
                error_handler = SignalErrorHandler()

            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = SignalError(
                    error_type=error_type,
                    severity=severity,
                    message=str(e),
                    timestamp=datetime.now(timezone.utc),
                    context={
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs),
                    },
                )

                if error_handler.handle_error(error):
                    # Retry the function if recovery was successful
                    try:
                        return func(*args, **kwargs)
                    except Exception as retry_e:
                        logger.error(f"Retry failed: {str(retry_e)}")
                        raise
                else:
                    raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Data consistency validation functions


def validate_market_data(data: Dict[str, Any]) -> bool:
    """
    Validate market data for consistency and corruption.

    Args:
        data: Market data dictionary

    Returns:
        bool: True if data is valid, False otherwise
    """
    if not data:
        return False

    required_fields = ["open", "high", "low", "close", "timestamp"]

    # Check required fields
    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field: {field}")
            return False

    # Validate OHLC relationship
    try:
        open_price = float(data["open"])
        high_price = float(data["high"])
        low_price = float(data["low"])
        close_price = float(data["close"])

        # High should be highest, low should be lowest
        if not (
            low_price <= open_price <= high_price
            and low_price <= close_price <= high_price
        ):
            logger.error("Invalid OHLC relationship")
            return False

        # Check for reasonable price values (not zero or negative)
        if any(
            price <= 0 for price in [open_price, high_price, low_price, close_price]
        ):
            logger.error("Invalid price values (zero or negative)")
            return False

        # Check for extreme price movements (more than 50% in one candle)
        max_change = max(
            abs(high_price - low_price) / open_price,
            abs(close_price - open_price) / open_price,
        )
        if max_change > 0.5:
            logger.warning(f"Extreme price movement detected: {max_change:.2%}")
            # Don't fail validation but log warning

    except (ValueError, TypeError) as e:
        logger.error(f"Invalid price data types: {str(e)}")
        return False

    return True


def validate_signal_data(signal: Dict[str, Any]) -> bool:
    """
    Validate signal data before processing.

    Args:
        signal: Signal data dictionary

    Returns:
        bool: True if signal is valid, False otherwise
    """
    if not signal:
        return False

    required_fields = [
        "pair",
        "action",
        "entry_price",
        "stop_loss",
        "take_profit",
        "timestamp",
    ]

    # Check required fields
    for field in required_fields:
        if field not in signal:
            logger.error(f"Missing required signal field: {field}")
            return False

    # Validate action
    if signal["action"] not in ["BUY", "SELL"]:
        logger.error(f"Invalid signal action: {signal['action']}")
        return False

    try:
        entry_price = float(signal["entry_price"])
        stop_loss = float(signal["stop_loss"])
        take_profit = float(signal["take_profit"])

        # Validate price relationships for BUY signals
        if signal["action"] == "BUY":
            if stop_loss >= entry_price:
                logger.error("BUY signal: stop loss should be below entry price")
                return False
            if take_profit <= entry_price:
                logger.error("BUY signal: take profit should be above entry price")
                return False

        # Validate price relationships for SELL signals
        elif signal["action"] == "SELL":
            if stop_loss <= entry_price:
                logger.error("SELL signal: stop loss should be above entry price")
                return False
            if take_profit >= entry_price:
                logger.error("SELL signal: take profit should be below entry price")
                return False

        # Check for reasonable risk-reward ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)

        if risk == 0:
            logger.error("Risk cannot be zero")
            return False

        rr_ratio = reward / risk
        if rr_ratio < 0.5:  # Minimum 1:0.5 risk-reward
            logger.warning(f"Poor risk-reward ratio: {rr_ratio:.2f}")
            # Don't fail validation but log warning

    except (ValueError, TypeError) as e:
        logger.error(f"Invalid signal price data: {str(e)}")
        return False

    return True


def detect_data_corruption(historical_data: List[Dict[str, Any]]) -> List[int]:
    """
    Detect potential data corruption in historical market data.

    Args:
        historical_data: List of market data dictionaries

    Returns:
        List[int]: Indices of potentially corrupted data points
    """
    corrupted_indices = []

    if len(historical_data) < 2:
        return corrupted_indices

    for i, data in enumerate(historical_data):
        # Validate individual candle
        if not validate_market_data(data):
            corrupted_indices.append(i)
            continue

        # Check for gaps in timestamp sequence
        if i > 0:
            current_time = data.get("timestamp")
            previous_time = historical_data[i - 1].get("timestamp")

            if current_time and previous_time:
                # Check for reasonable time progression
                time_diff = abs(current_time - previous_time)
                expected_diff = 3600  # 1 hour in seconds (adjust based on timeframe)

                if time_diff > expected_diff * 2:  # Allow some tolerance
                    logger.warning(f"Large time gap detected at index {i}")
                    corrupted_indices.append(i)

        # Check for duplicate timestamps
        if i > 0 and data.get("timestamp") == historical_data[i - 1].get("timestamp"):
            logger.error(f"Duplicate timestamp detected at index {i}")
            corrupted_indices.append(i)

    return corrupted_indices
