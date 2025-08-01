"""
Day 6: Logging Infrastructure Tests

Tests for the comprehensive logging system including:
- Basic logging functionality
- Context-aware logging with correlation IDs
- Performance monitoring
- Error logging with context
- FastAPI middleware integration
"""

import sys
import os
import time

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.infrastructure.logging import (
    get_logger,
    setup_logging,
    BaseLoggerMixin,
    set_correlation_id,
    set_user_id,
    generate_correlation_id,
    log_with_context,
    FASTAPI_AVAILABLE,
)


def test_basic_logging():
    """Test basic logging functionality."""
    print("🔧 Testing basic logging...")

    # Setup logging
    setup_logging()

    # Get a logger
    logger = get_logger("test.basic")

    # Test basic logging
    logger.info("Basic logging test successful")
    logger.warning("This is a warning message")
    logger.error("This is an error message", exc_info=False)

    print("✅ Basic logging test passed")


def test_context_logging():
    """Test context-aware logging."""
    print("🔧 Testing context-aware logging...")

    # Setup context
    correlation_id = generate_correlation_id()
    set_correlation_id(correlation_id)
    set_user_id("test_user_123")

    logger = get_logger("test.context")

    # Test context injection
    import logging

    log_with_context(
        logger,
        logging.INFO,
        "Context logging test",
        operation="test_operation",
        additional_data="some_value",
    )

    print("✅ Context logging test passed")


def test_performance_logging():
    """Test performance logging using BaseLoggerMixin."""
    print("🔧 Testing performance logging...")

    class TestService(BaseLoggerMixin):
        def __init__(self):
            super().__init__("test.performance")

        def slow_operation(self):
            start_time = time.time()

            # Simulate work
            time.sleep(0.1)

            duration = time.time() - start_time

            self.log_performance(
                "slow_operation",
                duration,
                threshold=0.05,  # 50ms threshold
                operation_type="simulation",
                data_processed=100,
            )

    service = TestService()
    service.slow_operation()

    print("✅ Performance logging test passed")


def test_error_logging():
    """Test error logging with context."""
    print("🔧 Testing error logging...")

    class TestService(BaseLoggerMixin):
        def __init__(self):
            super().__init__("test.errors")

        def failing_operation(self):
            try:
                # Simulate an error
                raise ValueError("This is a test error")
            except Exception as e:
                self.log_error(
                    e,
                    "failing_operation",
                    operation_id="test_123",
                    input_data="invalid_input",
                )

    service = TestService()
    service.failing_operation()

    print("✅ Error logging test passed")


def test_fastapi_availability():
    """Test FastAPI availability detection."""
    print("🔧 Testing FastAPI availability...")

    print(f"FastAPI Available: {FASTAPI_AVAILABLE}")

    if FASTAPI_AVAILABLE:
        from src.infrastructure.logging import LoggingMiddleware, setup_middleware

        print("✅ FastAPI middleware components available")
    else:
        print("ℹ️  FastAPI not installed - middleware components unavailable (expected)")

    print("✅ FastAPI availability test passed")


def run_day6_tests():
    """Run all Day 6 logging tests."""
    print("🚀 Starting Day 6: Logging Infrastructure Tests\n")

    try:
        test_basic_logging()
        print()

        test_context_logging()
        print()

        test_performance_logging()
        print()

        test_error_logging()
        print()

        test_fastapi_availability()
        print()

        print("🎉 All Day 6 tests passed! Logging infrastructure is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Day 6 test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_day6_tests()
    sys.exit(0 if success else 1)
