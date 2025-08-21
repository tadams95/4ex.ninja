#!/usr/bin/env python3
"""
Session Timing Optimization for Enhanced Daily Strategy

This module systematically tests different session timing parameters to optimize
the Enhanced Daily Strategy performance, particularly for JPY pairs which are
currently using Asian session filtering.

Focus Areas:
- USD_JPY: Optimize session timing for best performance (currently 57.69% win rate)
- GBP_JPY: Test expanded session windows (improve from 36.84% win rate)
- EUR_JPY: Enable more session opportunities (currently 1 trade)
- AUD_JPY: Broaden session windows to enable trading (currently 0 trades)
"""

import pandas as pd
from datetime import datetime, timezone, time
from typing import Dict, List, Tuple, Optional
import logging
import os
import sys
import json

# Add backend directory to path for imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from enhanced_daily_strategy import EnhancedDailyStrategy
from services.session_manager_service import SessionManagerService

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SessionTimingOptimizer:
    """Systematic session timing optimization for Enhanced Daily Strategy."""

    def __init__(self, initial_balance: float = 100000):
        self.initial_balance = initial_balance
        self.base_strategy = EnhancedDailyStrategy(account_balance=initial_balance)

        # Session timing optimization parameters
        self.session_optimization_parameters = {
            "USD_JPY": {
                "session_windows": [
                    # Current Asian session variants
                    {
                        "name": "Standard_Asian",
                        "start": "23:00",
                        "end": "08:00",
                        "quality": 1.0,
                    },
                    {
                        "name": "Extended_Asian",
                        "start": "22:00",
                        "end": "09:00",
                        "quality": 0.9,
                    },
                    {
                        "name": "Core_Asian",
                        "start": "00:00",
                        "end": "06:00",
                        "quality": 1.1,
                    },
                    # London session overlap
                    {
                        "name": "London_Open",
                        "start": "07:00",
                        "end": "10:00",
                        "quality": 0.8,
                    },
                    # Combined sessions
                    {
                        "name": "Asian_London",
                        "start": "23:00",
                        "end": "10:00",
                        "quality": 0.85,
                    },
                ],
                "priority": "maintain_quality",
                "target_win_rate": 55.0,
            },
            "GBP_JPY": {
                "session_windows": [
                    # Current Asian session
                    {
                        "name": "Standard_Asian",
                        "start": "23:00",
                        "end": "08:00",
                        "quality": 1.0,
                    },
                    # London session (GBP native)
                    {
                        "name": "London_Session",
                        "start": "08:00",
                        "end": "17:00",
                        "quality": 1.2,
                    },
                    {
                        "name": "London_Open",
                        "start": "08:00",
                        "end": "12:00",
                        "quality": 1.3,
                    },
                    # Extended windows
                    {
                        "name": "Extended_London",
                        "start": "07:00",
                        "end": "18:00",
                        "quality": 1.0,
                    },
                    {
                        "name": "Global_Sessions",
                        "start": "22:00",
                        "end": "18:00",
                        "quality": 0.8,
                    },
                ],
                "priority": "improve_performance",
                "target_win_rate": 45.0,
            },
            "EUR_JPY": {
                "session_windows": [
                    # Current restrictive session
                    {
                        "name": "Standard_Asian",
                        "start": "23:00",
                        "end": "08:00",
                        "quality": 1.0,
                    },
                    # European session (EUR native)
                    {
                        "name": "European_Session",
                        "start": "07:00",
                        "end": "16:00",
                        "quality": 1.1,
                    },
                    # Much broader windows to generate signals
                    {
                        "name": "Extended_European",
                        "start": "06:00",
                        "end": "18:00",
                        "quality": 0.9,
                    },
                    {
                        "name": "Multi_Session",
                        "start": "22:00",
                        "end": "18:00",
                        "quality": 0.7,
                    },
                    {
                        "name": "Full_Trading",
                        "start": "00:00",
                        "end": "23:59",
                        "quality": 0.6,
                    },
                ],
                "priority": "generate_signals",
                "target_win_rate": 40.0,
            },
            "AUD_JPY": {
                "session_windows": [
                    # Current restrictive session
                    {
                        "name": "Standard_Asian",
                        "start": "23:00",
                        "end": "08:00",
                        "quality": 1.0,
                    },
                    # Sydney session (AUD native)
                    {
                        "name": "Sydney_Session",
                        "start": "21:00",
                        "end": "06:00",
                        "quality": 1.2,
                    },
                    {
                        "name": "Sydney_Open",
                        "start": "21:00",
                        "end": "02:00",
                        "quality": 1.3,
                    },
                    # Very broad windows to enable any trading
                    {
                        "name": "Extended_Sydney",
                        "start": "20:00",
                        "end": "10:00",
                        "quality": 0.8,
                    },
                    {
                        "name": "All_Sessions",
                        "start": "00:00",
                        "end": "23:59",
                        "quality": 0.5,
                    },
                ],
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

    def is_time_in_session(self, timestamp: pd.Timestamp, session_config: Dict) -> bool:
        """Check if timestamp falls within session window."""
        try:
            start_time = datetime.strptime(session_config["start"], "%H:%M").time()
            end_time = datetime.strptime(session_config["end"], "%H:%M").time()

            current_time = timestamp.time()

            # Handle sessions that cross midnight
            if start_time > end_time:
                return current_time >= start_time or current_time <= end_time
            else:
                return start_time <= current_time <= end_time

        except Exception as e:
            logger.error(f"Error checking session time: {e}")
            return False

    def simulate_session_strategy_performance(
        self, pair: str, data: pd.DataFrame, session_config: Dict
    ) -> Dict:
        """Simulate strategy performance with custom session timing."""
        try:
            # Create strategy instance
            strategy = EnhancedDailyStrategy(account_balance=self.initial_balance)

            # Convert H4 data to daily for Enhanced Daily Strategy
            daily_data = (
                data.resample("D")
                .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
                .dropna()
            )

            if len(daily_data) < 60:
                return {"error": "Insufficient daily data after conversion"}

            # Track session statistics
            total_periods = 0
            session_periods = 0

            # Simulate trading through the data
            trades = []
            balance = self.initial_balance

            for i in range(60, len(daily_data)):
                current_data = daily_data.iloc[: i + 1].copy()
                current_date = current_data.index[-1]

                total_periods += 1

                # Check if current time falls within session window
                # For daily strategy, we check if the day had optimal session activity
                # This is a simplification - in practice, we'd check H4 periods within the day
                session_active = self.is_time_in_session(current_date, session_config)

                if session_active:
                    session_periods += 1

                try:
                    analysis = strategy.analyze_pair(pair, current_data)

                    if "error" in analysis:
                        continue

                    # Apply session filtering - only trade during session windows
                    if not session_active:
                        continue

                    # Check for trade signal
                    trade_rec = analysis.get("trade_recommendation", {})
                    signal_data = analysis.get("technical_signal", {})

                    if (
                        trade_rec.get("recommendation")
                        in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]
                        and signal_data.get("signal") != "NONE"
                    ):

                        # Simulate trade execution with session quality multiplier
                        entry_price = float(current_data["close"].iloc[-1])
                        direction = signal_data.get("direction", "LONG")
                        session_quality = session_config.get("quality", 1.0)

                        # Look ahead up to 5 days for outcome
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

                            # Apply session quality multiplier to profit
                            adjusted_profit_pct = profit_pct * session_quality

                            # Position sizing (1% risk)
                            trade_result = {
                                "entry_date": current_data.index[-1],
                                "entry_price": entry_price,
                                "exit_price": exit_price,
                                "direction": direction,
                                "session_name": session_config["name"],
                                "session_quality": session_quality,
                                "raw_profit_pct": profit_pct,
                                "adjusted_profit_pct": adjusted_profit_pct,
                                "profit_usd": balance
                                * 0.01
                                * adjusted_profit_pct
                                * 10,  # 10x leverage
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
            session_coverage = (
                session_periods / total_periods * 100 if total_periods > 0 else 0
            )

            if not trades:
                return {
                    "session_name": session_config["name"],
                    "session_window": f"{session_config['start']}-{session_config['end']}",
                    "session_quality": session_config["quality"],
                    "session_coverage_pct": round(session_coverage, 1),
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

            # Session-specific analytics
            avg_session_quality = sum(t["session_quality"] for t in trades) / len(
                trades
            )
            session_effectiveness = (
                len(trades) / session_periods * 100 if session_periods > 0 else 0
            )

            return {
                "session_name": session_config["name"],
                "session_window": f"{session_config['start']}-{session_config['end']}",
                "session_quality": session_config["quality"],
                "session_coverage_pct": round(session_coverage, 1),
                "session_effectiveness_pct": round(session_effectiveness, 2),
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
                "avg_session_quality_applied": round(avg_session_quality, 2),
                "session_analytics": {
                    "total_periods_analyzed": total_periods,
                    "session_periods": session_periods,
                    "trades_per_session_period": (
                        round(len(trades) / session_periods, 3)
                        if session_periods > 0
                        else 0
                    ),
                },
            }

        except Exception as e:
            return {
                "session_name": session_config["name"],
                "session_window": f"{session_config['start']}-{session_config['end']}",
                "error": str(e),
                "status": "error",
            }

    def optimize_pair_session_timing(self, pair: str) -> Dict:
        """Optimize session timing for a specific currency pair."""
        logger.info(f"Starting session timing optimization for {pair}")

        # Load historical data
        data = self.load_historical_data(pair)
        if data is None:
            return {"error": f"Failed to load data for {pair}"}

        # Get session parameters for this pair
        params = self.session_optimization_parameters.get(pair, {})
        session_windows = params.get("session_windows", [])
        target_win_rate = params.get("target_win_rate", 40.0)
        priority = params.get("priority", "improve_performance")

        logger.info(f"Testing {len(session_windows)} session configurations for {pair}")

        # Test all session configurations
        results = []
        best_result = None
        best_score = -float("inf")

        for session_config in session_windows:
            session_name = session_config["name"]
            logger.info(
                f"Testing {pair}: {session_name} ({session_config['start']}-{session_config['end']})"
            )

            result = self.simulate_session_strategy_performance(
                pair, data, session_config
            )

            if "error" not in result and result.get("total_trades", 0) > 0:
                # Calculate optimization score
                score = self._calculate_session_optimization_score(
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
            "sessions_tested": len(results),
            "best_session_config": best_result,
            "all_results": results,
            "summary": self._generate_session_optimization_summary(
                pair, results, best_result
            ),
        }

    def _calculate_session_optimization_score(
        self, result: Dict, priority: str, target_win_rate: float
    ) -> float:
        """Calculate optimization score based on pair-specific priorities."""
        win_rate = result.get("win_rate", 0)
        total_trades = result.get("total_trades", 0)
        total_return = result.get("total_return_pct", 0)
        profit_factor = result.get("profit_factor", 0)
        session_coverage = result.get("session_coverage_pct", 0)
        session_effectiveness = result.get("session_effectiveness_pct", 0)

        if priority == "maintain_quality":  # USD_JPY
            # Prioritize win rate and profit factor, balanced with reasonable coverage
            coverage_bonus = min(session_coverage, 50) * 0.2  # Cap coverage bonus
            score = (
                (win_rate * 0.4)
                + (profit_factor * 20)
                + coverage_bonus
                + (min(total_trades, 50) * 0.3)
            )

        elif priority == "improve_performance":  # GBP_JPY
            # Balance performance improvement with session effectiveness
            win_rate_bonus = max(0, win_rate - target_win_rate) * 2
            effectiveness_bonus = (
                min(session_effectiveness, 10) * 3
            )  # Reward efficient trading
            score = (
                (win_rate * 0.3)
                + win_rate_bonus
                + effectiveness_bonus
                + (profit_factor * 15)
            )

        elif priority == "generate_signals":  # EUR_JPY
            # Heavily prioritize trade generation with broad session coverage
            coverage_bonus = min(session_coverage, 80) * 1.5  # Reward broad coverage
            trade_frequency_bonus = min(total_trades, 40) * 2.0
            quality_threshold = 25.0
            quality_penalty = max(0, quality_threshold - win_rate) * -1.5
            score = (
                trade_frequency_bonus
                + coverage_bonus
                + quality_penalty
                + (profit_factor * 8)
            )

        elif priority == "enable_trading":  # AUD_JPY
            # Maximum priority on any signal generation
            if total_trades == 0:
                score = -100
            else:
                # Large bonus for generating any trades, plus coverage
                coverage_bonus = session_coverage * 1.0
                score = (
                    (total_trades * 3.0)
                    + coverage_bonus
                    + (win_rate * 0.15)
                    + (profit_factor * 5)
                )

        else:
            # Default balanced scoring
            score = (
                (win_rate * 0.25)
                + (total_trades * 0.3)
                + (profit_factor * 12)
                + (session_effectiveness * 2)
            )

        return round(score, 2)

    def _generate_session_optimization_summary(
        self, pair: str, results: List[Dict], best_result: Optional[Dict]
    ) -> Dict:
        """Generate summary of session timing optimization results."""
        if not results:
            return {
                "status": "no_valid_results",
                "message": "No valid session configurations found",
            }

        if not best_result:
            return {
                "status": "no_improvement",
                "message": "No session configuration met criteria",
            }

        current_session = "Standard_Asian (23:00-08:00)"  # Current default

        summary = {
            "pair": pair,
            "optimization_successful": True,
            "best_session_name": best_result["session_name"],
            "best_session_window": best_result["session_window"],
            "best_session_quality": best_result["session_quality"],
            "best_win_rate": best_result["win_rate"],
            "best_total_trades": best_result["total_trades"],
            "best_session_coverage": best_result["session_coverage_pct"],
            "best_optimization_score": best_result.get("optimization_score", 0),
            "session_analytics": best_result.get("session_analytics", {}),
            "recommendation": "",
        }

        # Generate recommendation based on improvement
        if best_result["win_rate"] > 45 and best_result["total_trades"] > 15:
            summary["recommendation"] = (
                f"IMPLEMENT: {best_result['session_name']} session ({best_result['session_window']}) for {pair}"
            )
        elif best_result["total_trades"] > 25:
            summary["recommendation"] = (
                f"CONSIDER: {best_result['session_name']} session for {pair} - high trade frequency"
            )
        elif best_result["session_coverage_pct"] > 70 and best_result["win_rate"] > 35:
            summary["recommendation"] = (
                f"EVALUATE: {best_result['session_name']} session for {pair} - broad coverage with decent quality"
            )
        else:
            summary["recommendation"] = (
                f"MAINTAIN: Current Asian session may be optimal for {pair}"
            )

        return summary

    def run_comprehensive_session_optimization(self) -> Dict:
        """Run session timing optimization for all target currency pairs."""
        logger.info("=== Starting Comprehensive Session Timing Optimization ===")

        target_pairs = ["USD_JPY", "GBP_JPY", "EUR_JPY", "AUD_JPY"]
        optimization_results = {}

        for pair in target_pairs:
            logger.info(f"\n--- Optimizing session timing for {pair} ---")
            result = self.optimize_pair_session_timing(pair)
            optimization_results[pair] = result

            # Log summary
            if "error" not in result:
                summary = result.get("summary", {})
                if summary.get("optimization_successful"):
                    best = result["best_session_config"]
                    logger.info(f"✅ {pair} session optimization complete:")
                    logger.info(f"   Best Session: {best['session_name']}")
                    logger.info(f"   Window: {best['session_window']}")
                    logger.info(f"   Win Rate: {best['win_rate']}%")
                    logger.info(f"   Trades: {best['total_trades']}")
                    logger.info(f"   Coverage: {best['session_coverage_pct']}%")
                    logger.info(f"   Recommendation: {summary['recommendation']}")

        return {
            "optimization_date": datetime.now(timezone.utc).isoformat(),
            "strategy": "Enhanced Daily Strategy - Session Timing Optimization",
            "pairs_optimized": len(target_pairs),
            "detailed_results": optimization_results,
        }

    def save_optimization_results(self, results: Dict) -> str:
        """Save session optimization results to file."""
        try:
            output_dir = "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/enhanced_daily_strategy/parameter_optimization/optimization_results"
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_timing_optimization_results_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Session timing optimization results saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving optimization results: {e}")
            return ""


def main():
    """Main execution function for session timing optimization."""
    logger.info("=== Enhanced Daily Strategy Session Timing Optimization ===")

    # Initialize optimizer
    optimizer = SessionTimingOptimizer(initial_balance=100000)

    # Run comprehensive optimization
    results = optimizer.run_comprehensive_session_optimization()

    # Save results
    output_file = optimizer.save_optimization_results(results)

    if output_file:
        logger.info("\n" + "=" * 80)
        logger.info("SESSION TIMING OPTIMIZATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        print(f"Detailed results saved to: {output_file}")
        print("=" * 80)
    else:
        logger.error("Session timing optimization failed to complete")


if __name__ == "__main__":
    main()
