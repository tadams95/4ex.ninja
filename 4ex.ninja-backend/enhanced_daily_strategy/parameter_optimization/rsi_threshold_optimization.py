#!/usr/bin/env python3
"""
RSI Threshold Optimization for Enhanced Daily Strategy

This module systematically tests different RSI threshold combinations to optimize
the Enhanced Daily Strategy performance, particularly for pairs that need more
signal generation or improved accuracy.

Focus Areas:
- USD_JPY: Fine-tune RSI for consistency (current: RSI 50/50)
- GBP_JPY: Optimize RSI for better entry/exit timing (current: 36.84% win rate)
- EUR_JPY: Relax RSI to generate more signals (current: 1 trade)
- AUD_JPY: Enable signal generation with appropriate RSI thresholds
"""

import pandas as pd
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


class RSIOptimizer:
    """Systematic RSI threshold optimization for Enhanced Daily Strategy."""

    def __init__(self, initial_balance: float = 100000):
        self.initial_balance = initial_balance
        self.base_strategy = EnhancedDailyStrategy(account_balance=initial_balance)

        # RSI parameter ranges for testing
        self.optimization_parameters = {
            "USD_JPY": {
                "rsi_oversold_range": [25, 30, 35],  # Fine-tuning around standard 30
                "rsi_overbought_range": [65, 70, 75],  # Fine-tuning around standard 70
                "rsi_neutral_ranges": [
                    (45, 55),
                    (48, 52),
                    (50, 50),
                ],  # Current vs alternatives
                "priority": "maintain_quality",
                "target_win_rate": 55.0,
            },
            "GBP_JPY": {
                "rsi_oversold_range": [
                    20,
                    25,
                    30,
                    35,
                ],  # More aggressive for more signals
                "rsi_overbought_range": [
                    65,
                    70,
                    75,
                    80,
                ],  # Wider range for better timing
                "rsi_neutral_ranges": [
                    (40, 60),
                    (45, 55),
                    (48, 52),
                ],  # Relaxed vs current
                "priority": "improve_timing",
                "target_win_rate": 45.0,
            },
            "EUR_JPY": {
                "rsi_oversold_range": [
                    15,
                    20,
                    25,
                    30,
                ],  # Very aggressive to generate signals
                "rsi_overbought_range": [
                    70,
                    75,
                    80,
                    85,
                ],  # Wide range for more opportunities
                "rsi_neutral_ranges": [
                    (35, 65),
                    (40, 60),
                    (45, 55),
                ],  # Much wider neutrals
                "priority": "generate_signals",
                "target_win_rate": 40.0,
            },
            "AUD_JPY": {
                "rsi_oversold_range": [10, 15, 20, 25],  # Extremely aggressive
                "rsi_overbought_range": [
                    75,
                    80,
                    85,
                    90,
                ],  # Very wide for signal generation
                "rsi_neutral_ranges": [
                    (30, 70),
                    (35, 65),
                    (40, 60),
                ],  # Very wide neutrals
                "priority": "enable_trading",
                "target_win_rate": 35.0,
            },
        }

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
        self,
        rsi_oversold: int,
        rsi_overbought: int,
        rsi_neutral_low: int = 50,
        rsi_neutral_high: int = 50,
    ) -> EnhancedDailyStrategy:
        """Create a strategy instance with custom RSI parameters."""
        strategy = EnhancedDailyStrategy(account_balance=self.initial_balance)
        strategy.rsi_oversold = rsi_oversold
        strategy.rsi_overbought = rsi_overbought

        # For neutral RSI ranges (used in signal generation logic)
        # We'll need to modify the strategy to use these ranges
        # For now, store them as custom attributes
        strategy.rsi_neutral_low = rsi_neutral_low
        strategy.rsi_neutral_high = rsi_neutral_high

        return strategy

    def simulate_rsi_strategy_performance(
        self,
        pair: str,
        data: pd.DataFrame,
        rsi_oversold: int,
        rsi_overbought: int,
        rsi_neutral_low: int,
        rsi_neutral_high: int,
    ) -> Dict:
        """Simulate strategy performance with custom RSI parameters."""
        try:
            # Create strategy with custom RSI parameters
            strategy = self.create_optimized_strategy(
                rsi_oversold, rsi_overbought, rsi_neutral_low, rsi_neutral_high
            )

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
                current_data = daily_data.iloc[: i + 1].copy()

                try:
                    analysis = strategy.analyze_pair(pair, current_data)

                    if "error" in analysis:
                        continue

                    # Check for trade signal with RSI considerations
                    trade_rec = analysis.get("trade_recommendation", {})
                    signal_data = analysis.get("technical_signal", {})

                    if (
                        trade_rec.get("recommendation")
                        in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]
                        and signal_data.get("signal") != "NONE"
                    ):

                        # Enhanced RSI filtering logic
                        current_rsi = self._calculate_rsi(
                            current_data["close"], period=14
                        )
                        if len(current_rsi) == 0:
                            continue

                        latest_rsi = current_rsi.iloc[-1]
                        direction = signal_data.get("direction", "LONG")

                        # Apply RSI filters based on direction
                        rsi_valid = False
                        if direction == "LONG":
                            # For long trades, prefer RSI not overbought and ideally oversold or neutral
                            rsi_valid = latest_rsi <= rsi_overbought and (
                                latest_rsi <= rsi_oversold
                                or (rsi_neutral_low <= latest_rsi <= rsi_neutral_high)
                            )
                        else:  # SHORT
                            # For short trades, prefer RSI not oversold and ideally overbought or neutral
                            rsi_valid = latest_rsi >= rsi_oversold and (
                                latest_rsi >= rsi_overbought
                                or (rsi_neutral_low <= latest_rsi <= rsi_neutral_high)
                            )

                        if not rsi_valid:
                            continue

                        # Simulate trade execution
                        entry_price = float(current_data["close"].iloc[-1])

                        # Look ahead up to 5 days for outcome (simplified)
                        future_end = min(i + 5, len(daily_data) - 1)
                        if future_end > i:
                            future_data = daily_data.iloc[i + 1 : future_end + 1]

                            # Simple profit calculation based on direction
                            if direction == "LONG":
                                exit_price = future_data["high"].max()
                                profit_pct = (exit_price - entry_price) / entry_price
                            else:
                                exit_price = future_data["low"].min()
                                profit_pct = (entry_price - exit_price) / entry_price

                            # Simple position sizing (1% risk)
                            trade_result = {
                                "entry_date": current_data.index[-1],
                                "entry_price": entry_price,
                                "exit_price": exit_price,
                                "direction": direction,
                                "entry_rsi": latest_rsi,
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
                    "rsi_oversold": rsi_oversold,
                    "rsi_overbought": rsi_overbought,
                    "rsi_neutral_range": f"{rsi_neutral_low}-{rsi_neutral_high}",
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

            # RSI-specific analytics
            avg_entry_rsi = sum(t["entry_rsi"] for t in trades) / len(trades)
            long_trades = [t for t in trades if t["direction"] == "LONG"]
            short_trades = [t for t in trades if t["direction"] == "SHORT"]

            return {
                "rsi_oversold": rsi_oversold,
                "rsi_overbought": rsi_overbought,
                "rsi_neutral_range": f"{rsi_neutral_low}-{rsi_neutral_high}",
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
                "avg_entry_rsi": round(avg_entry_rsi, 1),
                "long_trades": len(long_trades),
                "short_trades": len(short_trades),
                "rsi_analytics": {
                    "oversold_entries": len(
                        [t for t in trades if t["entry_rsi"] <= rsi_oversold]
                    ),
                    "overbought_entries": len(
                        [t for t in trades if t["entry_rsi"] >= rsi_overbought]
                    ),
                    "neutral_entries": len(
                        [
                            t
                            for t in trades
                            if rsi_neutral_low <= t["entry_rsi"] <= rsi_neutral_high
                        ]
                    ),
                },
            }

        except Exception as e:
            return {
                "rsi_oversold": rsi_oversold,
                "rsi_overbought": rsi_overbought,
                "rsi_neutral_range": f"{rsi_neutral_low}-{rsi_neutral_high}",
                "error": str(e),
                "status": "error",
            }

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series(dtype=float)

    def optimize_pair_rsi_parameters(self, pair: str) -> Dict:
        """Optimize RSI parameters for a specific currency pair."""
        logger.info(f"Starting RSI optimization for {pair}")

        # Load historical data
        data = self.load_historical_data(pair)
        if data is None:
            return {"error": f"Failed to load data for {pair}"}

        # Get optimization parameters for this pair
        params = self.optimization_parameters.get(pair, {})
        oversold_range = params.get("rsi_oversold_range", [20, 30])
        overbought_range = params.get("rsi_overbought_range", [70, 80])
        neutral_ranges = params.get("rsi_neutral_ranges", [(45, 55)])
        target_win_rate = params.get("target_win_rate", 40.0)
        priority = params.get("priority", "improve_performance")

        total_combinations = (
            len(oversold_range) * len(overbought_range) * len(neutral_ranges)
        )
        logger.info(f"Testing {total_combinations} RSI combinations for {pair}")

        # Test all combinations
        results = []
        best_result = None
        best_score = -float("inf")

        for oversold, overbought in product(oversold_range, overbought_range):
            if oversold >= overbought:  # Skip invalid combinations
                continue

            for neutral_low, neutral_high in neutral_ranges:
                if neutral_low > neutral_high:
                    continue

                logger.info(
                    f"Testing {pair}: RSI {oversold}/{overbought}, Neutral {neutral_low}-{neutral_high}"
                )

                result = self.simulate_rsi_strategy_performance(
                    pair, data, oversold, overbought, neutral_low, neutral_high
                )

                if "error" not in result and result.get("total_trades", 0) > 0:
                    # Calculate optimization score
                    score = self._calculate_rsi_optimization_score(
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
            "summary": self._generate_rsi_optimization_summary(
                pair, results, best_result
            ),
        }

    def _calculate_rsi_optimization_score(
        self, result: Dict, priority: str, target_win_rate: float
    ) -> float:
        """Calculate optimization score based on pair-specific priorities."""
        win_rate = result.get("win_rate", 0)
        total_trades = result.get("total_trades", 0)
        total_return = result.get("total_return_pct", 0)
        profit_factor = result.get("profit_factor", 0)
        avg_entry_rsi = result.get("avg_entry_rsi", 50)

        # RSI-specific factors
        rsi_analytics = result.get("rsi_analytics", {})
        oversold_entries = rsi_analytics.get("oversold_entries", 0)
        overbought_entries = rsi_analytics.get("overbought_entries", 0)

        if priority == "maintain_quality":  # USD_JPY
            # Prioritize consistent performance with good RSI timing
            rsi_timing_bonus = (
                (oversold_entries + overbought_entries) / max(total_trades, 1) * 20
            )
            score = (
                (win_rate * 0.4)
                + (profit_factor * 15)
                + rsi_timing_bonus
                + (min(total_trades, 50) * 0.3)
            )

        elif priority == "improve_timing":  # GBP_JPY
            # Focus on RSI timing quality for better entries
            rsi_timing_bonus = (
                (oversold_entries + overbought_entries) / max(total_trades, 1) * 30
            )
            win_rate_bonus = max(0, win_rate - target_win_rate) * 2
            score = (
                (win_rate * 0.3)
                + rsi_timing_bonus
                + win_rate_bonus
                + (profit_factor * 10)
            )

        elif priority == "generate_signals":  # EUR_JPY
            # Prioritize trade generation with reasonable RSI logic
            trade_frequency_bonus = min(total_trades, 30) * 2.0
            quality_threshold = 25.0
            quality_penalty = max(0, quality_threshold - win_rate) * -1.5
            score = (
                trade_frequency_bonus
                + (win_rate * 0.2)
                + quality_penalty
                + (profit_factor * 8)
            )

        elif priority == "enable_trading":  # AUD_JPY
            # Heavy focus on any signal generation
            if total_trades == 0:
                score = -100
            else:
                score = (total_trades * 3.0) + (win_rate * 0.15) + (profit_factor * 5)

        else:
            # Default balanced scoring
            score = (
                (win_rate * 0.3)
                + (total_trades * 0.3)
                + (profit_factor * 10)
                + (total_return * 0.2)
            )

        return round(score, 2)

    def _generate_rsi_optimization_summary(
        self, pair: str, results: List[Dict], best_result: Optional[Dict]
    ) -> Dict:
        """Generate summary of RSI optimization results."""
        if not results:
            return {
                "status": "no_valid_results",
                "message": "No valid RSI combinations found",
            }

        if not best_result:
            return {
                "status": "no_improvement",
                "message": "No RSI combination met criteria",
            }

        current_params = {
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "rsi_neutral_range": "50-50",
        }

        summary = {
            "pair": pair,
            "optimization_successful": True,
            "best_rsi_oversold": best_result["rsi_oversold"],
            "best_rsi_overbought": best_result["rsi_overbought"],
            "best_rsi_neutral_range": best_result["rsi_neutral_range"],
            "best_win_rate": best_result["win_rate"],
            "best_total_trades": best_result["total_trades"],
            "best_optimization_score": best_result.get("optimization_score", 0),
            "rsi_timing_analysis": best_result.get("rsi_analytics", {}),
            "recommendation": "",
        }

        # Generate recommendation based on improvement potential
        if best_result["win_rate"] > 40 and best_result["total_trades"] > 10:
            summary["recommendation"] = (
                f"IMPLEMENT: RSI {best_result['rsi_oversold']}/{best_result['rsi_overbought']} with neutral {best_result['rsi_neutral_range']} for {pair}"
            )
        elif best_result["total_trades"] > 20:
            summary["recommendation"] = (
                f"CONSIDER: Test RSI {best_result['rsi_oversold']}/{best_result['rsi_overbought']} for {pair} - high trade frequency"
            )
        elif best_result["win_rate"] > 50:
            summary["recommendation"] = (
                f"EVALUATE: RSI {best_result['rsi_oversold']}/{best_result['rsi_overbought']} for {pair} - high accuracy but low frequency"
            )
        else:
            summary["recommendation"] = (
                f"MAINTAIN: Current RSI parameters may be optimal for {pair}"
            )

        return summary

    def run_comprehensive_rsi_optimization(self) -> Dict:
        """Run RSI optimization for all target currency pairs."""
        logger.info("=== Starting Comprehensive RSI Parameter Optimization ===")

        target_pairs = ["USD_JPY", "GBP_JPY", "EUR_JPY", "AUD_JPY"]
        optimization_results = {}

        for pair in target_pairs:
            logger.info(f"\n--- Optimizing RSI for {pair} ---")
            result = self.optimize_pair_rsi_parameters(pair)
            optimization_results[pair] = result

            # Log summary
            if "error" not in result:
                summary = result.get("summary", {})
                if summary.get("optimization_successful"):
                    best = result["best_parameters"]
                    logger.info(f"✅ {pair} RSI optimization complete:")
                    logger.info(
                        f"   Best RSI: {best['rsi_oversold']}/{best['rsi_overbought']}"
                    )
                    logger.info(f"   Neutral Range: {best['rsi_neutral_range']}")
                    logger.info(f"   Win Rate: {best['win_rate']}%")
                    logger.info(f"   Trades: {best['total_trades']}")
                    logger.info(f"   Recommendation: {summary['recommendation']}")

        return {
            "optimization_date": datetime.now(timezone.utc).isoformat(),
            "strategy": "Enhanced Daily Strategy - RSI Optimization",
            "pairs_optimized": len(target_pairs),
            "detailed_results": optimization_results,
        }

    def save_optimization_results(self, results: Dict) -> str:
        """Save RSI optimization results to file."""
        try:
            output_dir = "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/enhanced_daily_strategy/parameter_optimization/optimization_results"
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rsi_optimization_results_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"RSI optimization results saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving optimization results: {e}")
            return ""


def main():
    """Main execution function for RSI optimization."""
    logger.info("=== Enhanced Daily Strategy RSI Parameter Optimization ===")

    # Initialize optimizer
    optimizer = RSIOptimizer(initial_balance=100000)

    # Run comprehensive optimization
    results = optimizer.run_comprehensive_rsi_optimization()

    # Save results
    output_file = optimizer.save_optimization_results(results)

    if output_file:
        logger.info("\n" + "=" * 80)
        logger.info("RSI OPTIMIZATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        print(f"Detailed results saved to: {output_file}")
        print("=" * 80)
    else:
        logger.error("RSI optimization failed to complete")


if __name__ == "__main__":
    main()
