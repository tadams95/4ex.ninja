#!/usr/bin/env python3
"""
Simple validation test for the Swing Backtesting Framework.

This script validates that the backtesting framework can run a basic
backtest using the existing infrastructure.

Note: Import errors in the IDE are expected since we dynamically modify
sys.path at runtime. The script runs correctly when executed.
"""

import sys
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend src to path - this resolves the import issues at runtime
sys.path.append(str(Path(__file__).parent / "src"))

# These imports work at runtime after the path modification above
from backtesting.swing_backtest_engine import SwingBacktestEngine, SwingBacktestConfig
from backtesting.strategy_interface import BaseStrategy, TradeSignal, AccountInfo
from backtesting.regime_detector import MarketRegime
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleTestStrategy(BaseStrategy):
    """Simple moving average strategy for testing."""

    def __init__(self, config):
        super().__init__(config)
        self.ma_short = config.get("ma_short", 10)
        self.ma_long = config.get("ma_long", 20)

    def generate_signals(self, data, regime=None):
        """Generate simple MA crossover signals."""
        if len(data) < self.ma_long:
            return []

        # Calculate moving averages
        data["ma_short"] = data["close"].rolling(window=self.ma_short).mean()
        data["ma_long"] = data["close"].rolling(window=self.ma_long).mean()

        signals = []

        # Look for crossovers
        for i in range(1, len(data)):
            current_short = data.iloc[i]["ma_short"]
            current_long = data.iloc[i]["ma_long"]
            prev_short = data.iloc[i - 1]["ma_short"]
            prev_long = data.iloc[i - 1]["ma_long"]

            if pd.notna(current_short) and pd.notna(current_long):
                # Bullish crossover
                if prev_short <= prev_long and current_short > current_long:
                    signal = TradeSignal(
                        pair="EURUSD",
                        direction="BUY",
                        entry_price=data.iloc[i]["close"],
                        stop_loss=data.iloc[i]["close"] * 0.99,  # 1% stop loss
                        take_profit=data.iloc[i]["close"] * 1.02,  # 2% take profit
                        signal_strength=0.7,
                        signal_time=data.iloc[i]["timestamp"],
                        strategy_name=self.strategy_name,
                        regime_context=regime,
                    )
                    signals.append(signal)

                # Bearish crossover
                elif prev_short >= prev_long and current_short < current_long:
                    signal = TradeSignal(
                        pair="EURUSD",
                        direction="SELL",
                        entry_price=data.iloc[i]["close"],
                        stop_loss=data.iloc[i]["close"] * 1.01,  # 1% stop loss
                        take_profit=data.iloc[i]["close"] * 0.98,  # 2% take profit
                        signal_strength=0.7,
                        signal_time=data.iloc[i]["timestamp"],
                        strategy_name=self.strategy_name,
                        regime_context=regime,
                    )
                    signals.append(signal)

        return signals

    def get_regime_parameters(self, regime):
        """Return regime-specific parameters."""
        base_params = {"ma_short": self.ma_short, "ma_long": self.ma_long}

        if regime == MarketRegime.TRENDING_HIGH_VOL:
            return {**base_params, "ma_short": 8, "ma_long": 18}
        elif regime == MarketRegime.RANGING_LOW_VOL:
            return {**base_params, "ma_short": 12, "ma_long": 24}

        return base_params

    def calculate_position_size(self, signal, account_info):
        """Calculate position size based on risk management."""
        risk_amount = account_info.balance * account_info.risk_per_trade
        price_diff = abs(signal.entry_price - signal.stop_loss)

        if price_diff == 0:
            return 0

        position_size = risk_amount / price_diff
        return min(position_size, account_info.max_position_size)

    def validate_signal(self, signal, market_data):
        """Basic signal validation."""
        return True


async def test_swing_backtest_framework():
    """Test the swing backtesting framework."""
    logger.info("🚀 Starting Swing Backtesting Framework Validation")

    try:
        # Initialize engine
        config = SwingBacktestConfig(initial_balance=10000.0, timeframe="4H")
        engine = SwingBacktestEngine(config)
        logger.info("✅ SwingBacktestEngine initialized successfully")

        # Create test strategy
        strategy_config = {"ma_short": 10, "ma_long": 20}
        strategy = SimpleTestStrategy(strategy_config)
        logger.info("✅ Test strategy created successfully")

        # Define test period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # 3 months of data

        logger.info(f"📊 Testing period: {start_date} to {end_date}")

        # Run simple backtest
        logger.info("🔄 Running simple backtest...")
        result = await engine.run_simple_backtest(
            strategy=strategy, pair="EURUSD", start_date=start_date, end_date=end_date
        )

        logger.info("✅ Simple backtest completed successfully")
        logger.info(
            f"📈 Results: {result.total_trades} trades, {result.win_rate:.2%} win rate"
        )

        # Test parameter optimization (simplified)
        logger.info("🔄 Testing parameter optimization...")
        parameter_ranges = {"ma_short": [8, 10, 12], "ma_long": [18, 20, 22]}

        optimization_results = await engine.optimize_strategy_by_regime(
            strategy=strategy,
            pair="EURUSD",
            start_date=start_date,
            end_date=end_date
            - timedelta(days=30),  # Use earlier period for optimization
            parameter_ranges=parameter_ranges,
        )

        logger.info(
            f"✅ Optimization completed for {len(optimization_results)} regimes"
        )

        # Test walk-forward analysis (simplified)
        logger.info("🔄 Testing walk-forward analysis...")
        walk_forward_result = await engine.run_walk_forward_analysis(
            strategy=strategy,
            pair="EURUSD",
            start_date=start_date,
            end_date=end_date,
            parameter_ranges=parameter_ranges,
        )

        logger.info(
            f"✅ Walk-forward analysis completed with {walk_forward_result.total_periods} periods"
        )
        logger.info(f"📊 Combined metrics: {walk_forward_result.combined_metrics}")

        logger.info("🎉 All tests passed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_swing_backtest_framework())
    if success:
        print("\n✅ Swing Backtesting Framework validation completed successfully!")
        print("🚀 Ready for production use with Phase 2 infrastructure")
    else:
        print("\n❌ Validation failed - check logs for details")
        sys.exit(1)
