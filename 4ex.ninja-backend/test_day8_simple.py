#!/usr/bin/env python3
"""
Simple test runner for Day 8 critical system error handling and alerting.

This script tests the basic functionality without requiring pytest.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))


def test_signal_error_handling():
    """Test signal processing error handling."""
    print("Testing Signal Error Handling...")

    try:
        from src.strategies.error_handling import (
            SignalErrorHandler,
            SignalError,
            SignalErrorType,
            SignalErrorSeverity,
            validate_market_data,
            validate_signal_data,
        )

        # Test error creation
        error = SignalError(
            error_type=SignalErrorType.MARKET_DATA_API_FAILURE,
            severity=SignalErrorSeverity.HIGH,
            message="API connection failed",
            timestamp=datetime.now(timezone.utc),
            context={"api_endpoint": "test.com"},
            pair="EUR_USD",
        )

        assert error.error_type == SignalErrorType.MARKET_DATA_API_FAILURE
        assert error.pair == "EUR_USD"
        print("✓ Signal error creation working")

        # Test error handler
        handler = SignalErrorHandler()
        assert handler.max_retry_attempts == 3
        print("✓ Signal error handler initialization working")

        # Test data validation
        valid_data = {
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0950,
            "close": 1.1025,
            "timestamp": 1625097600,
        }
        assert validate_market_data(valid_data)
        print("✓ Market data validation working")

        # Test signal validation
        valid_signal = {
            "pair": "EUR_USD",
            "action": "BUY",
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "take_profit": 1.1100,
            "timestamp": 1625097600,
        }
        assert validate_signal_data(valid_signal)
        print("✓ Signal data validation working")

        return True

    except ImportError as e:
        print(f"✗ Signal error handling not available: {e}")
        return False
    except Exception as e:
        print(f"✗ Signal error handling test failed: {e}")
        return False


def test_database_error_handling():
    """Test database operation error handling."""
    print("\nTesting Database Error Handling...")

    try:
        from src.infrastructure.repositories.error_handling import (
            DatabaseErrorHandler,
            DatabaseError,
            DatabaseErrorType,
            DatabaseErrorSeverity,
            ConnectionPoolManager,
            validate_document,
            check_constraint_violations,
        )

        # Test connection pool manager
        pool = ConnectionPoolManager("mongodb://localhost:27017")
        assert pool.connection_string == "mongodb://localhost:27017"
        print("✓ Connection pool manager creation working")

        # Test database error handler
        handler = DatabaseErrorHandler(pool)
        assert handler.max_retry_attempts == 3
        print("✓ Database error handler initialization working")

        # Test document validation
        schema = {
            "required": ["name"],
            "types": {"name": "string"},
            "constraints": {"name": {"min_length": 2}},
        }

        valid_doc = {"name": "John Doe"}
        errors = validate_document(valid_doc, schema)
        assert len(errors) == 0
        print("✓ Document validation working")

        # Test constraint violations
        valid_signal = {
            "action": "BUY",
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "pair": "EUR_USD",
        }
        violations = check_constraint_violations(valid_signal, "signals")
        assert len(violations) == 0
        print("✓ Constraint violation checking working")

        return True

    except ImportError as e:
        print(f"✗ Database error handling not available: {e}")
        return False
    except Exception as e:
        print(f"✗ Database error handling test failed: {e}")
        return False


async def test_alerting_system():
    """Test critical system alerting."""
    print("\nTesting Alerting System...")

    try:
        from src.infrastructure.monitoring.alerts import (
            AlertManager,
            Alert,
            AlertType,
            AlertSeverity,
            AlertStatus,
            LogAlertChannel,
            alert_signal_processing_failure,
        )

        # Test alert creation
        alert = Alert(
            alert_type=AlertType.SIGNAL_PROCESSING_FAILURE,
            severity=AlertSeverity.HIGH,
            title="Signal Processing Failed",
            message="Unable to process market data",
            timestamp=datetime.now(timezone.utc),
        )

        assert alert.alert_type == AlertType.SIGNAL_PROCESSING_FAILURE
        assert alert.status == AlertStatus.ACTIVE
        print("✓ Alert creation working")

        # Test log alert channel
        channel = LogAlertChannel()
        assert channel.is_available()
        result = await channel.send_alert(alert)
        assert result is True
        print("✓ Log alert channel working")

        # Test alert manager
        manager = AlertManager()
        assert len(manager.channels) > 0
        print("✓ Alert manager initialization working")

        # Test convenience function
        result = await alert_signal_processing_failure("Test failure")
        assert result is True
        print("✓ Convenience alert functions working")

        return True

    except ImportError as e:
        print(f"✗ Alerting system not available: {e}")
        return False
    except Exception as e:
        print(f"✗ Alerting system test failed: {e}")
        return False


def test_dashboards_metrics():
    """Test monitoring dashboards and metrics."""
    print("\nTesting Dashboards and Metrics...")

    try:
        from src.infrastructure.monitoring.dashboards import (
            MetricsCollector,
            Dashboard,
            Metric,
            MetricType,
            MetricCategory,
        )

        # Test metrics collector
        collector = MetricsCollector()
        assert len(collector.metrics) > 0
        print("✓ Metrics collector initialization working")

        # Test metric registration
        metric = collector.register_metric(
            "test_metric", MetricType.COUNTER, MetricCategory.APPLICATION, "Test metric"
        )
        assert metric.name == "test_metric"
        print("✓ Metric registration working")

        # Test counter increment
        collector.increment_counter("test_metric", 5)
        test_metric = collector.get_metric("test_metric")
        assert test_metric is not None
        value = test_metric.get_current_value()
        assert value == 5
        print("✓ Counter increment working")

        # Test dashboard
        dashboard = Dashboard(collector)
        summary = dashboard.get_system_health_summary()
        assert "timestamp" in summary
        assert "status" in summary
        print("✓ Dashboard functionality working")

        return True

    except ImportError as e:
        print(f"✗ Dashboard system not available: {e}")
        return False
    except Exception as e:
        print(f"✗ Dashboard system test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Day 8 Critical System Error Handling and Alerting Tests")
    print("=" * 60)

    results = []

    # Run tests
    results.append(test_signal_error_handling())
    results.append(test_database_error_handling())
    results.append(await test_alerting_system())
    results.append(test_dashboards_metrics())

    # Summary
    passed = sum(results)
    total = len(results)

    print(f"\nTest Summary:")
    print(f"=" * 30)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 All Day 8 components implemented successfully!")
        return True
    else:
        print(f"\n⚠️  {total - passed} components need attention")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
