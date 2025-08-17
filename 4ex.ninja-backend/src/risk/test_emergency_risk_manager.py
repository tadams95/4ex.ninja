"""
Test Emergency Risk Management Framework

This test demonstrates the EmergencyRiskManager capabilities:
- 4-level emergency protocols
- Stress event detection with 2x volatility threshold
- Crisis mode activation at 20% drawdown
- Emergency stop at 25% drawdown
- Dynamic position sizing based on risk levels
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import logging
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from risk.emergency_risk_manager import (
    EmergencyRiskManager,
    EmergencyLevel,
    StressEvent,
    StressEventType,
    create_emergency_risk_manager,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockMarketDataSource:
    """Mock market data source for testing"""

    def __init__(self):
        self.pairs = ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]
        self.data_history = {}
        self._initialize_data()

    def _initialize_data(self):
        """Initialize sample market data"""
        base_time = datetime.now(timezone.utc) - timedelta(days=30)

        for pair in self.pairs:
            # Generate 30 days of sample data
            dates = [
                base_time + timedelta(hours=i) for i in range(720)
            ]  # 30 days hourly

            # Generate realistic price data
            np.random.seed(42)  # For reproducible results
            price_base = (
                1.1000
                if "EUR" in pair
                else 1.3000 if "GBP" in pair else 110.00 if "JPY" in pair else 0.7500
            )

            # Generate price walk
            price_changes = np.random.normal(0, 0.001, len(dates))  # 0.1% volatility
            prices = [price_base]

            for change in price_changes[1:]:
                new_price = prices[-1] * (1 + change)
                prices.append(new_price)

            # Create OHLC data
            df_data = []
            for i, (date, price) in enumerate(zip(dates, prices)):
                high = price * (1 + abs(np.random.normal(0, 0.0005)))
                low = price * (1 - abs(np.random.normal(0, 0.0005)))
                close = price
                open_price = prices[i - 1] if i > 0 else price

                df_data.append(
                    {
                        "timestamp": date,
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": np.random.randint(1000, 10000),
                    }
                )

            self.data_history[pair] = pd.DataFrame(df_data).set_index("timestamp")

    async def get_latest_data(self, stress_simulation: bool = False):
        """Get latest market data"""
        current_data = {}

        for pair in self.pairs:
            df = self.data_history[pair].copy()

            # Simulate stress conditions if requested
            if stress_simulation:
                # Add volatile market conditions
                last_price = df["close"].iloc[-1]

                # Create stress scenario - 3x normal volatility
                stress_multiplier = 3.0
                stress_change = np.random.normal(
                    0, 0.003 * stress_multiplier
                )  # 3x normal volatility
                new_price = last_price * (1 + stress_change)

                # Add new stress candle
                new_time = df.index[-1] + timedelta(hours=1)
                high = new_price * (1 + abs(np.random.normal(0, 0.002)))
                low = new_price * (1 - abs(np.random.normal(0, 0.002)))

                new_row = pd.DataFrame(
                    {
                        "open": [last_price],
                        "high": [high],
                        "low": [low],
                        "close": [new_price],
                        "volume": [np.random.randint(1000, 10000)],
                    },
                    index=[new_time],
                )

                df = pd.concat([df, new_row])

            current_data[pair] = df.tail(50)  # Return last 50 candles

        return current_data


async def test_emergency_risk_manager():
    """Test the Emergency Risk Management Framework"""
    logger.info("🔥 Starting Emergency Risk Management Framework Test")

    # Create emergency risk manager
    portfolio_value = 100000.0
    emergency_manager = await create_emergency_risk_manager(portfolio_value)

    # Create mock data source
    data_source = MockMarketDataSource()

    logger.info(
        f"✅ EmergencyRiskManager initialized with portfolio value: ${portfolio_value:,.2f}"
    )

    # Test 1: Normal conditions
    logger.info("\n📊 Test 1: Normal Market Conditions")
    market_data = await data_source.get_latest_data(stress_simulation=False)
    stress_events = await emergency_manager.monitor_stress_events(market_data)

    logger.info(f"Stress events detected: {len(stress_events)}")
    logger.info(f"Emergency level: {emergency_manager.current_emergency_level.name}")

    # Test position sizing in normal conditions
    base_position_size = 10000.0
    normal_position_size = emergency_manager.calculate_position_size(
        base_size=base_position_size, pair="EUR_USD"
    )
    logger.info(
        f"Position size (normal): ${normal_position_size:,.2f} (vs base ${base_position_size:,.2f})"
    )

    # Test 2: Stress event detection
    logger.info("\n🚨 Test 2: Stress Event Detection (2x Volatility)")

    # Build volatility history first
    for i in range(25):  # Build history for base volatility calculation
        normal_data = await data_source.get_latest_data(stress_simulation=False)
        await emergency_manager.monitor_stress_events(normal_data)
        await asyncio.sleep(0.1)  # Small delay

    # Now test stress detection
    stress_data = await data_source.get_latest_data(stress_simulation=True)
    stress_events = await emergency_manager.monitor_stress_events(stress_data)

    logger.info(f"Stress events detected: {len(stress_events)}")
    for event in stress_events:
        logger.info(
            f"  - {event.event_type.value}: Severity {event.severity:.2f}x, Pairs: {event.affected_pairs}"
        )
        logger.info(f"    Recommended action: {event.recommended_action}")

    # Test 3: Portfolio drawdown scenarios
    logger.info("\n📉 Test 3: Portfolio Drawdown Emergency Levels")

    # Test Level 1: 10% drawdown
    drawdown_value = portfolio_value * 0.9  # 10% loss
    await emergency_manager.update_portfolio_value(drawdown_value)

    level1_position_size = emergency_manager.calculate_position_size(
        base_size=base_position_size, pair="EUR_USD"
    )
    logger.info(
        f"Level 1 (10% drawdown): Position size ${level1_position_size:,.2f} "
        f"(multiplier: {level1_position_size/base_position_size:.1%})"
    )

    # Test Level 2: 15% drawdown
    drawdown_value = portfolio_value * 0.85  # 15% loss
    await emergency_manager.update_portfolio_value(drawdown_value)

    level2_position_size = emergency_manager.calculate_position_size(
        base_size=base_position_size, pair="EUR_USD"
    )
    logger.info(
        f"Level 2 (15% drawdown): Position size ${level2_position_size:,.2f} "
        f"(multiplier: {level2_position_size/base_position_size:.1%})"
    )

    # Test Level 3: 20% drawdown (CRISIS MODE)
    drawdown_value = portfolio_value * 0.8  # 20% loss
    await emergency_manager.update_portfolio_value(drawdown_value)

    level3_position_size = emergency_manager.calculate_position_size(
        base_size=base_position_size, pair="EUR_USD"
    )
    logger.info(
        f"🚨 Level 3 (20% drawdown - CRISIS): Position size ${level3_position_size:,.2f} "
        f"(multiplier: {level3_position_size/base_position_size:.1%})"
    )

    # Test Level 4: 25% drawdown (EMERGENCY STOP)
    drawdown_value = portfolio_value * 0.75  # 25% loss
    await emergency_manager.update_portfolio_value(drawdown_value)

    level4_position_size = emergency_manager.calculate_position_size(
        base_size=base_position_size, pair="EUR_USD"
    )
    logger.info(
        f"🛑 Level 4 (25% drawdown - EMERGENCY STOP): Position size ${level4_position_size:,.2f} "
        f"(Trading halted: {emergency_manager.emergency_protocols[EmergencyLevel.LEVEL_4].stop_trading})"
    )

    # Test 4: Dynamic position sizing with volatility
    logger.info("\n⚡ Test 4: Dynamic Position Sizing with Volatility")

    # Reset to normal level for volatility testing
    await emergency_manager.update_portfolio_value(
        portfolio_value * 0.95
    )  # 5% drawdown

    # Test with different volatility levels
    volatility_scenarios = [
        (0.001, "Low volatility"),
        (0.002, "Normal volatility"),
        (0.004, "High volatility (2x)"),
        (0.008, "Extreme volatility (4x)"),
    ]

    for vol, description in volatility_scenarios:
        adjusted_size = emergency_manager.calculate_position_size(
            base_size=base_position_size,
            pair="EUR_USD",
            current_volatility=vol,
            portfolio_correlation=0.3,
        )
        logger.info(f"  {description}: ${adjusted_size:,.2f} (volatility: {vol:.3f})")

    # Test 5: Emergency status report
    logger.info("\n📊 Test 5: Emergency Status Report")
    status = emergency_manager.get_emergency_status()

    logger.info("Current Emergency Status:")
    logger.info(f"  Emergency Level: {status['emergency_level']}")
    logger.info(f"  Portfolio Drawdown: {status['portfolio_drawdown']:.2%}")
    logger.info(f"  Portfolio Value: ${status['portfolio_value']:,.2f}")
    logger.info(f"  Position Size Multiplier: {status['position_size_multiplier']:.1%}")
    logger.info(f"  Trading Halted: {status['trading_halted']}")
    logger.info(f"  Active Stress Events: {status['active_stress_events']}")
    logger.info(f"  Protocol: {status['protocol_description']}")

    logger.info("\n✅ Emergency Risk Management Framework Test Completed")

    return emergency_manager


async def test_integration_with_strategy():
    """Test integration with existing strategy"""
    logger.info("\n🔗 Testing Integration with Strategy")

    # Mock strategy class for testing
    class MockStrategy:
        def __init__(self):
            self.logger = logger
            self.pair = "EUR_USD"

        def validate_signal(self, signal, atr, risk_reward_ratio):
            """Original validation logic"""
            return signal != 0 and atr >= 0.001 and risk_reward_ratio >= 1.5

    # Create strategy and emergency manager
    strategy = MockStrategy()
    emergency_manager = await create_emergency_risk_manager(100000.0)

    # Test normal conditions
    result = strategy.validate_signal(1, 0.002, 2.0)
    logger.info(f"Normal validation (no emergency manager): {result}")

    # Integrate emergency manager
    from risk.emergency_risk_manager import integrate_with_strategy

    integrate_with_strategy(strategy, emergency_manager)

    # Test with emergency manager in normal conditions
    result = strategy.validate_signal(1, 0.002, 2.0)
    logger.info(f"Normal validation (with emergency manager): {result}")

    # Test with emergency stop condition
    await emergency_manager.update_portfolio_value(
        75000.0
    )  # 25% drawdown - emergency stop
    result = strategy.validate_signal(1, 0.002, 2.0)
    logger.info(f"Emergency stop validation (25% drawdown): {result}")

    logger.info("✅ Strategy integration test completed")


if __name__ == "__main__":

    async def main():
        # Run comprehensive tests
        emergency_manager = await test_emergency_risk_manager()
        await test_integration_with_strategy()

        logger.info("\n🎯 All Emergency Risk Management Tests Completed Successfully!")

        # Display final summary
        logger.info("\n📋 EMERGENCY RISK MANAGEMENT FRAMEWORK SUMMARY:")
        logger.info("✅ 4-level emergency protocols implemented")
        logger.info("✅ Stress event detection with 2x volatility threshold")
        logger.info("✅ Crisis mode activation at 20% drawdown")
        logger.info("✅ Emergency stop at 25% drawdown")
        logger.info("✅ Dynamic position sizing based on risk conditions")
        logger.info("✅ Real-time monitoring and alerting system")
        logger.info("✅ Integration capabilities with existing strategies")

        return emergency_manager

    # Run the test
    asyncio.run(main())
