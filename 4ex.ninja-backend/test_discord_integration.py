"""
Discord Integration Test Script for 4ex.ninja

This script tests the Discord notification system with sample data
to verify proper integration and formatting.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

# Add the src directory to the Python path
backend_root = Path(__file__).parent
src_path = backend_root / "src"
sys.path.insert(0, str(src_path))

# Import after path setup to avoid import resolution issues
try:
    from core.entities.signal import Signal, SignalType, CrossoverType, SignalStatus
    from infrastructure.monitoring.alerts import Alert, AlertSeverity, AlertType
    from infrastructure.external_services.discord_service import (
        get_discord_service,
        UserTier,
    )
    from infrastructure.monitoring.discord_alerts import (
        EnhancedDiscordAlertChannel,
        send_signal_to_discord,
        send_market_analysis_to_discord,
        send_system_status_to_discord,
    )

    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


async def test_signal_notification():
    """Test signal notification to Discord."""
    print("🧪 Testing Signal Notification...")

    # Create a sample signal
    signal = Signal(
        signal_id="test_signal_001",
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
        strategy_name="MA Crossover Strategy",
    )

    # Test with different user tiers
    discord_service = get_discord_service()

    print("  📤 Sending to Free Tier Channel...")
    success_free = await discord_service.send_signal_notification(
        signal=signal,
        user_tier=UserTier.FREE,
        additional_context={
            "market_conditions": "Trending upward",
            "volatility": "Medium",
            "session": "London Open",
        },
    )

    print("  📤 Sending to Premium Tier Channel...")
    success_premium = await discord_service.send_signal_notification(
        signal=signal,
        user_tier=UserTier.PREMIUM,
        additional_context={
            "advanced_indicators": "RSI: 65, MACD: Bullish",
            "support_resistance": "Support at 1.1000, Resistance at 1.1200",
            "economic_events": "No major events expected",
        },
    )

    print(f"  ✅ Free tier: {'Success' if success_free else 'Failed'}")
    print(f"  ✅ Premium tier: {'Success' if success_premium else 'Failed'}")

    return success_free or success_premium


async def test_system_alert():
    """Test system alert notification to Discord."""
    print("🧪 Testing System Alert...")

    # Create a sample critical alert
    alert = Alert(
        alert_type=AlertType.SYSTEM_RESOURCE_EXHAUSTION,
        severity=AlertSeverity.CRITICAL,
        title="High CPU Usage Detected",
        message="CPU usage has exceeded 95% for the last 5 minutes. Immediate attention required.",
        timestamp=datetime.now(timezone.utc),
        context={
            "cpu_usage": "96.5%",
            "memory_usage": "78.2%",
            "process_count": 145,
            "load_average": "4.2, 3.8, 3.5",
            "affected_services": ["signal_generation", "api_server"],
        },
        source="system_monitor",
        tags=["performance", "cpu", "critical"],
    )

    discord_service = get_discord_service()
    success = await discord_service.send_system_alert(alert)

    print(f"  ✅ System alert: {'Success' if success else 'Failed'}")
    return success


async def test_market_analysis():
    """Test market analysis notification to Discord."""
    print("🧪 Testing Market Analysis...")

    success = await send_market_analysis_to_discord(
        title="EUR/USD Daily Market Analysis",
        analysis=(
            "The EUR/USD pair is showing strong bullish momentum following the ECB's hawkish stance. "
            "Technical indicators suggest a continuation of the uptrend with key resistance at 1.1200. "
            "Volume analysis confirms institutional buying interest."
        ),
        trend_data={
            "short_term": "Bullish (95% confidence)",
            "medium_term": "Bullish (78% confidence)",
            "long_term": "Neutral (52% confidence)",
            "trend_strength": "Strong",
        },
        regime_data={
            "current_regime": "Risk-On",
            "volatility_regime": "Medium",
            "correlation_regime": "Decoupling",
            "regime_probability": "87%",
        },
    )

    print(f"  ✅ Market analysis: {'Success' if success else 'Failed'}")
    return success


async def test_system_status():
    """Test system status notification to Discord."""
    print("🧪 Testing System Status...")

    success = await send_system_status_to_discord(
        status="online",
        message="All systems are operating normally. Signal generation is active and API endpoints are responsive.",
        status_type="info",
        uptime="7 days, 14 hours, 23 minutes",
        performance_metrics={
            "api_response_time": "45ms avg",
            "signal_generation_rate": "12 signals/hour",
            "active_connections": "1,247",
            "memory_usage": "68%",
            "cpu_usage": "23%",
            "database_health": "Excellent",
        },
    )

    print(f"  ✅ System status: {'Success' if success else 'Failed'}")
    return success


async def test_enhanced_alert_channel():
    """Test the enhanced Discord alert channel integration."""
    print("🧪 Testing Enhanced Alert Channel...")

    discord_channel = EnhancedDiscordAlertChannel()

    if not discord_channel.is_available():
        print("  ⚠️ Discord channel not available (check configuration)")
        return False

    # Test signal alert through the enhanced channel
    signal = Signal(
        signal_id="enhanced_test_001",
        pair="GBP/USD",
        timeframe="4H",
        signal_type=SignalType.SELL,
        crossover_type=CrossoverType.BEARISH,
        entry_price=Decimal("1.2750"),
        current_price=Decimal("1.2745"),
        fast_ma=20,
        slow_ma=50,
        timestamp=datetime.now(timezone.utc),
        stop_loss=Decimal("1.2800"),
        take_profit=Decimal("1.2650"),
        confidence_score=0.92,
        strategy_name="Enhanced Crossover Strategy",
    )

    success = await discord_channel.send_signal_alert(
        signal=signal,
        alert_type="high_confidence_signal",
        additional_context={
            "confidence_level": "Very High",
            "market_sentiment": "Risk-Off",
            "news_impact": "Brexit developments affecting GBP",
        },
    )

    print(f"  ✅ Enhanced channel: {'Success' if success else 'Failed'}")
    return success


async def main():
    """Run all Discord integration tests."""
    print("🚀 Starting Discord Integration Tests for 4ex.ninja")
    print("=" * 60)

    # Check environment configuration
    print("\n📋 Checking Configuration...")
    webhook_vars = [
        "DISCORD_WEBHOOK_SIGNALS_FREE",
        "DISCORD_WEBHOOK_SIGNALS_PREMIUM",
        "DISCORD_WEBHOOK_ALERTS_CRITICAL",
        "DISCORD_WEBHOOK_ALERTS_GENERAL",
        "DISCORD_WEBHOOK_MARKET_ANALYSIS",
        "DISCORD_WEBHOOK_SYSTEM_STATUS",
    ]

    configured_webhooks = []
    for var in webhook_vars:
        if os.getenv(var):
            configured_webhooks.append(var)
            print(f"  ✅ {var}: Configured")
        else:
            print(f"  ⚠️ {var}: Not configured")

    if not configured_webhooks:
        print("\n❌ No Discord webhooks configured!")
        print("Please set at least one webhook URL in your environment variables.")
        print("\nExample:")
        print(
            "export DISCORD_WEBHOOK_SIGNALS_FREE='https://discord.com/api/webhooks/YOUR_WEBHOOK_URL'"
        )
        return

    print(f"\n✅ Found {len(configured_webhooks)} configured webhook(s)")

    # Run tests
    print("\n🧪 Running Tests...")
    print("-" * 40)

    tests = [
        ("Signal Notification", test_signal_notification),
        ("System Alert", test_system_alert),
        ("Market Analysis", test_market_analysis),
        ("System Status", test_system_status),
        ("Enhanced Alert Channel", test_enhanced_alert_channel),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n{test_name}:")
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results.append((test_name, False))

    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Discord integration is working correctly.")
    elif passed > 0:
        print("⚠️ Partial success. Check failed tests and Discord configuration.")
    else:
        print(
            "❌ All tests failed. Please check Discord configuration and network connectivity."
        )

    print("\n📝 Next Steps:")
    print("1. Configure additional webhook URLs for missing channels")
    print("2. Set up Discord server with appropriate channels")
    print("3. Configure role-based access control in Discord")
    print("4. Test with real signal generation pipeline")


if __name__ == "__main__":
    asyncio.run(main())
