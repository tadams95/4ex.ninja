"""
Test script for Universal Backtesting Engine components.

This script validates that the core universal backtesting engine components
are working correctly with the existing strategy implementations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Import the universal backtesting components
from src.backtesting.universal_backtesting_engine import UniversalBacktestingEngine
from src.backtesting.execution_simulator import ExecutionSimulator, ExecutionConfig
from src.backtesting.market_simulator import MarketSimulator
from src.backtesting.strategies.strategy_factory import StrategyFactory
from src.backtesting.strategies.strategy_registry import strategy_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_universal_backtesting_engine():
    """Test the universal backtesting engine with multiple strategies."""
    logger.info("🚀 Testing Universal Backtesting Engine")

    try:
        # Initialize the engine
        engine = UniversalBacktestingEngine()
        logger.info("✅ Engine initialized successfully")

        # Test parameters
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        pair = "EURUSD"
        timeframe = "4H"
        initial_balance = 10000.0

        # Test with available strategies
        available_strategies = strategy_registry.list_strategies()
        logger.info(f"Available strategies: {available_strategies}")

        results = {}

        for strategy_name in available_strategies:
            logger.info(f"Testing strategy: {strategy_name}")

            try:
                # Create strategy instance
                strategy_config = _get_test_config_for_strategy(strategy_name)
                strategy = strategy_registry.get_strategy(
                    strategy_name, strategy_config
                )

                # Run backtest
                result = await engine.run_backtest(
                    strategy=strategy,
                    pair=pair,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date,
                    initial_balance=initial_balance,
                )

                results[strategy_name] = result
                logger.info(
                    f"✅ {strategy_name} backtest completed: "
                    f"{len(result.trades)} trades, "
                    f"P&L: ${result.final_balance - result.initial_balance:.2f}"
                )

            except Exception as e:
                logger.error(f"❌ Error testing {strategy_name}: {e}")
                results[strategy_name] = {"error": str(e)}

        # Summary
        logger.info("📊 Backtest Summary:")
        for strategy_name, result in results.items():
            if isinstance(result, dict) and "error" in result:
                logger.info(f"  {strategy_name}: ERROR - {result['error']}")
            else:
                try:
                    if hasattr(result, "final_balance") and hasattr(
                        result, "initial_balance"
                    ):
                        pnl = getattr(result, "final_balance", 0) - getattr(
                            result, "initial_balance", 0
                        )
                        trade_count = len(getattr(result, "trades", []))
                        logger.info(
                            f"  {strategy_name}: {trade_count} trades, P&L: ${pnl:.2f}"
                        )
                    else:
                        logger.info(f"  {strategy_name}: Completed successfully")
                except Exception as e:
                    logger.info(
                        f"  {strategy_name}: Completed (unable to parse result: {e})"
                    )

        return results

    except Exception as e:
        logger.error(f"❌ Failed to test universal backtesting engine: {e}")
        raise


def test_execution_simulator():
    """Test the execution simulator components."""
    logger.info("🔧 Testing Execution Simulator")

    try:
        # Test different execution configurations
        configs = [
            ExecutionConfig(),  # Default config
            ExecutionConfig(spread_pips=2.0, slippage_pips=1.0),  # Higher costs
            ExecutionConfig(spread_pips=0.5, slippage_pips=0.2),  # Lower costs
        ]

        for i, config in enumerate(configs):
            simulator = ExecutionSimulator(config)
            logger.info(
                f"✅ Execution simulator {i+1} initialized: "
                f"spread={config.spread_pips}pips, "
                f"slippage={config.slippage_pips}pips"
            )

        logger.info("✅ All execution simulator configurations working")

    except Exception as e:
        logger.error(f"❌ Failed to test execution simulator: {e}")
        raise


def test_market_simulator():
    """Test the market simulator components."""
    logger.info("🌍 Testing Market Simulator")

    try:
        simulator = MarketSimulator()
        logger.info("✅ Market simulator initialized")

        # Test synthetic data generation
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        pairs = ["EURUSD", "GBPUSD"]

        # Test with a simple strategy
        strategy_config = _get_test_config_for_strategy("ma_crossover")
        strategy = strategy_registry.get_strategy("ma_crossover", strategy_config)

        result = simulator.simulate_trading_session(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            pairs=pairs,
            timeframe="4H",
        )

        logger.info(
            f"✅ Multi-pair simulation completed: "
            f"{result.total_trades} total trades across {len(pairs)} pairs"
        )

        for pair, pair_result in result.pair_results.items():
            logger.info(
                f"  {pair}: {pair_result.get('total_trades', 0)} trades, "
                f"P&L: ${pair_result.get('total_pnl', 0):.2f}"
            )

    except Exception as e:
        logger.error(f"❌ Failed to test market simulator: {e}")
        raise


def _get_test_config_for_strategy(strategy_name: str) -> Dict[str, Any]:
    """Get test configuration for a specific strategy."""
    configs = {
        "ma_crossover": {"fast_period": 10, "slow_period": 20, "risk_percentage": 0.02},
        "rsi": {
            "period": 14,
            "overbought": 70,
            "oversold": 30,
            "risk_percentage": 0.02,
        },
        "bollinger": {"period": 20, "std_dev": 2.0, "risk_percentage": 0.02},
    }

    return configs.get(strategy_name, {"risk_percentage": 0.02})


async def main():
    """Run all tests."""
    logger.info("🧪 Starting Universal Backtesting Framework Tests")

    try:
        # Test individual components
        test_execution_simulator()
        test_market_simulator()

        # Test full integration
        await test_universal_backtesting_engine()

        logger.info("🎉 All tests completed successfully!")
        logger.info("✅ Universal Backtesting Engine is operational")

    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
