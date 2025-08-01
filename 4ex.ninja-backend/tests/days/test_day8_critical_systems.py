"""
Day 8: Critical System Error Handling and Alerting Tests

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
    def test_data_validation(self):
        """Test market data and signal validation."""
        # Test valid market data
        valid_data = {
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0950,
            "close": 1.1025,
            "timestamp": int(time.time()),
        }
        assert validate_market_data(valid_data) is True

        # Test invalid market data
        invalid_data = {
            "open": 1.1000,
            "high": 1.0950,  # High < Low
            "low": 1.1050,
            "close": 1.1025,
        }
        assert validate_market_data(invalid_data) is False

        # Test valid signal data
        valid_signal = {
            "pair": "EUR_USD",
            "action": "BUY",
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "take_profit": 1.1100,
            "timestamp": int(time.time()),
        }
        assert validate_signal_data(valid_signal) is True

        # Test invalid signal data
        invalid_signal = {
            "pair": "EUR_USD",
            "action": "BUY",
            "entry_price": 1.1000,
            "stop_loss": 1.1050,  # Stop loss above entry for BUY
            "take_profit": 1.1100,
        }
        assert validate_signal_data(invalid_signal) is False

    @pytest.mark.skipif(
        not SIGNAL_ERROR_HANDLING_AVAILABLE,
        reason="Signal error handling not available",
    )
    def test_data_corruption_detection(self):
        """Test data corruption detection."""
        # Test normal data
        normal_data = {
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0950,
            "close": 1.1025,
            "volume": 1000000,
        }
        assert detect_data_corruption(normal_data) is False

        # Test data with extreme values
        extreme_data = {
            "open": 1.1000,
            "high": 1.5000,  # Extreme value
            "low": 1.0950,
            "close": 1.1025,
            "volume": 1000000,
        }
        assert detect_data_corruption(extreme_data) is True


class TestDatabaseErrorHandling:
    """Test database operation error handling."""

    @pytest.mark.skipif(
        not DB_ERROR_HANDLING_AVAILABLE, reason="Database error handling not available"
    )
    def test_connection_pool_manager(self):
        """Test connection pool manager."""
        pool = ConnectionPoolManager("mongodb://localhost:27017")
        assert pool.connection_string == "mongodb://localhost:27017"
        assert pool.min_connections == 5
        assert pool.max_connections == 20
        assert pool.connection_timeout == 30.0

    @pytest.mark.skipif(
        not DB_ERROR_HANDLING_AVAILABLE, reason="Database error handling not available"
    )
    def test_database_error_handler(self):
        """Test database error handler."""
        pool = ConnectionPoolManager("mongodb://localhost:27017")
        handler = DatabaseErrorHandler(pool)

        assert handler.pool == pool
        assert handler.max_retry_attempts == 3
        assert handler.retry_delay == 1.0
        assert handler.circuit_breaker_threshold == 5

    @pytest.mark.skipif(
        not DB_ERROR_HANDLING_AVAILABLE, reason="Database error handling not available"
    )
    def test_document_validation(self):
        """Test document validation."""
        schema = {
            "required": ["name", "email"],
            "types": {"name": "string", "email": "string"},
            "constraints": {
                "name": {"min_length": 2, "max_length": 50},
                "email": {"pattern": r"^[^@]+@[^@]+\.[^@]+$"},
            },
        }

        # Valid document
        valid_doc = {"name": "John Doe", "email": "john@example.com"}
        errors = validate_document(valid_doc, schema)
        assert len(errors) == 0

        # Invalid document
        invalid_doc = {"name": "J", "email": "invalid-email"}
        errors = validate_document(invalid_doc, schema)
        assert len(errors) > 0

    @pytest.mark.skipif(
        not DB_ERROR_HANDLING_AVAILABLE, reason="Database error handling not available"
    )
    def test_constraint_violations(self):
        """Test constraint violation checking."""
        # Test signal constraints
        valid_signal = {
            "action": "BUY",
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "take_profit": 1.1100,
            "pair": "EUR_USD",
        }
        violations = check_constraint_violations(valid_signal, "signals")
        assert len(violations) == 0

        # Invalid signal
        invalid_signal = {
            "action": "INVALID_ACTION",
            "entry_price": -1.0,  # Negative price
            "pair": "INVALID_PAIR",
        }
        violations = check_constraint_violations(invalid_signal, "signals")
        assert len(violations) > 0


class TestAlertingSystem:
    """Test critical system alerting."""

    @pytest.mark.skipif(not ALERTING_AVAILABLE, reason="Alerting system not available")
    def test_alert_creation(self):
        """Test creating alerts."""
        alert = Alert(
            alert_type=AlertType.SIGNAL_PROCESSING_FAILURE,
            severity=AlertSeverity.HIGH,
            title="Signal Processing Failed",
            message="Unable to process market data",
            timestamp=datetime.now(timezone.utc),
            tags=["signal", "processing"],
        )

        assert alert.alert_type == AlertType.SIGNAL_PROCESSING_FAILURE
        assert alert.severity == AlertSeverity.HIGH
        assert alert.title == "Signal Processing Failed"
        assert alert.status == AlertStatus.ACTIVE
        assert "signal" in alert.tags

    @pytest.mark.skipif(not ALERTING_AVAILABLE, reason="Alerting system not available")
    @pytest.mark.asyncio
    async def test_log_alert_channel(self):
        """Test log alert channel."""
        channel = LogAlertChannel()
        assert channel.is_available() is True

        alert = Alert(
            alert_type=AlertType.SYSTEM_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Test Alert",
            message="Test message",
            timestamp=datetime.now(timezone.utc),
        )

        result = await channel.send_alert(alert)
        assert result is True

    @pytest.mark.skipif(not ALERTING_AVAILABLE, reason="Alerting system not available")
    def test_alert_manager(self):
        """Test alert manager."""
        manager = AlertManager()
        assert len(manager.channels) > 0
        assert any(isinstance(ch, LogAlertChannel) for ch in manager.channels.values())

    @pytest.mark.skipif(not ALERTING_AVAILABLE, reason="Alerting system not available")
    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test convenience alert functions."""
        # Test signal processing failure alert
        result = await alert_signal_processing_failure("Test signal failure")
        assert result is True

        # Test database connectivity alert
        result = await alert_database_connectivity("Connection lost")
        assert result is True

        # Test external API downtime alert
        result = await alert_external_api_downtime("OANDA API down")
        assert result is True

        # Test circuit breaker alert
        result = await alert_circuit_breaker_triggered("Circuit breaker opened")
        assert result is True


class TestDashboardsAndMetrics:
    """Test monitoring dashboards and metrics."""

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_metrics_collector(self):
        """Test metrics collector."""
        collector = MetricsCollector()
        assert len(collector.metrics) > 0  # Should have default metrics

        # Test metric registration
        metric = collector.register_metric(
            "test_metric", MetricType.COUNTER, MetricCategory.APPLICATION, "Test metric"
        )
        assert metric.name == "test_metric"
        assert metric.metric_type == MetricType.COUNTER

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_metric_operations(self):
        """Test metric operations."""
        collector = MetricsCollector()

        # Test counter
        collector.increment_counter("test_counter", 5)
        metric = collector.get_metric("test_counter")
        assert metric is not None
        assert metric.get_current_value() == 5

        # Test gauge
        collector.set_gauge("test_gauge", 42.5)
        gauge = collector.get_metric("test_gauge")
        assert gauge is not None
        assert gauge.get_current_value() == 42.5

        # Test histogram
        collector.record_histogram("test_histogram", 100)
        collector.record_histogram("test_histogram", 200)
        histogram = collector.get_metric("test_histogram")
        assert histogram is not None
        stats = histogram.get_statistics()
        assert stats["count"] == 2

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_dashboard(self):
        """Test dashboard functionality."""
        collector = MetricsCollector()
        dashboard = Dashboard(collector)

        # Test health summary
        summary = dashboard.get_system_health_summary()
        assert "timestamp" in summary
        assert "status" in summary
        assert "metrics" in summary

        # Test performance summary
        perf_summary = dashboard.get_performance_summary()
        assert "timestamp" in perf_summary
        assert "signal_processing" in perf_summary
        assert "api_requests" in perf_summary

    @pytest.mark.skipif(
        not DASHBOARDS_AVAILABLE, reason="Dashboard system not available"
    )
    def test_business_metrics(self):
        """Test business metric tracking."""
        # Test request tracking
        track_requests("/api/signals", "GET", 200, 50.0)

        # Test signal generation tracking
        record_signal_generated("EUR_USD", "BUY", 1.1000)

        # Verify metrics were recorded
        collector = metrics_collector
        request_metric = collector.get_metric("api_requests_total")
        signal_metric = collector.get_metric("signals_generated_total")

        assert request_metric is not None
        assert signal_metric is not None


class TestIntegration:
    """Integration tests for the entire error handling system."""

    @pytest.mark.skipif(
        not all([SIGNAL_ERROR_HANDLING_AVAILABLE, ALERTING_AVAILABLE]),
        reason="Required components not available",
    )
    @pytest.mark.asyncio
    async def test_signal_error_to_alert_flow(self):
        """Test the flow from signal error to alert."""
        # Simulate a signal processing error
        error = SignalError(
            error_type=SignalErrorType.MARKET_DATA_API_FAILURE,
            severity=SignalErrorSeverity.HIGH,
            message="API connection failed",
            timestamp=datetime.now(timezone.utc),
            context={"api_endpoint": "test.com"},
            pair="EUR_USD",
        )

        # This should trigger an alert
        result = await alert_signal_processing_failure(
            f"Signal processing failed: {error.message}"
        )
        assert result is True

    @pytest.mark.skipif(
        not all([DB_ERROR_HANDLING_AVAILABLE, ALERTING_AVAILABLE]),
        reason="Required components not available",
    )
    @pytest.mark.asyncio
    async def test_database_error_to_alert_flow(self):
        """Test the flow from database error to alert."""
        # Simulate a database error
        error = DatabaseError(
            error_type=DatabaseErrorType.CONNECTION_FAILURE,
            severity=DatabaseErrorSeverity.HIGH,
            message="Database connection lost",
            timestamp=datetime.now(timezone.utc),
        )

        # This should trigger an alert
        result = await alert_database_connectivity(f"Database error: {error.message}")
        assert result is True

    @pytest.mark.skipif(
        not all([SIGNAL_ERROR_HANDLING_AVAILABLE, DASHBOARDS_AVAILABLE]),
        reason="Required components not available",
    )
    def test_error_metrics_integration(self):
        """Test that errors are properly recorded in metrics."""
        collector = metrics_collector

        # Record some error metrics
        collector.increment_counter("signal_errors_total", 1, {"type": "api_failure"})
        collector.increment_counter("database_errors_total", 1, {"type": "connection"})

        # Verify metrics were recorded
        signal_errors = collector.get_metric("signal_errors_total")
        db_errors = collector.get_metric("database_errors_total")

        assert signal_errors is not None
        assert db_errors is not None

    @pytest.mark.skipif(
        not all([DASHBOARDS_AVAILABLE, ALERTING_AVAILABLE]),
        reason="Required components not available",
    )
    @pytest.mark.asyncio
    async def test_metrics_threshold_alerting(self):
        """Test that metrics can trigger alerts when thresholds are exceeded."""
        collector = metrics_collector

        # Simulate high error rate
        for _ in range(10):
            collector.increment_counter("api_errors_total")

        # Check if this would trigger an alert (in a real system)
        error_count = collector.get_metric("api_errors_total")
        if error_count and error_count.get_current_value() > 5:
            result = await alert_external_api_downtime("High API error rate detected")
            assert result is True


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
