#!/usr/bin/env python3
"""
EMA Period Optimization for Enhanced Daily Strategy

This module systematically tests different EMA period combinations to optimize
the Enhanced Daily Strategy performance for each currency pair.

Focus Areas:
- USD_JPY: Fine-tune from excellent 57.69% baseline
- GBP_JPY: Major improvement from 36.84% win rate
- EUR_JPY: Generate more signals (currently 1 trade)
- AUD_JPY: Enable signal generation (currently 0 trades)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
import logging
import os
import sys
import json
from itertools import product

# Add backend directory to path for imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from enhanced_daily_strategy import EnhancedDailyStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EMAOptimizer:
    """Systematic EMA period optimization for Enhanced Daily Strategy."""

    def __init__(self, initial_balance: float = 100000):
        self.initial_balance = initial_balance
        self.base_strategy = EnhancedDailyStrategy(account_balance=initial_balance)

        # EMA parameter ranges for testing
        self.optimization_parameters = {
            "USD_JPY": {
                "ema_fast_range": [15, 18, 20, 22, 25],  # Fine-tuning around current 20
                "ema_slow_range": [45, 48, 50, 52, 55],  # Fine-tuning around current 50
                "priority": "maintain_quality",
                "target_win_rate": 55.0,  # Maintain high performance
            },
            "GBP_JPY": {
                "ema_fast_range": [
                    12,
                    15,
                    18,
                    20,
                    22,
                ],  # More aggressive for more signals
                "ema_slow_range": [
                    35,
                    40,
                    42,
                    45,
                    50,
                ],  # Shorter periods for responsiveness
                "priority": "improve_performance",
                "target_win_rate": 45.0,  # Major improvement target
            },
            "EUR_JPY": {
                "ema_fast_range": [
                    10,
                    12,
                    15,
                    18,
                    20,
                ],  # Aggressive to generate signals
                "ema_slow_range": [30, 35, 40, 45, 50],  # Shorter for more crossovers
                "priority": "generate_signals",
                "target_win_rate": 40.0,  # Modest target while generating volume
            },
            "AUD_JPY": {
                "ema_fast_range": [
                    8,
                    10,
                    12,
                    15,
                    18,
                ],  # Very aggressive to enable trading
                "ema_slow_range": [25, 30, 35, 40, 45],  # Much shorter for sensitivity
                "priority": "enable_trading",
                "target_win_rate": 35.0,  # Conservative target to start trading
            },
        }

        # Store optimization results
        self.optimization_results = {}

    def load_historical_data(self, pair: str) -> Optional[pd.DataFrame]:
        """Load historical H4 data for optimization."""
        try:
            data_file = f"/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/backtest_data/historical_data/{pair}_H4_5Y.json"

            if not os.path.exists(data_file):
                logger.error(f"Historical data file not found: {data_file}")
                return None

            with open(data_file, "r") as f:
                raw_data = json.load(f)

            # Extract the data array from the file structure
            if isinstance(raw_data, dict) and "data" in raw_data:
                data_list = raw_data["data"]
            elif isinstance(raw_data, list):
                data_list = raw_data
            else:
                logger.error(f"Unexpected data format in {data_file}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data_list)

            # Handle both 'time' and 'timestamp' columns
            time_col = "timestamp" if "timestamp" in df.columns else "time"

            # Convert timestamp to datetime
            df[time_col] = pd.to_datetime(df[time_col])
            df.set_index(time_col, inplace=True)
            df.sort_index(inplace=True)

            # Ensure numeric columns
            for col in ["open", "high", "low", "close"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # Remove any rows with NaN values
            df = df.dropna()

            logger.info(f"Loaded {len(df)} H4 candles for {pair}")
            return df

        except Exception as e:
            logger.error(f"Error loading data for {pair}: {e}")
            return None

    def create_optimized_strategy(
        self, ema_fast: int, ema_slow: int
    ) -> EnhancedDailyStrategy:
        """Create a strategy instance with custom EMA parameters."""
        strategy = EnhancedDailyStrategy(account_balance=self.initial_balance)
        strategy.ema_fast = ema_fast
        strategy.ema_slow = ema_slow
        return strategy

    def backtest_ema_combination(
        self, pair: str, data: pd.DataFrame, ema_fast: int, ema_slow: int
    ) -> Dict:
        """Backtest a specific EMA combination for a pair."""
        try:
            # Create strategy with custom EMA parameters
            strategy = self.create_optimized_strategy(ema_fast, ema_slow)

            # Convert H4 data to daily for Enhanced Daily Strategy
            daily_data = (
                data.resample("D")
                .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
                .dropna()
            )

            if len(daily_data) < 60:
                return {"error": "Insufficient daily data after conversion"}

            # Simulate trading through the data
            trades = []
            balance = self.initial_balance

            for i in range(60, len(daily_data)):
                current_data = daily_data.iloc[: i + 1]

                try:
                    analysis = strategy.analyze_pair(pair, current_data)

                    if "error" in analysis:
                        continue

                    # Check for trade signal
                    trade_rec = analysis.get("trade_recommendation", {})
                    if trade_rec.get("recommendation") in [
                        "STRONG_BUY",
                        "STRONG_SELL",
                        "BUY",
                        "SELL",
                    ]:
                        # Simulate trade execution (simplified)
                        signal_data = analysis.get("technical_signal", {})
                        if signal_data.get("signal") != "NONE":
                            # Calculate simple profit/loss simulation
                            entry_price = float(current_data["close"].iloc[-1])
                            direction = signal_data.get("direction", "LONG")

                            # Look ahead up to 5 days for outcome (simplified)
                            future_end = min(i + 5, len(daily_data) - 1)
                            if future_end > i:
                                future_data = daily_data.iloc[i + 1 : future_end + 1]

                                # Simple profit calculation based on direction
                                if direction == "LONG":
                                    exit_price = future_data["high"].max()
                                    profit_pct = (
                                        exit_price - entry_price
                                    ) / entry_price
                                else:
                                    exit_price = future_data["low"].min()
                                    profit_pct = (
                                        entry_price - exit_price
                                    ) / entry_price

                                # Simple position sizing (1% risk)
                                trade_result = {
                                    "entry_date": current_data.index[-1],
                                    "entry_price": entry_price,
                                    "exit_price": exit_price,
                                    "direction": direction,
                                    "profit_pct": profit_pct,
                                    "profit_usd": balance
                                    * 0.01
                                    * profit_pct
                                    * 10,  # 10x leverage simulation
                                    "confidence": trade_rec.get("confidence", 0.5),
                                    "confluence_score": analysis.get(
                                        "confluence_score", 0.0
                                    ),
                                }

                                trades.append(trade_result)
                                balance += trade_result["profit_usd"]

                except Exception as e:
                    continue

            # Calculate performance metrics
            if not trades:
                return {
                    "ema_fast": ema_fast,
                    "ema_slow": ema_slow,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "total_return_pct": 0.0,
                    "profit_factor": 0.0,
                    "avg_confidence": 0.0,
                    "status": "no_trades",
                }

            wins = [t for t in trades if t["profit_usd"] > 0]
            losses = [t for t in trades if t["profit_usd"] <= 0]

            win_rate = len(wins) / len(trades) * 100
            total_return = (balance - self.initial_balance) / self.initial_balance * 100

            profit_factor = 0.0
            if losses:
                total_profit = sum(t["profit_usd"] for t in wins)
                total_loss = abs(sum(t["profit_usd"] for t in losses))
                profit_factor = (
                    total_profit / total_loss if total_loss > 0 else float("inf")
                )

            return {
                "ema_fast": ema_fast,
                "ema_slow": ema_slow,
                "total_trades": len(trades),
                "win_rate": round(win_rate, 2),
                "total_return_pct": round(total_return, 2),
                "profit_factor": round(profit_factor, 2),
                "avg_confidence": round(
                    sum(t["confidence"] for t in trades) / len(trades), 3
                ),
                "avg_confluence": round(
                    sum(t["confluence_score"] for t in trades) / len(trades), 2
                ),
                "trades_sample": trades[-3:] if len(trades) >= 3 else trades,
            }

        except Exception as e:
            return {
                "ema_fast": ema_fast,
                "ema_slow": ema_slow,
                "error": str(e),
                "status": "error",
            }

    def optimize_pair_ema_parameters(self, pair: str) -> Dict:
        """Optimize EMA parameters for a specific currency pair."""
        logger.info(f"Starting EMA optimization for {pair}")

        # Load historical data
        data = self.load_historical_data(pair)
        if data is None:
            return {"error": f"Failed to load data for {pair}"}

        # Get optimization parameters for this pair
        params = self.optimization_parameters.get(pair, {})
        ema_fast_range = params.get("ema_fast_range", [15, 20, 25])
        ema_slow_range = params.get("ema_slow_range", [45, 50, 55])
        target_win_rate = params.get("target_win_rate", 40.0)
        priority = params.get("priority", "improve_performance")

        logger.info(
            f"Testing {len(ema_fast_range) * len(ema_slow_range)} EMA combinations for {pair}"
        )

        # Test all combinations
        results = []
        best_result = None
        best_score = -float("inf")

        for ema_fast, ema_slow in product(ema_fast_range, ema_slow_range):
            if ema_fast >= ema_slow:  # Skip invalid combinations
                continue

            logger.info(f"Testing {pair}: EMA {ema_fast}/{ema_slow}")

            result = self.backtest_ema_combination(pair, data, ema_fast, ema_slow)

            if "error" not in result and result.get("total_trades", 0) > 0:
                # Calculate optimization score based on pair priority
                score = self._calculate_optimization_score(
                    result, priority, target_win_rate
                )
                result["optimization_score"] = score

                if score > best_score:
                    best_score = score
                    best_result = result

                results.append(result)

        # Sort results by optimization score
        results.sort(key=lambda x: x.get("optimization_score", -1), reverse=True)

        return {
            "pair": pair,
            "optimization_priority": priority,
            "target_win_rate": target_win_rate,
            "combinations_tested": len(results),
            "best_parameters": best_result,
            "top_5_results": results[:5],
            "all_results": results,
            "summary": self._generate_optimization_summary(pair, results, best_result),
        }

    def _calculate_optimization_score(
        self, result: Dict, priority: str, target_win_rate: float
    ) -> float:
        """Calculate optimization score based on pair-specific priorities."""
        win_rate = result.get("win_rate", 0)
        total_trades = result.get("total_trades", 0)
        total_return = result.get("total_return_pct", 0)
        profit_factor = result.get("profit_factor", 0)

        if priority == "maintain_quality":  # USD_JPY
            # Prioritize win rate and profit factor for already good performer
            score = (
                (win_rate * 0.4) + (profit_factor * 20) + (min(total_trades, 100) * 0.2)
            )

        elif priority == "improve_performance":  # GBP_JPY
            # Balance win rate improvement with trade frequency
            win_rate_bonus = max(0, win_rate - target_win_rate) * 2
            score = (
                (win_rate * 0.3)
                + (total_trades * 0.3)
                + (profit_factor * 15)
                + win_rate_bonus
            )

        elif priority == "generate_signals":  # EUR_JPY
            # Prioritize trade generation while maintaining reasonable quality
            trade_frequency_bonus = min(total_trades, 50) * 1.5
            quality_threshold = 25.0  # Minimum acceptable win rate
            quality_penalty = max(0, quality_threshold - win_rate) * -2
            score = (
                trade_frequency_bonus
                + (win_rate * 0.2)
                + (profit_factor * 10)
                + quality_penalty
            )

        elif priority == "enable_trading":  # AUD_JPY
            # Heavily prioritize any signal generation with basic quality
            if total_trades == 0:
                score = -100  # Heavy penalty for no trades
            else:
                # Large bonus for generating any trades
                score = (total_trades * 2.0) + (win_rate * 0.15) + (profit_factor * 8)

        else:
            # Default balanced scoring
            score = (
                (win_rate * 0.25)
                + (total_trades * 0.25)
                + (profit_factor * 12.5)
                + (total_return * 0.25)
            )

        return round(score, 2)

    def _generate_optimization_summary(
        self, pair: str, results: List[Dict], best_result: Optional[Dict]
    ) -> Dict:
        """Generate summary of optimization results."""
        if not results:
            return {
                "status": "no_valid_results",
                "message": "No valid parameter combinations found",
            }

        if not best_result:
            return {
                "status": "no_improvement",
                "message": "No parameter combination met criteria",
            }

        current_params = {
            "ema_fast": 20,
            "ema_slow": 50,
        }  # Current Enhanced Daily defaults

        # Find current parameter performance in results
        current_performance = None
        for result in results:
            if result.get("ema_fast") == 20 and result.get("ema_slow") == 50:
                current_performance = result
                break

        summary = {
            "pair": pair,
            "optimization_successful": True,
            "best_ema_fast": best_result["ema_fast"],
            "best_ema_slow": best_result["ema_slow"],
            "best_win_rate": best_result["win_rate"],
            "best_total_trades": best_result["total_trades"],
            "best_optimization_score": best_result.get("optimization_score", 0),
            "improvement_vs_current": {},
            "recommendation": "",
        }

        if current_performance:
            summary["current_performance"] = {
                "win_rate": current_performance["win_rate"],
                "total_trades": current_performance["total_trades"],
                "total_return": current_performance["total_return_pct"],
            }

            # Calculate improvements
            win_rate_improvement = (
                best_result["win_rate"] - current_performance["win_rate"]
            )
            trade_improvement = (
                best_result["total_trades"] - current_performance["total_trades"]
            )

            summary["improvement_vs_current"] = {
                "win_rate_improvement": round(win_rate_improvement, 2),
                "trade_count_improvement": trade_improvement,
                "return_improvement": round(
                    best_result["total_return_pct"]
                    - current_performance["total_return_pct"],
                    2,
                ),
            }

            # Generate recommendation
            if win_rate_improvement > 2.0 or trade_improvement > 5:
                summary["recommendation"] = (
                    f"IMPLEMENT: Switch to EMA {best_result['ema_fast']}/{best_result['ema_slow']} for {pair}"
                )
            elif win_rate_improvement > 0.5:
                summary["recommendation"] = (
                    f"CONSIDER: Test EMA {best_result['ema_fast']}/{best_result['ema_slow']} for {pair} in paper trading"
                )
            else:
                summary["recommendation"] = (
                    f"MAINTAIN: Current EMA 20/50 parameters are optimal for {pair}"
                )
        else:
            summary["recommendation"] = (
                f"IMPLEMENT: Use EMA {best_result['ema_fast']}/{best_result['ema_slow']} for {pair}"
            )

        return summary

    def run_comprehensive_ema_optimization(self) -> Dict:
        """Run EMA optimization for all target currency pairs."""
        logger.info("=== Starting Comprehensive EMA Parameter Optimization ===")

        target_pairs = ["USD_JPY", "GBP_JPY", "EUR_JPY", "AUD_JPY"]
        optimization_results = {}

        for pair in target_pairs:
            logger.info(f"\n--- Optimizing {pair} ---")
            result = self.optimize_pair_ema_parameters(pair)
            optimization_results[pair] = result

            # Log summary
            if "error" not in result:
                summary = result.get("summary", {})
                if summary.get("optimization_successful"):
                    best = result["best_parameters"]
                    logger.info(f"✅ {pair} optimization complete:")
                    logger.info(f"   Best EMA: {best['ema_fast']}/{best['ema_slow']}")
                    logger.info(f"   Win Rate: {best['win_rate']}%")
                    logger.info(f"   Trades: {best['total_trades']}")
                    logger.info(f"   Recommendation: {summary['recommendation']}")
                else:
                    logger.warning(
                        f"❌ {pair} optimization failed: {summary.get('message', 'Unknown error')}"
                    )
            else:
                logger.error(f"❌ {pair} optimization error: {result['error']}")

        # Generate comprehensive summary
        overall_summary = self._generate_overall_optimization_summary(
            optimization_results
        )

        return {
            "optimization_date": datetime.now(timezone.utc).isoformat(),
            "strategy": "Enhanced Daily Strategy - EMA Optimization",
            "pairs_optimized": len(target_pairs),
            "overall_summary": overall_summary,
            "detailed_results": optimization_results,
        }

    def _generate_overall_optimization_summary(self, results: Dict) -> Dict:
        """Generate overall optimization summary across all pairs."""
        successful_optimizations = 0
        recommended_changes = 0

        summary = {
            "pairs_processed": len(results),
            "successful_optimizations": 0,
            "recommended_parameter_changes": 0,
            "implementation_priority": [],
            "next_steps": [],
        }

        for pair, result in results.items():
            if "error" not in result and result.get("summary", {}).get(
                "optimization_successful"
            ):
                successful_optimizations += 1

                recommendation = result["summary"].get("recommendation", "")
                if "IMPLEMENT" in recommendation:
                    recommended_changes += 1
                    best = result["best_parameters"]
                    priority_item = {
                        "pair": pair,
                        "action": "implement_immediately",
                        "current_ema": "20/50",
                        "optimized_ema": f"{best['ema_fast']}/{best['ema_slow']}",
                        "expected_improvement": result["summary"].get(
                            "improvement_vs_current", {}
                        ),
                        "justification": recommendation,
                    }
                    summary["implementation_priority"].append(priority_item)

        summary["successful_optimizations"] = successful_optimizations
        summary["recommended_parameter_changes"] = recommended_changes

        # Generate next steps
        if recommended_changes > 0:
            summary["next_steps"].append(
                "Implement optimized EMA parameters for high-priority pairs"
            )
            summary["next_steps"].append("Run validation backtest with new parameters")
            summary["next_steps"].append("Begin RSI threshold optimization")
        else:
            summary["next_steps"].append(
                "Current EMA parameters are optimal - proceed to RSI optimization"
            )
            summary["next_steps"].append("Consider session timing optimization")

        return summary

    def save_optimization_results(self, results: Dict) -> str:
        """Save EMA optimization results to file."""
        try:
            output_dir = "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/enhanced_daily_strategy/parameter_optimization/optimization_results"
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ema_optimization_results_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"EMA optimization results saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving optimization results: {e}")
            return ""


def main():
    """Main execution function for EMA optimization."""
    logger.info("=== Enhanced Daily Strategy EMA Parameter Optimization ===")

    # Initialize optimizer
    optimizer = EMAOptimizer(initial_balance=100000)

    # Run comprehensive optimization
    results = optimizer.run_comprehensive_ema_optimization()

    # Save results
    output_file = optimizer.save_optimization_results(results)

    if output_file:
        logger.info("\n" + "=" * 80)
        logger.info("EMA OPTIMIZATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        # Print summary
        overall = results["overall_summary"]
        print(f"Pairs Processed: {overall['pairs_processed']}")
        print(f"Successful Optimizations: {overall['successful_optimizations']}")
        print(f"Recommended Changes: {overall['recommended_parameter_changes']}")

        if overall["implementation_priority"]:
            print("\nIMPLEMENTATION PRIORITY:")
            for item in overall["implementation_priority"]:
                print(
                    f"• {item['pair']}: {item['current_ema']} → {item['optimized_ema']}"
                )

        print(f"\nDetailed results saved to: {output_file}")
        print("=" * 80)
    else:
        logger.error("EMA optimization failed to complete")


if __name__ == "__main__":
    main()
