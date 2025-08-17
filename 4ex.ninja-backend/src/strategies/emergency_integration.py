"""
Integration Guide: Emergency Risk Management Framework with MA_Unified_Strat

This file demonstrates how to integrate the EmergencyRiskManager with the existing
MovingAverageCrossStrategy to implement the 4-level emergency protocols.

PRIORITY 1: CRITICAL RISK MANAGEMENT IMPLEMENTATION
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

# Import the Emergency Risk Management Framework
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from risk.emergency_risk_manager import (
    EmergencyRiskManager,
    EmergencyLevel,
    create_emergency_risk_manager,
    integrate_with_strategy,
)

# Import existing MA strategy (assuming it's already imported in the main file)
# from strategies.MA_Unified_Strat import MovingAverageCrossStrategy

logger = logging.getLogger(__name__)


class EnhancedMovingAverageCrossStrategy:
    """
    Enhanced version of MovingAverageCrossStrategy with Emergency Risk Management

    This class extends the existing strategy with:
    - 4-level emergency protocols
    - Stress event detection
    - Dynamic position sizing
    - Crisis mode activation
    - Emergency stop mechanisms
    """

    def __init__(
        self,
        original_strategy,
        portfolio_initial_value: float = 100000.0,
        enable_emergency_management: bool = True,
    ):
        """
        Initialize enhanced strategy with emergency risk management

        Args:
            original_strategy: Instance of MovingAverageCrossStrategy
            portfolio_initial_value: Initial portfolio value for drawdown calculations
            enable_emergency_management: Enable/disable emergency protocols
        """
        self.original_strategy = original_strategy
        self.portfolio_initial_value = portfolio_initial_value
        self.enable_emergency_management = enable_emergency_management

        # Initialize emergency risk manager
        self.emergency_manager = None
        self.portfolio_current_value = portfolio_initial_value

        # Copy original strategy attributes
        for attr in [
            "pair",
            "timeframe",
            "slow_ma",
            "fast_ma",
            "atr_period",
            "sl_atr_multiplier",
            "tp_atr_multiplier",
            "min_atr_value",
            "min_rr_ratio",
            "sleep_seconds",
            "min_candles",
        ]:
            if hasattr(original_strategy, attr):
                setattr(self, attr, getattr(original_strategy, attr))

        logger.info(
            f"Enhanced strategy initialized for {self.pair} with emergency management: {enable_emergency_management}"
        )

    async def initialize_emergency_manager(self):
        """Initialize the emergency risk manager"""
        if self.enable_emergency_management:
            self.emergency_manager = await create_emergency_risk_manager(
                portfolio_value=self.portfolio_initial_value
            )
            logger.info(f"Emergency Risk Manager initialized for {self.pair}")
        else:
            logger.info(f"Emergency Risk Manager disabled for {self.pair}")

    def enhanced_validate_signal(
        self,
        signal: int,
        atr: float,
        risk_reward_ratio: float,
        current_market_data: Optional[Dict] = None,
    ) -> bool:
        """
        Enhanced signal validation with emergency risk management

        Args:
            signal: Trading signal (-1, 0, 1)
            atr: Average True Range value
            risk_reward_ratio: Risk-reward ratio
            current_market_data: Current market data for stress detection

        Returns:
            bool: Whether signal is valid under current risk conditions
        """
        try:
            # First, apply original validation logic
            original_valid = self.original_strategy.validate_signal(
                signal, atr, risk_reward_ratio
            )

            if not original_valid:
                return False

            # If emergency management is disabled, return original result
            if not self.enable_emergency_management or not self.emergency_manager:
                return original_valid

            # Check emergency protocols
            emergency_status = self.emergency_manager.get_emergency_status()

            # Emergency stop check
            if emergency_status.get("trading_halted", False):
                logger.warning(
                    f"Signal REJECTED for {self.pair}: Trading halted due to emergency protocol Level {emergency_status.get('emergency_level')}"
                )
                return False

            # Crisis mode additional validation
            if emergency_status.get("emergency_level") in ["LEVEL_3", "LEVEL_4"]:
                # In crisis mode, apply stricter criteria
                if risk_reward_ratio < 3.0:  # Require higher RR in crisis
                    logger.warning(
                        f"Signal REJECTED for {self.pair}: Insufficient RR ratio ({risk_reward_ratio:.2f}) during crisis mode"
                    )
                    return False

                if atr < self.min_atr_value * 1.5:  # Require higher ATR in crisis
                    logger.warning(
                        f"Signal REJECTED for {self.pair}: Insufficient ATR ({atr:.4f}) during crisis mode"
                    )
                    return False

            # Stress event validation
            active_stress_events = emergency_status.get("active_stress_events", 0)
            if active_stress_events > 0:
                logger.warning(
                    f"Signal evaluated under stress conditions: {active_stress_events} active events"
                )

                # Reduce signal acceptance during stress
                if (
                    emergency_status.get("emergency_level_value", 0) >= 2
                ):  # Level 2 or higher
                    # Only accept signals with very high confidence
                    if risk_reward_ratio < 2.5:
                        logger.warning(
                            f"Signal REJECTED for {self.pair}: Insufficient RR during stress event"
                        )
                        return False

            logger.info(
                f"Signal ACCEPTED for {self.pair} under emergency level {emergency_status.get('emergency_level')}"
            )
            return True

        except Exception as e:
            logger.error(f"Error in enhanced signal validation for {self.pair}: {e}")
            return False  # Conservative approach during errors

    def calculate_enhanced_position_size(
        self,
        base_size: float,
        current_volatility: Optional[float] = None,
        market_correlation: float = 0.0,
    ) -> float:
        """
        Calculate position size with emergency risk management

        Args:
            base_size: Base position size from original strategy
            current_volatility: Current market volatility
            market_correlation: Correlation with other positions

        Returns:
            float: Risk-adjusted position size
        """
        try:
            if not self.enable_emergency_management or not self.emergency_manager:
                return base_size

            # Use emergency manager for dynamic position sizing
            adjusted_size = self.emergency_manager.calculate_position_size(
                base_size=base_size,
                pair=self.pair,
                current_volatility=current_volatility,
                portfolio_correlation=market_correlation,
            )

            emergency_status = self.emergency_manager.get_emergency_status()
            logger.info(
                f"Position sizing for {self.pair}: ${base_size:.2f} -> ${adjusted_size:.2f} "
                f"(Emergency Level: {emergency_status.get('emergency_level')}, "
                f"Multiplier: {emergency_status.get('position_size_multiplier', 1.0):.1%})"
            )

            return adjusted_size

        except Exception as e:
            logger.error(
                f"Error calculating enhanced position size for {self.pair}: {e}"
            )
            return base_size * 0.5  # Conservative fallback

    async def update_portfolio_value(self, new_value: float):
        """Update portfolio value for emergency protocol monitoring"""
        try:
            if self.enable_emergency_management and self.emergency_manager:
                await self.emergency_manager.update_portfolio_value(new_value)
                self.portfolio_current_value = new_value

                # Log portfolio status
                drawdown = (
                    self.portfolio_initial_value - new_value
                ) / self.portfolio_initial_value
                logger.info(
                    f"Portfolio updated for {self.pair}: ${new_value:,.2f} (Drawdown: {drawdown:.2%})"
                )

        except Exception as e:
            logger.error(f"Error updating portfolio value for {self.pair}: {e}")

    async def monitor_stress_events(self, market_data: Dict):
        """Monitor for stress events and update emergency protocols"""
        try:
            if self.enable_emergency_management and self.emergency_manager:
                stress_events = await self.emergency_manager.monitor_stress_events(
                    market_data
                )

                if stress_events:
                    logger.warning(
                        f"Stress events detected for {self.pair}: {len(stress_events)} events"
                    )
                    for event in stress_events[:3]:  # Log first 3 events
                        logger.warning(
                            f"  - {event.event_type.value}: Severity {event.severity:.2f}x"
                        )

                return stress_events

            return []

        except Exception as e:
            logger.error(f"Error monitoring stress events for {self.pair}: {e}")
            return []

    def get_emergency_status(self) -> Dict:
        """Get current emergency status"""
        if self.enable_emergency_management and self.emergency_manager:
            return self.emergency_manager.get_emergency_status()
        else:
            return {
                "emergency_level": "DISABLED",
                "portfolio_drawdown": 0.0,
                "trading_halted": False,
                "emergency_management_enabled": False,
            }

    # Delegate other methods to original strategy
    def __getattr__(self, name):
        """Delegate unknown attributes to original strategy"""
        return getattr(self.original_strategy, name)


async def integrate_emergency_management_with_existing_strategy():
    """
    Example integration with existing MovingAverageCrossStrategy
    """
    logger.info("🔧 Integrating Emergency Risk Management with MA_Unified_Strat")

    # This would be your existing strategy initialization
    # original_strategy = MovingAverageCrossStrategy(
    #     pair="EUR_USD",
    #     timeframe="H1",
    #     slow_ma=50,
    #     fast_ma=20,
    #     atr_period=14,
    #     sl_atr_multiplier=2.0,
    #     tp_atr_multiplier=3.0,
    #     min_atr_value=0.001,
    #     min_rr_ratio=1.5,
    #     sleep_seconds=30,
    #     min_candles=100
    # )

    # For demonstration, create a mock strategy
    class MockOriginalStrategy:
        def __init__(self):
            self.pair = "EUR_USD"
            self.timeframe = "H1"
            self.slow_ma = 50
            self.fast_ma = 20
            self.min_atr_value = 0.001
            self.min_rr_ratio = 1.5

        def validate_signal(self, signal, atr, risk_reward_ratio):
            return (
                signal != 0
                and atr >= self.min_atr_value
                and risk_reward_ratio >= self.min_rr_ratio
            )

    original_strategy = MockOriginalStrategy()

    # Create enhanced strategy with emergency management
    enhanced_strategy = EnhancedMovingAverageCrossStrategy(
        original_strategy=original_strategy,
        portfolio_initial_value=100000.0,
        enable_emergency_management=True,
    )

    # Initialize emergency manager
    await enhanced_strategy.initialize_emergency_manager()

    # Test normal signal validation
    logger.info("📊 Testing signal validation under different conditions:")

    # Normal conditions
    result = enhanced_strategy.enhanced_validate_signal(1, 0.002, 2.0)
    logger.info(f"Normal conditions: Signal valid = {result}")

    # Simulate portfolio drawdown to Level 3 (Crisis Mode)
    await enhanced_strategy.update_portfolio_value(80000.0)  # 20% drawdown
    result = enhanced_strategy.enhanced_validate_signal(1, 0.002, 2.0)
    logger.info(f"Crisis mode (20% drawdown) with RR 2.0: Signal valid = {result}")

    result = enhanced_strategy.enhanced_validate_signal(1, 0.002, 3.5)
    logger.info(f"Crisis mode (20% drawdown) with RR 3.5: Signal valid = {result}")

    # Simulate emergency stop
    await enhanced_strategy.update_portfolio_value(75000.0)  # 25% drawdown
    result = enhanced_strategy.enhanced_validate_signal(1, 0.002, 4.0)
    logger.info(f"Emergency stop (25% drawdown): Signal valid = {result}")

    # Test position sizing
    logger.info("💰 Testing dynamic position sizing:")

    # Reset to normal conditions
    await enhanced_strategy.update_portfolio_value(95000.0)  # 5% drawdown

    base_size = 10000.0
    volatility_scenarios = [
        (0.001, "Low volatility"),
        (0.002, "Normal volatility"),
        (0.004, "High volatility"),
        (0.008, "Extreme volatility"),
    ]

    for vol, description in volatility_scenarios:
        adjusted_size = enhanced_strategy.calculate_enhanced_position_size(
            base_size=base_size, current_volatility=vol, market_correlation=0.3
        )
        logger.info(f"  {description}: ${adjusted_size:,.2f} (from ${base_size:,.2f})")

    # Display final status
    status = enhanced_strategy.get_emergency_status()
    logger.info("📊 Final Emergency Status:")
    logger.info(f"  Emergency Level: {status.get('emergency_level')}")
    logger.info(f"  Portfolio Drawdown: {status.get('portfolio_drawdown', 0):.2%}")
    logger.info(f"  Trading Halted: {status.get('trading_halted')}")

    logger.info("✅ Emergency Risk Management integration completed successfully!")

    return enhanced_strategy


# Integration helper for existing MA_Unified_Strat.py
def create_emergency_enhanced_strategy(
    original_strategy_instance, portfolio_value: float = 100000.0
):
    """
    Simple helper to enhance existing strategy with emergency management

    Usage in MA_Unified_Strat.py:

    # After creating original strategy
    strategy = MovingAverageCrossStrategy(...)

    # Enhance with emergency management
    enhanced_strategy = create_emergency_enhanced_strategy(strategy, 100000.0)
    """
    return EnhancedMovingAverageCrossStrategy(
        original_strategy=original_strategy_instance,
        portfolio_initial_value=portfolio_value,
        enable_emergency_management=True,
    )


if __name__ == "__main__":

    async def main():
        await integrate_emergency_management_with_existing_strategy()

    asyncio.run(main())
