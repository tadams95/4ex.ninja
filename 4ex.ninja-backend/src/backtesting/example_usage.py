"""
Example usage of the Simplified Backtesting Framework.

This example demonstrates how to use the SwingBacktestEngine for:
1. Simple backtesting
2. Regime-based optimization
3. Walk-forward analysis
"""

from datetime import datetime, timedelta
from swing_backtest_engine import SwingBacktestEngine, SwingBacktestConfig
from strategy_interface import BaseStrategy, TradeSignal, AccountInfo
from regime_detector import MarketRegime
import pandas as pd
import asyncio


class ExampleMACDStrategy(BaseStrategy):
    """Example MACD strategy for demonstration."""

    def __init__(self, config):
        super().__init__(config)
        self.fast_period = config.get("fast_period", 12)
        self.slow_period = config.get("slow_period", 26)
        self.signal_period = config.get("signal_period", 9)

    def generate_signals(self, data, regime=None):
        """Generate MACD-based signals."""
        if len(data) < self.slow_period + self.signal_period:
            return []

        # Calculate MACD
        ema_fast = data["close"].ewm(span=self.fast_period).mean()
        ema_slow = data["close"].ewm(span=self.slow_period).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period).mean()

        signals = []

        # Look for MACD crossovers
        for i in range(1, len(data)):
            current_macd = macd_line.iloc[i]
            current_signal = signal_line.iloc[i]
            prev_macd = macd_line.iloc[i - 1]
            prev_signal = signal_line.iloc[i - 1]

            if pd.notna(current_macd) and pd.notna(current_signal):
                # Bullish crossover
                if prev_macd <= prev_signal and current_macd > current_signal:
                    signals.append(
                        TradeSignal(
                            pair="EURUSD",
                            direction="BUY",
                            entry_price=data.iloc[i]["close"],
                            stop_loss=data.iloc[i]["close"] * 0.985,  # 1.5% stop
                            take_profit=data.iloc[i]["close"] * 1.03,  # 3% target
                            signal_strength=0.8,
                            signal_time=data.iloc[i]["timestamp"],
                            strategy_name=self.strategy_name,
                            regime_context=regime,
                        )
                    )

                # Bearish crossover
                elif prev_macd >= prev_signal and current_macd < current_signal:
                    signals.append(
                        TradeSignal(
                            pair="EURUSD",
                            direction="SELL",
                            entry_price=data.iloc[i]["close"],
                            stop_loss=data.iloc[i]["close"] * 1.015,  # 1.5% stop
                            take_profit=data.iloc[i]["close"] * 0.97,  # 3% target
                            signal_strength=0.8,
                            signal_time=data.iloc[i]["timestamp"],
                            strategy_name=self.strategy_name,
                            regime_context=regime,
                        )
                    )

        return signals

    def get_regime_parameters(self, regime):
        """Adapt parameters based on market regime."""
        base_params = {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "signal_period": self.signal_period,
        }

        # Optimize for different regimes
        if regime == MarketRegime.TRENDING_HIGH_VOL:
            # Faster parameters for volatile trending markets
            return {
                **base_params,
                "fast_period": 8,
                "slow_period": 21,
                "signal_period": 7,
            }
        elif regime == MarketRegime.RANGING_LOW_VOL:
            # Slower parameters for ranging markets
            return {
                **base_params,
                "fast_period": 15,
                "slow_period": 30,
                "signal_period": 12,
            }
        elif regime == MarketRegime.TRENDING_LOW_VOL:
            # Standard parameters for stable trends
            return base_params

        return base_params

    def calculate_position_size(self, signal, account_info):
        """Calculate position size with regime-aware risk management."""
        base_risk = account_info.risk_per_trade

        # Adjust risk based on signal strength and regime
        if signal.regime_context == MarketRegime.TRENDING_HIGH_VOL:
            risk_multiplier = 0.8  # Reduce risk in high volatility
        elif signal.regime_context == MarketRegime.TRENDING_LOW_VOL:
            risk_multiplier = 1.2  # Increase risk in stable trends
        else:
            risk_multiplier = 1.0

        adjusted_risk = base_risk * risk_multiplier * signal.signal_strength
        risk_amount = account_info.balance * adjusted_risk

        price_diff = abs(signal.entry_price - signal.stop_loss)
        if price_diff == 0:
            return 0

        position_size = risk_amount / price_diff
        return min(position_size, account_info.max_position_size)

    def validate_signal(self, signal, market_data):
        """Validate signal against current market conditions."""
        # Basic validation - in production, this could include more checks
        return signal.signal_strength > 0.5


async def main():
    """Demonstrate the Swing Backtesting Framework."""
    print("🚀 Swing Backtesting Framework Example")
    print("=" * 50)

    # 1. Configure the backtesting engine
    config = SwingBacktestConfig(
        initial_balance=50000.0,
        timeframe="4H",
        risk_per_trade=0.015,  # 1.5% risk per trade
        training_window_months=6,
        testing_window_months=2,
        reoptimization_frequency_months=2,
    )

    engine = SwingBacktestEngine(config)
    print("✅ Backtesting engine configured")

    # 2. Create and configure strategy
    strategy_config = {"fast_period": 12, "slow_period": 26, "signal_period": 9}
    strategy = ExampleMACDStrategy(strategy_config)
    print("✅ MACD strategy created")

    # 3. Define backtesting period
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year of data

    print(
        f"📊 Backtesting period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )

    # 4. Run simple backtest
    print("\n🔄 Running simple backtest...")
    try:
        simple_result = await engine.run_simple_backtest(
            strategy=strategy, pair="EURUSD", start_date=start_date, end_date=end_date
        )

        print("✅ Simple backtest completed")
        print(f"📈 Total trades: {simple_result.total_trades}")
        print(f"📈 Win rate: {simple_result.win_rate:.2%}")
        print(f"💰 Final balance: ${simple_result.final_balance:.2f}")

    except Exception as e:
        print(f"❌ Simple backtest failed: {e}")

    # 5. Run regime-based optimization
    print("\n🔄 Running regime-based optimization...")
    try:
        parameter_ranges = {
            "fast_period": [8, 10, 12, 15],
            "slow_period": [21, 24, 26, 30],
            "signal_period": [7, 9, 12],
        }

        optimization_start = start_date
        optimization_end = start_date + timedelta(days=180)  # 6 months for optimization

        optimization_results = await engine.optimize_strategy_by_regime(
            strategy=strategy,
            pair="EURUSD",
            start_date=optimization_start,
            end_date=optimization_end,
            parameter_ranges=parameter_ranges,
        )

        print("✅ Regime optimization completed")
        print(f"📊 Optimized {len(optimization_results)} regimes")

        for regime, result in optimization_results.items():
            print(f"  • {regime.value}: Score {result.validation_score:.3f}")
            print(f"    Best params: {result.best_parameters}")

    except Exception as e:
        print(f"❌ Optimization failed: {e}")

    # 6. Run walk-forward analysis
    print("\n🔄 Running walk-forward analysis...")
    try:
        walk_forward_result = await engine.run_walk_forward_analysis(
            strategy=strategy,
            pair="EURUSD",
            start_date=start_date,
            end_date=end_date,
            parameter_ranges=parameter_ranges,
        )

        print("✅ Walk-forward analysis completed")
        print(f"📊 Total periods tested: {walk_forward_result.total_periods}")
        print(f"📈 Combined metrics:")
        for metric, value in walk_forward_result.combined_metrics.items():
            if isinstance(value, float):
                print(f"  • {metric}: {value:.4f}")
            else:
                print(f"  • {metric}: {value}")

        print(
            f"🎯 Consistency score: {walk_forward_result.combined_metrics.get('consistency_score', 0):.2%}"
        )

    except Exception as e:
        print(f"❌ Walk-forward analysis failed: {e}")

    print("\n🎉 Swing Backtesting Framework example completed!")
    print(
        "💡 This framework integrates with Phase 2 regime detection and monitoring systems"
    )


if __name__ == "__main__":
    asyncio.run(main())
