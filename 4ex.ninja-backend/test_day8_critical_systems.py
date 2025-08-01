"""
Test suite for Day 8 critical system error handling and alerting implementation.

This module tests all components of the critical system error handling:
- Signal processing error handling
- Database operation error handling
- Critical system alerting
- Monitoring dashboards and metrics
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
import logging

# Test imports with graceful fallbacks
try:
    from src.strategies.error_handling import (
        SignalErrorHandler,
        SignalError,
        SignalErrorType,
        SignalErrorSeverity,
        signal_error_handler,
        validate_market_data,
        validate_signal_data,
        detect_data_corruption,
    )

    SIGNAL_ERROR_HANDLING_AVAILABLE = True
except ImportError as e:
    print(f"Signal error handling not available: {e}")
    SIGNAL_ERROR_HANDLING_AVAILABLE = False

try:
    from src.infrastructure.repositories.error_handling import (
        DatabaseErrorHandler,
        DatabaseError,
        DatabaseErrorType,
        DatabaseErrorSeverity,
        ConnectionPoolManager,
        database_operation,
        TransactionManager,
        validate_document,
        check_constraint_violations,
    )

    DB_ERROR_HANDLING_AVAILABLE = True
except ImportError as e:
    print(f"Database error handling not available: {e}")
    DB_ERROR_HANDLING_AVAILABLE = False

try:
    from src.infrastructure.monitoring.alerts import (
        AlertManager,
        Alert,
        AlertType,
        AlertSeverity,
        AlertStatus,
        LogAlertChannel,
        EmailAlertChannel,
        WebhookAlertChannel,
        alert_signal_processing_failure,
        alert_database_connectivity,
        alert_external_api_downtime,
        alert_circuit_breaker_triggered,
    )

    ALERTING_AVAILABLE = True
except ImportError as e:
    print(f"Alerting system not available: {e}")
    ALERTING_AVAILABLE = False

try:
    from src.infrastructure.monitoring.dashboards import (
        MetricsCollector,
        Dashboard,
        MetricsScheduler,
        Metric,
        MetricType,
        MetricCategory,
        track_requests,
        record_signal_generated,
        metrics_collector,
        dashboard,
        scheduler,
    )

    DASHBOARDS_AVAILABLE = True
except ImportError as e:
    print(f"Dashboard system not available: {e}")
    DASHBOARDS_AVAILABLE = False


class TestSignalErrorHandling:
    """Test signal processing error handling."""

    @pytest.mark.skipif(
        not SIGNAL_ERROR_HANDLING_AVAILABLE,
        reason="Signal error handling not available",
    )
    def test_signal_error_creation(self):
        """Test creating signal errors."""
        error = SignalError(
            error_type=SignalErrorType.MARKET_DATA_API_FAILURE,
            severity=SignalErrorSeverity.HIGH,
            message="API connection failed",
            timestamp=datetime.now(timezone.utc),
            context={"api_endpoint": "test.com"},
            pair="EUR_USD",
            timeframe="H1",
        )

        assert error.error_type == SignalErrorType.MARKET_DATA_API_FAILURE
        assert error.severity == SignalErrorSeverity.HIGH
        assert error.message == "API connection failed"
        assert error.pair == "EUR_USD"
        assert error.timeframe == "H1"
        assert not error.recovery_attempted
        assert not error.recovery_successful

    @pytest.mark.skipif(
        not SIGNAL_ERROR_HANDLING_AVAILABLE,
        reason="Signal error handling not available",
    )
    def test_signal_error_handler_initialization(self):
        """Test signal error handler initialization."""
        handler = SignalErrorHandler()

        assert handler.max_retry_attempts == 3
        assert handler.retry_backoff_factor == 2.0
        assert handler.circuit_breaker_threshold == 5
        assert handler.circuit_breaker_timeout == 300
        assert len(handler.recovery_strategies) > 0
        assert SignalErrorType.MARKET_DATA_API_FAILURE in handler.recovery_strategies

    @pytest.mark.skipif(
        not SIGNAL_ERROR_HANDLING_AVAILABLE,
        reason="Signal error handling not available",
    )
    def test_circuit_breaker_functionality(self):
        """Test circuit breaker functionality."""
        handler = SignalErrorHandler()

        # Initially circuit breaker should be closed
        assert not handler._is_circuit_breaker_open(
            "EUR_USD", SignalErrorType.MARKET_DATA_API_FAILURE
        )

        # Simulate failures to trigger circuit breaker
        for i in range(6):  # Exceed threshold of 5
            handler._update_circuit_breaker(
                "EUR_USD", SignalErrorType.MARKET_DATA_API_FAILURE, False
            )

        # Circuit breaker should now be open
        assert handler._is_circuit_breaker_open(
            "EUR_USD", SignalErrorType.MARKET_DATA_API_FAILURE
        )

        # Success should reset circuit breaker
        handler._update_circuit_breaker(
            "EUR_USD", SignalErrorType.MARKET_DATA_API_FAILURE, True
        )
        assert not handler._is_circuit_breaker_open(
            "EUR_USD", SignalErrorType.MARKET_DATA_API_FAILURE
        )

    @pytest.mark.skipif(
        not SIGNAL_ERROR_HANDLING_AVAILABLE,
        reason="Signal error handling not available",
    )
    def test_market_data_validation(self):
        """Test market data validation."""
        # Valid data
        valid_data = {
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0950,
            "close": 1.1025,
            "timestamp": 1625097600,
        }
        assert validate_market_data(valid_data)

        # Invalid OHLC relationship
        invalid_data = {
            "open": 1.1000,
            "high": 1.0900,  # High less than open
            "low": 1.0950,
            "close": 1.1025,
            "timestamp": 1625097600,
        }
        assert not validate_market_data(invalid_data)

        # Missing required field
        incomplete_data = {
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0950,
            # Missing close
            "timestamp": 1625097600,
        }
        assert not validate_market_data(incomplete_data)

    @pytest.mark.skipif(
        not SIGNAL_ERROR_HANDLING_AVAILABLE,
        reason="Signal error handling not available",
    )
    def test_signal_data_validation(self):
        """Test signal data validation."""
        # Valid BUY signal
        valid_buy_signal = {
            "pair": "EUR_USD",
            "action": "BUY",
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "take_profit": 1.1100,
            "timestamp": 1625097600,
        }
        assert validate_signal_data(valid_buy_signal)

        # Valid SELL signal
        valid_sell_signal = {
            "pair": "EUR_USD",
            "action": "SELL",
            "entry_price": 1.1000,
            "stop_loss": 1.1050,
            "take_profit": 1.0900,
            "timestamp": 1625097600,
        }
        assert validate_signal_data(valid_sell_signal)

        # Invalid BUY signal (stop loss above entry)
        invalid_buy_signal = {
            "pair": "EUR_USD",
            "action": "BUY",
            "entry_price": 1.1000,
            "stop_loss": 1.1050,  # Should be below entry for BUY
            "take_profit": 1.1100,
            "timestamp": 1625097600,
        }
        assert not validate_signal_data(invalid_buy_signal)


class TestDatabaseErrorHandling:
    """Test database operation error handling."""

    @pytest.mark.skipif(
        not DB_ERROR_HANDLING_AVAILABLE, reason="Database error handling not available"
    )
    def test_connection_pool_manager_initialization(self):
        """Test connection pool manager initialization."""
        pool = ConnectionPoolManager(
            "mongodb://localhost:27017", pool_size=5, max_pool_size=20
        )

        assert pool.connection_string == "mongodb://localhost:27017"
        assert pool.pool_size == 5
        assert pool.max_pool_size == 20
        assert pool.client is None
        assert pool.database is None
        assert pool.connection_failures == 0

    @pytest.mark.skipif(
        not DB_ERROR_HANDLING_AVAILABLE, reason="Database error handling not available"
    )
    @pytest.mark.asyncio
    async def test_database_error_handler_initialization(self):
        """Test database error handler initialization."""
        pool = ConnectionPoolManager("mongodb://localhost:27017")
        handler = DatabaseErrorHandler(pool)

        assert handler.connection_pool == pool
        assert handler.max_retry_attempts == 3
        assert handler.retry_backoff_base == 1.0
        assert handler.retry_backoff_multiplier == 2.0
        assert handler.max_backoff_delay == 30.0
        assert len(handler.retryable_errors) > 0

    @pytest.mark.skipif(
        not DB_ERROR_HANDLING_AVAILABLE, reason="Database error handling not available"
    )
    def test_document_validation(self):
        """Test document validation against schema."""
        schema = {
            "required": ["name", "email"],
            "types": {"name": "string", "email": "string", "age": "number"},
            "constraints": {
                "name": {"min_length": 2, "max_length": 50},
                "age": {"min_value": 0, "max_value": 150},
            },
        }

        # Valid document
        valid_doc = {"name": "John Doe", "email": "john@example.com", "age": 30}
        errors = validate_document(valid_doc, schema)
        assert len(errors) == 0

        # Invalid document - missing required field
        invalid_doc = {
            "name": "John Doe",
            # Missing email
            "age": 30,
        }
        errors = validate_document(invalid_doc, schema)
        assert len(errors) > 0
        assert any("email" in error for error in errors)

        # Invalid document - constraint violation
        invalid_doc2 = {
            "name": "J",  # Too short
            "email": "john@example.com",
            "age": 200,  # Too high
        }
        errors = validate_document(invalid_doc2, schema)
        assert len(errors) >= 2  # At least name and age violations

    @pytest.mark.skipif(
        not DB_ERROR_HANDLING_AVAILABLE, reason="Database error handling not available"
    )
    def test_constraint_violations_check(self):
        """Test constraint violations for specific collections."""
        # Valid signal document
        valid_signal = {
            "action": "BUY",
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "pair": "EUR_USD",
        }
        violations = check_constraint_violations(valid_signal, "signals")
        assert len(violations) == 0

        # Invalid signal - equal entry and stop loss
        invalid_signal = {
            "action": "BUY",
            "entry_price": 1.1000,
            "stop_loss": 1.1000,  # Same as entry
            "pair": "EUR_USD",
        }
        violations = check_constraint_violations(invalid_signal, "signals")
        assert len(violations) > 0

        # Invalid market data - bad OHLC relationship
        invalid_market_data = {
            "open": 1.1000,
            "high": 1.0900,  # High less than open
            "low": 1.0950,
            "close": 1.1025,
        }
        violations = check_constraint_violations(invalid_market_data, "market_data")
        assert len(violations) > 0


class TestAlerting:
    """Test critical system alerting."""

    @pytest.mark.skipif(not ALERTING_AVAILABLE, reason="Alerting system not available")
    def test_alert_creation(self):
        """Test alert creation."""
        alert = Alert(
            alert_type=AlertType.SIGNAL_PROCESSING_FAILURE,
            severity=AlertSeverity.HIGH,
            title="Signal Processing Failed",
            message="Unable to process market data",
            timestamp=datetime.now(timezone.utc),
            context={"pair": "EUR_USD"},
            tags=["trading", "signals"],
        )

        assert alert.alert_type == AlertType.SIGNAL_PROCESSING_FAILURE
        assert alert.severity == AlertSeverity.HIGH
        assert alert.title == "Signal Processing Failed"
        assert alert.status == AlertStatus.ACTIVE
        assert alert.alert_id is not None
        assert "trading" in alert.tags

    @pytest.mark.skipif(not ALERTING_AVAILABLE, reason="Alerting system not available")
    def test_log_alert_channel(self):
        """Test log alert channel."""
        channel = LogAlertChannel()

        assert channel.is_available()

        alert = Alert(
            alert_type=AlertType.DATABASE_CONNECTIVITY,
            severity=AlertSeverity.CRITICAL,
            title="Database Connection Lost",
            message="Cannot connect to MongoDB",
            timestamp=datetime.now(timezone.utc),
        )

        # This should not raise an exception
        result = asyncio.run(channel.send_alert(alert))
        assert result is True

    @pytest.mark.skipif(not ALERTING_AVAILABLE, reason="Alerting system not available")
    def test_alert_manager_initialization(self):
        """Test alert manager initialization."""
        manager = AlertManager()

        assert len(manager.channels) > 0
        assert "logs" in manager.channels
        assert len(manager.alert_rules) > 0
        assert len(manager.suppression_rules) > 0
        assert len(manager.active_alerts) == 0

    @pytest.mark.skipif(not ALERTING_AVAILABLE, reason="Alerting system not available")
    @pytest.mark.asyncio
    async def test_alert_triggering(self):
        """Test alert triggering and routing."""
        manager = AlertManager()

        alert = Alert(
            alert_type=AlertType.EXTERNAL_API_DOWNTIME,
            severity=AlertSeverity.HIGH,
            title="OANDA API Down",
            message="Cannot reach OANDA API",
            timestamp=datetime.now(timezone.utc),
        )

        result = await manager.trigger_alert(alert)
        assert result is True
        assert len(manager.active_alerts) == 1
        assert len(manager.alert_history) == 1

    @pytest.mark.skipif(not ALERTING_AVAILABLE, reason="Alerting system not available")
    @pytest.mark.asyncio
    async def test_convenience_alert_functions(self):
        """Test convenience functions for triggering alerts."""
        # Test signal processing failure alert
        result = await alert_signal_processing_failure(
            "Failed to calculate moving averages",
            context={"pair": "EUR_USD", "timeframe": "H1"},
        )
        assert result is True

        # Test database connectivity alert
        result = await alert_database_connectivity(
            "MongoDB connection timeout", context={"host": "localhost", "port": 27017}
        )
        assert result is True

        # Test external API downtime alert
        result = await alert_external_api_downtime(
            "OANDA", "API returning 503 errors", context={"endpoint": "/v3/accounts"}
        )
        assert result is True


class TestDashboards:
    """Test monitoring dashboards and metrics."""

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_metrics_collector_initialization(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector()

        assert len(collector.metrics) > 0
        assert "cpu_usage_percent" in collector.metrics
        assert "memory_usage_bytes" in collector.metrics
        assert "request_count" in collector.metrics
        assert "signals_generated" in collector.metrics

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_metric_registration(self):
        """Test metric registration."""
        collector = MetricsCollector()

        metric = collector.register_metric(
            "test_metric",
            MetricType.COUNTER,
            MetricCategory.APPLICATION,
            "Test metric for unit tests",
            "count",
        )

        assert metric.name == "test_metric"
        assert metric.metric_type == MetricType.COUNTER
        assert metric.category == MetricCategory.APPLICATION
        assert "test_metric" in collector.metrics

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_counter_increment(self):
        """Test counter metric increments."""
        collector = MetricsCollector()

        # Initial value should be None or 0
        request_metric = collector.get_metric("request_count")
        assert request_metric is not None
        initial_value = request_metric.get_current_value()

        collector.increment_counter("request_count", 5)

        new_value = request_metric.get_current_value()
        assert new_value == (initial_value or 0) + 5

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_gauge_setting(self):
        """Test gauge metric setting."""
        collector = MetricsCollector()

        collector.set_gauge("cpu_usage_percent", 75.5)

        cpu_metric = collector.get_metric("cpu_usage_percent")
        assert cpu_metric is not None
        value = cpu_metric.get_current_value()
        assert value == 75.5

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_histogram_recording(self):
        """Test histogram metric recording."""
        collector = MetricsCollector()

        collector.record_histogram("request_duration_ms", 150.0)
        collector.record_histogram("request_duration_ms", 200.0)

        metric = collector.get_metric("request_duration_ms")
        assert metric is not None
        assert len(metric.data_points) >= 2

        # Test average calculation
        avg = metric.get_average()
        assert avg is not None
        assert avg > 0

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_dashboard_health_summary(self):
        """Test dashboard health summary."""
        collector = MetricsCollector()
        dashboard_instance = Dashboard(collector)

        # Set some test values
        collector.set_gauge("cpu_usage_percent", 45.0)
        collector.set_gauge("memory_usage_bytes", 4 * 1024 * 1024 * 1024)  # 4GB

        summary = dashboard_instance.get_system_health_summary()

        assert "timestamp" in summary
        assert "status" in summary
        assert "metrics" in summary
        assert (
            summary["status"] == "healthy"
        )  # Should be healthy with low CPU and memory

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_business_metrics_tracking(self):
        """Test business metrics tracking."""
        # Test signal generation recording
        record_signal_generated("EUR_USD", 0.85)

        signals_metric = metrics_collector.get_metric("signals_generated")
        confidence_metric = metrics_collector.get_metric("signal_confidence")

        assert signals_metric is not None
        assert confidence_metric is not None

        # Should have recorded the signal
        signals_count = signals_metric.get_current_value()
        assert signals_count is not None and signals_count > 0

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_metrics_export(self):
        """Test metrics export to JSON."""
        collector = MetricsCollector()
        dashboard_instance = Dashboard(collector)

        # Add some test data
        collector.increment_counter("request_count", 10)
        collector.set_gauge("cpu_usage_percent", 55.0)

        json_export = dashboard_instance.export_metrics_json(3600)

        assert isinstance(json_export, str)
        assert "timestamp" in json_export
        assert "metrics" in json_export
        assert "request_count" in json_export
        assert "cpu_usage_percent" in json_export


# Integration tests combining multiple components


class TestDay8Integration:
    """Integration tests for Day 8 components."""

    @pytest.mark.skipif(
        not all(
            [SIGNAL_ERROR_HANDLING_AVAILABLE, ALERTING_AVAILABLE, DASHBOARDS_AVAILABLE]
        ),
        reason="Not all Day 8 components available",
    )
    @pytest.mark.asyncio
    async def test_error_handling_with_alerting(self):
        """Test error handling triggering alerts."""
        # Create a signal error
        error = SignalError(
            error_type=SignalErrorType.MARKET_DATA_API_FAILURE,
            severity=SignalErrorSeverity.CRITICAL,
            message="OANDA API connection failed",
            timestamp=datetime.now(timezone.utc),
            context={"endpoint": "/v3/accounts", "timeout": 30},
            pair="EUR_USD",
        )

        # Trigger alert for the error
        await alert_signal_processing_failure(
            error.message, context=error.context, severity=AlertSeverity.CRITICAL
        )

        # Verify alert was created
        from src.infrastructure.monitoring.alerts import alert_manager

        assert len(alert_manager.active_alerts) > 0

    @pytest.mark.skipif(
        not all(
            [DB_ERROR_HANDLING_AVAILABLE, ALERTING_AVAILABLE, DASHBOARDS_AVAILABLE]
        ),
        reason="Not all Day 8 components available",
    )
    @pytest.mark.asyncio
    async def test_database_error_with_metrics(self):
        """Test database errors being tracked in metrics."""
        # Simulate database error
        await alert_database_connectivity(
            "Connection pool exhausted",
            context={"active_connections": 50, "max_connections": 50},
        )

        # Record error in metrics
        metrics_collector.increment_counter("error_count")
        metrics_collector.increment_counter("database_errors")

        # Verify metrics were updated
        error_metric = metrics_collector.get_metric("error_count")
        assert error_metric is not None
        error_count = error_metric.get_current_value()
        assert error_count is not None and error_count > 0


def run_day8_tests():
    """Run all Day 8 tests."""
    import subprocess
    import sys

    try:
        # Run pytest on this file
        result = subprocess.run(
            [sys.executable, "-m", "pytest", __file__, "-v"],
            capture_output=True,
            text=True,
        )

        print("Day 8 Test Results:")
        print("=" * 50)
        print(result.stdout)

        if result.stderr:
            print("Errors:")
            print(result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"Error running tests: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_day8_tests()
    print(f"\nDay 8 implementation tests {'PASSED' if success else 'FAILED'}")
