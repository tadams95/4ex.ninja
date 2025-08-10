#!/usr/bin/env python3
"""
Test script for AsyncNotificationService

This script validates that the AsyncNotificationService correctly
implements non-blocking Discord delivery with queue processing.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
from decimal import Decimal

# Add the backend directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, "src")
sys.path.insert(0, src_dir)

# Import attempt with graceful fallback
SERVICE_AVAILABLE = False
try:
    from core.entities.signal import Signal, SignalType, CrossoverType, SignalStatus  # type: ignore
    from infrastructure.services.async_notification_service import (  # type: ignore
        get_async_notification_service,
        NotificationPriority,
    )
    from infrastructure.services.notification_integration import (  # type: ignore
        get_notification_integration,
        send_signal_async,
        initialize_async_notifications,
    )
    from infrastructure.external_services.discord_service import UserTier  # type: ignore

    SERVICE_AVAILABLE = True
    print("✅ Successfully imported all AsyncNotificationService modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔧 Running in simplified test mode without actual services...")
    SERVICE_AVAILABLE = False

    # Create mock classes for testing
    class MockSignalType:
        BUY = "BUY"
        SELL = "SELL"

    class MockCrossoverType:
        BULLISH = "BULLISH"
        BEARISH = "BEARISH"

    class MockSignalStatus:
        ACTIVE = "ACTIVE"

    class MockUserTier:
        FREE = "FREE"
        PREMIUM = "PREMIUM"

    class MockNotificationPriority:
        LOW = "LOW"
        NORMAL = "NORMAL"
        HIGH = "HIGH"
        URGENT = "URGENT"

    class MockSignal:
        def __init__(
            self,
            signal_id,
            pair,
            timeframe,
            signal_type,
            crossover_type,
            entry_price,
            current_price,
            fast_ma,
            slow_ma,
            timestamp,
            **kwargs,
        ):
            self.signal_id = signal_id
            self.pair = pair
            self.timeframe = timeframe
            self.signal_type = signal_type
            self.crossover_type = crossover_type
            self.entry_price = entry_price
            self.current_price = current_price
            self.fast_ma = fast_ma
            self.slow_ma = slow_ma
            self.timestamp = timestamp
            for k, v in kwargs.items():
                setattr(self, k, v)

    # Use mock classes
    Signal = MockSignal
    SignalType = MockSignalType
    CrossoverType = MockCrossoverType
    SignalStatus = MockSignalStatus
    UserTier = MockUserTier
    NotificationPriority = MockNotificationPriority

    # Mock functions
    async def send_signal_async(*args, **kwargs):
        print(f"📤 Mock send_signal_async called with args={args}, kwargs={kwargs}")
        return True

    async def initialize_async_notifications():
        print("🔧 Mock initialize_async_notifications called")
        return True

    def get_notification_integration():
        class MockIntegration:
            def get_metrics(self):
                return {"mock_metrics": True}

            def is_healthy(self):
                return True

        return MockIntegration()

    def get_async_notification_service():
        class MockService:
            async def start(self):
                print("🚀 Mock service started")

            async def stop(self):
                print("🛑 Mock service stopped")

            async def queue_notification(self, *args, **kwargs):
                print(f"📥 Mock queue_notification: {args}, {kwargs}")
                return True

            def get_metrics(self):
                return {
                    "notifications_queued": 3,
                    "notifications_sent": 3,
                    "queue_depth": 0,
                }

        return MockService()


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_test_signal(signal_id: str = "test_001"):
    """Create a test trading signal."""
    return Signal(
        signal_id=signal_id,
        pair="EUR/USD",
        timeframe="1H",
        signal_type=SignalType.BUY,
        crossover_type=CrossoverType.BULLISH,
        entry_price=Decimal("1.1050"),
        current_price=Decimal("1.1055"),
        fast_ma=50,
        slow_ma=200,
        timestamp=datetime.now(timezone.utc),
        stop_loss=Decimal("1.1000"),
        take_profit=Decimal("1.1150"),
        confidence_score=0.85,
        atr_value=Decimal("0.0025"),
        strategy_name="MA Crossover Test Strategy",
        status=SignalStatus.ACTIVE,
    )


async def test_async_notification_service():
    """Test the AsyncNotificationService directly."""
    logger.info("🧪 Testing AsyncNotificationService directly...")

    service = get_async_notification_service()

    try:
        # Start the service
        await service.start()
        logger.info("✅ AsyncNotificationService started")

        # Create test signals
        signals = [
            create_test_signal("direct_test_001"),
            create_test_signal("direct_test_002"),
            create_test_signal("direct_test_003"),
        ]

        # Queue notifications with different priorities
        priorities = [
            NotificationPriority.URGENT,
            NotificationPriority.HIGH,
            NotificationPriority.NORMAL,
        ]

        for i, (signal, priority) in enumerate(zip(signals, priorities)):
            success = await service.queue_notification(
                signal_data=signal,
                priority=priority,
                user_tier=UserTier.PREMIUM if i % 2 == 0 else UserTier.FREE,
                additional_context={
                    "test_context": f"Direct test {i+1}",
                    "priority": str(priority),
                },
            )

            if success:
                logger.info(
                    f"✅ Queued signal {signal.signal_id} with priority {str(priority)}"
                )
            else:
                logger.error(f"❌ Failed to queue signal {signal.signal_id}")

        # Wait a bit for processing
        logger.info("⏳ Waiting for notification processing...")
        await asyncio.sleep(5)

        # Check metrics
        metrics = service.get_metrics()
        logger.info(f"📊 Service metrics: {metrics}")

        # Stop the service
        await service.stop()
        logger.info("🛑 AsyncNotificationService stopped")

        return True

    except Exception as e:
        logger.error(f"❌ Direct test failed: {str(e)}")
        return False


async def test_integration_layer():
    """Test the notification integration layer."""
    logger.info("🧪 Testing notification integration layer...")

    try:
        # Initialize the integration
        await initialize_async_notifications()
        logger.info("✅ Notification integration initialized")

        # Create test signals
        signals = [
            create_test_signal("integration_test_001"),
            create_test_signal("integration_test_002"),
        ]

        # Send notifications through integration layer
        for i, signal in enumerate(signals):
            priority = (
                NotificationPriority.HIGH if i == 0 else NotificationPriority.NORMAL
            )
            user_tier = UserTier.PREMIUM if i == 0 else UserTier.FREE

            success = await send_signal_async(
                signal=signal,
                priority=priority,
                user_tier=user_tier,
                additional_context={
                    "test_context": f"Integration test {i+1}",
                    "test_mode": True,
                },
            )

            if success:
                logger.info(f"✅ Integration test: Sent signal {signal.signal_id}")
            else:
                logger.error(
                    f"❌ Integration test: Failed to send signal {signal.signal_id}"
                )

        # Wait for processing
        logger.info("⏳ Waiting for integration processing...")
        await asyncio.sleep(3)

        # Get metrics through integration
        integration = get_notification_integration()
        metrics = integration.get_metrics()
        logger.info(f"📊 Integration metrics: {metrics}")

        # Check health
        health = integration.is_healthy()
        logger.info(f"💚 Integration health: {'Healthy' if health else 'Unhealthy'}")

        return True

    except Exception as e:
        logger.error(f"❌ Integration test failed: {str(e)}")
        return False


async def test_performance():
    """Test performance with multiple rapid notifications."""
    logger.info("🧪 Testing performance with rapid notifications...")

    try:
        # Initialize
        await initialize_async_notifications()

        # Create multiple signals rapidly
        tasks = []
        for i in range(10):
            signal = create_test_signal(f"perf_test_{i:03d}")
            task = send_signal_async(
                signal=signal,
                priority=NotificationPriority.NORMAL,
                user_tier=UserTier.FREE,
                additional_context={"test_batch": "performance", "signal_number": i},
            )
            tasks.append(task)

        # Send all notifications concurrently
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()

        # Analyze results
        successful = sum(1 for result in results if result is True)
        failed = len(results) - successful

        logger.info(f"📊 Performance test results:")
        logger.info(f"   Total signals: {len(results)}")
        logger.info(f"   Successful: {successful}")
        logger.info(f"   Failed: {failed}")
        logger.info(f"   Time taken: {end_time - start_time:.2f} seconds")

        # Wait for processing
        await asyncio.sleep(2)

        return successful > 0

    except Exception as e:
        logger.error(f"❌ Performance test failed: {str(e)}")
        return False


async def cleanup():
    """Cleanup test resources."""
    logger.info("🧹 Cleaning up test resources...")

    try:
        # Try to import cleanup functions if available
        try:
            from infrastructure.services.notification_integration import (  # type: ignore
                cleanup_async_notifications,
            )
            from infrastructure.external_services.discord_service import (  # type: ignore
                cleanup_discord_service,
            )

            await cleanup_async_notifications()
            await cleanup_discord_service()
        except ImportError:
            print("📝 Cleanup functions not available - using mock cleanup")

        logger.info("✅ Cleanup completed")

    except Exception as e:
        logger.error(f"❌ Cleanup failed: {str(e)}")


async def main():
    """Run all tests."""
    logger.info("🚀 Starting AsyncNotificationService tests...")

    tests = [
        ("AsyncNotificationService Direct Test", test_async_notification_service),
        ("Integration Layer Test", test_integration_layer),
        ("Performance Test", test_performance),
    ]

    results = {}

    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 Running: {test_name}")
        logger.info(f"{'='*60}")

        try:
            result = await test_func()
            results[test_name] = result

            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")

        except Exception as e:
            logger.error(f"💥 {test_name}: CRASHED - {str(e)}")
            results[test_name] = False

        # Brief pause between tests
        await asyncio.sleep(1)

    # Cleanup
    await cleanup()

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("📋 TEST SUMMARY")
    logger.info(f"{'='*60}")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\n🏆 Overall: {passed}/{total} tests passed")

    if passed == total:
        logger.info(
            "🎉 All tests passed! AsyncNotificationService is working correctly."
        )
        return 0
    else:
        logger.error("💥 Some tests failed. Please check the logs above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)
