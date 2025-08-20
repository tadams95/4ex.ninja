#!/usr/bin/env python3
"""
Enhanced Daily Strategy Phase 1 Backtest

This backtest properly uses the Enhanced Daily Strategy with all Phase 1 enhancements:
1. Session-Based Trading (JPY pairs during Asian session)
2. Support/Resistance Confluence (key levels detection)
3. Dynamic Position Sizing (signal strength + volatility based)

This is the REAL Phase 1 Enhanced Strategy backtest.
"""

import pandas as pd
import numpy as np
import json
import os
import sys
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

# Add backend directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_daily_strategy import EnhancedDailyStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Phase1EnhancedBacktester:
    """Proper backtesting engine using the real Enhanced Daily Strategy with Phase 1 enhancements."""

    def __init__(self, initial_balance: float = 100000):
        self.initial_balance = initial_balance

        # Initialize the REAL Enhanced Daily Strategy
        self.strategy = EnhancedDailyStrategy(account_balance=initial_balance)

        # Backtest configuration
        self.commission_per_lot = 7.0
        self.spread_pips = {
            "EUR_USD": 1.2,
            "GBP_USD": 1.5,
            "USD_JPY": 1.0,
            "USD_CHF": 1.8,
            "USD_CAD": 1.5,
            "AUD_USD": 1.3,
            "EUR_GBP": 2.0,
            "EUR_JPY": 1.8,
            "GBP_JPY": 2.5,
            "AUD_JPY": 2.0,
        }

        # Results storage
        self.all_trades = []
        self.portfolio_balance = initial_balance

    def load_historical_data(self, pair: str) -> Optional[pd.DataFrame]:
        """Load historical H4 data for backtesting."""
        try:
            data_file = f"/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/backtest_data/historical_data/{pair}_H4_5Y.json"

            if not os.path.exists(data_file):
                logger.warning(f"Data file not found: {data_file}")
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

            df.dropna(inplace=True)
            logger.info(f"Loaded {len(df)} H4 candles for {pair}")
            return df

        except Exception as e:
            logger.error(f"Error loading data for {pair}: {str(e)}")
            return None

    def calculate_pip_value(self, pair: str, lot_size: float = 0.1) -> float:
        """Calculate pip value for position sizing."""
        pip_values = {
            "EUR_USD": 1.0,
            "GBP_USD": 1.0,
            "AUD_USD": 1.0,
            "USD_JPY": 0.909,
            "USD_CHF": 1.0,
            "USD_CAD": 0.769,
            "EUR_GBP": 1.0,
            "EUR_JPY": 0.909,
            "GBP_JPY": 0.909,
            "AUD_JPY": 0.909,
        }
        return pip_values.get(pair, 1.0) * lot_size

    def calculate_pips_distance(self, pair: str, price1: float, price2: float) -> float:
        """Calculate distance in pips between two prices."""
        if "JPY" in pair:
            return abs(price1 - price2) * 100
        else:
            return abs(price1 - price2) * 10000

    def simulate_enhanced_trade(
        self, analysis: Dict, pair: str, entry_date: datetime
    ) -> Optional[Dict]:
        """Simulate a trade using Enhanced Daily Strategy analysis."""

        # Check if we have a valid trade recommendation
        trade_rec = analysis.get("trade_recommendation", {})
        recommendation = trade_rec.get("recommendation", "WAIT")

        # Only trade on strong recommendations from Phase 1 strategy
        if recommendation not in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]:
            return None

        # Get signal data
        signal_data = analysis.get("technical_signal", {})
        if signal_data.get("signal") == "NONE":
            return None

        # Get position sizing from Phase 1 enhancement
        position_sizing = analysis.get("position_sizing")
        if not position_sizing:
            logger.warning(f"No position sizing data for {pair}")
            return None

        # Extract trade parameters
        direction = signal_data.get("direction")
        entry_price = signal_data.get("entry_price")
        stop_loss = signal_data.get("stop_loss")
        take_profit = signal_data.get("take_profit")

        # Get enhanced position size
        lot_size = position_sizing.get("recommended_lot_size", 0.1)
        risk_amount = position_sizing.get("risk_amount_usd", 1000)

        # Apply spread cost
        spread_cost = self.spread_pips.get(pair, 1.5)
        if direction == "LONG":
            entry_price += spread_cost / (100 if "JPY" in pair else 10000)
        else:
            entry_price -= spread_cost / (100 if "JPY" in pair else 10000)

        return {
            "pair": pair,
            "entry_date": entry_date,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "lot_size": lot_size,
            "risk_amount": risk_amount,
            "recommendation": recommendation,
            "confidence": trade_rec.get("confidence", 0.0),
            "signal_strength": analysis.get("signal_strength", "unknown"),
            "confluence_score": analysis.get("confluence_score", 0.0),
            "session_quality": analysis.get("session_analysis", {}).get(
                "session_quality_multiplier", 1.0
            ),
            "phase1_enhancements": analysis.get("phase1_enhancements", {}),
        }

    def execute_trade_simulation(self, trade: Dict, future_data: pd.DataFrame) -> Dict:
        """Simulate trade execution and outcome using future price data."""

        entry_price = trade["entry_price"]
        stop_loss = trade["stop_loss"]
        take_profit = trade["take_profit"]
        direction = trade["direction"]
        lot_size = trade["lot_size"]
        pair = trade["pair"]

        # Track the trade through future price data
        max_favorable = entry_price
        max_adverse = entry_price
        bars_held = 0

        # Look ahead up to 30 days (120 H4 candles) for trade outcome
        max_bars = min(120, len(future_data))

        for i in range(max_bars):
            candle = future_data.iloc[i]
            bars_held += 1

            # Track maximum favorable and adverse movements
            if direction == "LONG":
                max_favorable = max(max_favorable, float(candle["high"]))
                max_adverse = min(max_adverse, float(candle["low"]))

                # Check for stop loss hit
                if float(candle["low"]) <= stop_loss:
                    exit_price = stop_loss
                    outcome = "STOP_LOSS"
                    exit_date = candle.name
                    break

                # Check for take profit hit
                if float(candle["high"]) >= take_profit:
                    exit_price = take_profit
                    outcome = "TAKE_PROFIT"
                    exit_date = candle.name
                    break

            else:  # SHORT
                max_favorable = min(max_favorable, float(candle["low"]))
                max_adverse = max(max_adverse, float(candle["high"]))

                # Check for stop loss hit
                if float(candle["high"]) >= stop_loss:
                    exit_price = stop_loss
                    outcome = "STOP_LOSS"
                    exit_date = candle.name
                    break

                # Check for take profit hit
                if float(candle["low"]) <= take_profit:
                    exit_price = take_profit
                    outcome = "TAKE_PROFIT"
                    exit_date = candle.name
                    break
        else:
            # No SL/TP hit, close at current price
            exit_price = future_data.iloc[-1]["close"]
            outcome = "TIMEOUT"
            exit_date = future_data.iloc[-1].name

        # Calculate profit/loss
        if direction == "LONG":
            profit_pips = self.calculate_pips_distance(pair, exit_price, entry_price)
            if exit_price < entry_price:
                profit_pips = -profit_pips
        else:
            profit_pips = self.calculate_pips_distance(pair, entry_price, exit_price)
            if exit_price > entry_price:
                profit_pips = -profit_pips

        # Calculate USD profit/loss
        pip_value = self.calculate_pip_value(pair, lot_size)
        profit_usd = profit_pips * pip_value

        # Subtract commission
        profit_usd -= self.commission_per_lot * lot_size

        return {
            **trade,
            "exit_date": exit_date,
            "exit_price": exit_price,
            "outcome": outcome,
            "bars_held": bars_held,
            "profit_pips": round(profit_pips, 1),
            "profit_usd": round(profit_usd, 2),
            "max_favorable": max_favorable,
            "max_adverse": max_adverse,
            "pip_value": pip_value,
        }

    def backtest_pair_phase1(self, pair: str) -> Dict:
        """Run Phase 1 Enhanced Strategy backtest for a single pair."""
        logger.info(f"Starting Phase 1 Enhanced backtest for {pair}")

        # Load historical data
        data = self.load_historical_data(pair)
        if data is None:
            return {"error": f"Could not load data for {pair}"}

        # Resample to daily data for analysis (Enhanced Daily Strategy works on daily timeframe)
        daily_data = (
            data.resample("D")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
            .dropna()
        )

        logger.info(f"Analyzing {len(daily_data)} daily candles for {pair}")

        trades = []
        pair_balance = self.initial_balance

        # Walk through daily data, starting after we have enough for indicators
        for i in range(60, len(daily_data)):
            analysis_date = daily_data.index[i]

            # Get H4 data slice for analysis (past 400 H4 candles = ~100 days)
            try:
                # Find the closest H4 timestamp to our analysis date
                h4_mask = data.index <= analysis_date
                h4_data_up_to_date = data.loc[h4_mask]

                # Take the last 400 H4 candles for analysis
                analysis_data = h4_data_up_to_date.iloc[-400:].copy()

                # Ensure we have enough data
                if len(analysis_data) < 100:
                    continue
            except Exception:
                continue

            # Run Enhanced Daily Strategy analysis with H4 data
            try:
                analysis = self.strategy.analyze_pair(pair, analysis_data)

                if "error" in analysis:
                    continue

                # Check if we have a trade signal from Phase 1 strategy
                trade = self.simulate_enhanced_trade(analysis, pair, analysis_date)
                if trade is None:
                    continue

                # Get future data for trade simulation (next 30 days of H4 data)
                future_start_idx = data.index.get_indexer(
                    [analysis_date], method="nearest"
                )[0]
                if future_start_idx < len(data) - 120:
                    future_data = data.iloc[
                        future_start_idx + 1 : future_start_idx + 121
                    ]

                    # Execute trade simulation
                    trade_result = self.execute_trade_simulation(trade, future_data)
                    trades.append(trade_result)

                    # Update balance
                    pair_balance += trade_result["profit_usd"]

                    logger.info(
                        f"{pair} - {str(analysis_date)}: {trade_result['recommendation']} "
                        f"-> {trade_result['outcome']} "
                        f"({trade_result['profit_pips']:.1f} pips, ${trade_result['profit_usd']:.2f})"
                    )

            except Exception as e:
                logger.error(f"Error analyzing {pair} on {analysis_date}: {str(e)}")
                continue

        # Calculate performance metrics
        if not trades:
            return {"pair": pair, "error": "No trades generated", "trades": 0}

        wins = [t for t in trades if t["profit_usd"] > 0]
        losses = [t for t in trades if t["profit_usd"] <= 0]

        # Phase 1 enhancement statistics
        session_filtered_trades = [
            t
            for t in trades
            if t["phase1_enhancements"].get("session_filter_active", False)
        ]
        confluence_trades = [
            t
            for t in trades
            if t["phase1_enhancements"].get("confluence_detected", False)
        ]
        dynamic_sized_trades = [
            t
            for t in trades
            if t["phase1_enhancements"].get("dynamic_sizing_applied", False)
        ]

        metrics = {
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / len(trades) * 100, 2) if trades else 0,
            "total_return_usd": round(pair_balance - self.initial_balance, 2),
            "total_return_pct": round(
                (pair_balance - self.initial_balance) / self.initial_balance * 100, 2
            ),
            "avg_win_usd": (
                round(sum(t["profit_usd"] for t in wins) / len(wins), 2) if wins else 0
            ),
            "avg_loss_usd": (
                round(sum(t["profit_usd"] for t in losses) / len(losses), 2)
                if losses
                else 0
            ),
            "avg_win_pips": (
                round(sum(t["profit_pips"] for t in wins) / len(wins), 1) if wins else 0
            ),
            "avg_loss_pips": (
                round(sum(t["profit_pips"] for t in losses) / len(losses), 1)
                if losses
                else 0
            ),
            "total_pips": round(sum(t["profit_pips"] for t in trades), 1),
            "profit_factor": (
                round(
                    sum(t["profit_usd"] for t in wins)
                    / abs(sum(t["profit_usd"] for t in losses)),
                    2,
                )
                if losses
                else float("inf")
            ),
            # Phase 1 Enhancement Metrics
            "phase1_metrics": {
                "session_filtered_trades": len(session_filtered_trades),
                "confluence_trades": len(confluence_trades),
                "dynamic_sized_trades": len(dynamic_sized_trades),
                "session_filter_percentage": round(
                    len(session_filtered_trades) / len(trades) * 100, 1
                ),
                "confluence_percentage": round(
                    len(confluence_trades) / len(trades) * 100, 1
                ),
                "dynamic_sizing_percentage": round(
                    len(dynamic_sized_trades) / len(trades) * 100, 1
                ),
                "avg_confidence": round(
                    sum(t["confidence"] for t in trades) / len(trades), 3
                ),
                "avg_confluence_score": round(
                    sum(t["confluence_score"] for t in trades) / len(trades), 2
                ),
                "avg_session_quality": round(
                    sum(t["session_quality"] for t in trades) / len(trades), 2
                ),
            },
        }

        return {
            "pair": pair,
            "backtest_period": f"{str(daily_data.index[0])} to {str(daily_data.index[-1])}",
            "metrics": metrics,
            "trades": trades[-10:],  # Last 10 trades for review
            "total_trades_count": len(trades),
        }

    def run_comprehensive_phase1_backtest(self) -> Dict:
        """Run comprehensive Phase 1 Enhanced Strategy backtest."""
        logger.info("=== Starting Phase 1 Enhanced Daily Strategy Backtest ===")

        # Target currency pairs (focus on proven performers)
        test_pairs = ["USD_JPY", "EUR_USD", "GBP_USD", "EUR_JPY", "AUD_JPY", "GBP_JPY"]

        results = {}
        overall_stats = {
            "total_trades": 0,
            "total_wins": 0,
            "total_return_usd": 0,
            "best_pair": None,
            "worst_pair": None,
            "best_return": -float("inf"),
            "worst_return": float("inf"),
            "phase1_impact": {
                "total_session_filtered": 0,
                "total_confluence_trades": 0,
                "total_dynamic_sized": 0,
            },
        }

        for pair in test_pairs:
            try:
                result = self.backtest_pair_phase1(pair)
                results[pair] = result

                if "error" not in result and "metrics" in result:
                    metrics = result["metrics"]

                    # Update overall statistics
                    overall_stats["total_trades"] += metrics["total_trades"]
                    overall_stats["total_wins"] += metrics["wins"]
                    overall_stats["total_return_usd"] += metrics["total_return_usd"]

                    # Track best/worst performers
                    return_pct = metrics["total_return_pct"]
                    if return_pct > overall_stats["best_return"]:
                        overall_stats["best_return"] = return_pct
                        overall_stats["best_pair"] = pair
                    if return_pct < overall_stats["worst_return"]:
                        overall_stats["worst_return"] = return_pct
                        overall_stats["worst_pair"] = pair

                    # Phase 1 enhancement impact
                    phase1 = metrics.get("phase1_metrics", {})
                    overall_stats["phase1_impact"][
                        "total_session_filtered"
                    ] += phase1.get("session_filtered_trades", 0)
                    overall_stats["phase1_impact"][
                        "total_confluence_trades"
                    ] += phase1.get("confluence_trades", 0)
                    overall_stats["phase1_impact"]["total_dynamic_sized"] += phase1.get(
                        "dynamic_sized_trades", 0
                    )

            except Exception as e:
                logger.error(f"Error backtesting {pair}: {str(e)}")
                results[pair] = {"error": str(e)}

        # Calculate final overall metrics
        if overall_stats["total_trades"] > 0:
            overall_stats["overall_win_rate"] = round(
                overall_stats["total_wins"] / overall_stats["total_trades"] * 100, 2
            )
            overall_stats["overall_return_pct"] = round(
                overall_stats["total_return_usd"]
                / (self.initial_balance * len(test_pairs))
                * 100,
                2,
            )

            # Phase 1 enhancement percentages
            phase1_impact = overall_stats["phase1_impact"]
            phase1_impact["session_filter_impact"] = round(
                phase1_impact["total_session_filtered"]
                / overall_stats["total_trades"]
                * 100,
                1,
            )
            phase1_impact["confluence_impact"] = round(
                phase1_impact["total_confluence_trades"]
                / overall_stats["total_trades"]
                * 100,
                1,
            )
            phase1_impact["dynamic_sizing_impact"] = round(
                phase1_impact["total_dynamic_sized"]
                / overall_stats["total_trades"]
                * 100,
                1,
            )

        return {
            "backtest_summary": {
                "strategy": "Enhanced Daily Strategy (Phase 1)",
                "backtest_date": datetime.now(timezone.utc).isoformat(),
                "pairs_tested": len(test_pairs),
                "initial_balance_per_pair": self.initial_balance,
                "enhancements_tested": [
                    "Session-Based Trading (JPY pairs during Asian session)",
                    "Support/Resistance Confluence Detection",
                    "Dynamic Position Sizing (0.5% to 3% risk scaling)",
                ],
                "overall_statistics": overall_stats,
            },
            "pair_results": results,
            "phase1_summary": self._generate_phase1_impact_summary(results),
        }

    def _generate_phase1_impact_summary(self, results: Dict) -> Dict:
        """Generate detailed Phase 1 impact analysis."""
        all_trades = []
        for pair_result in results.values():
            if "trades" in pair_result and isinstance(pair_result["trades"], list):
                all_trades.extend(pair_result["trades"])

        if not all_trades:
            return {"error": "No trades to analyze"}

        # Analyze Phase 1 enhancement impact
        session_trades = [
            t
            for t in all_trades
            if t.get("phase1_enhancements", {}).get("session_filter_active", False)
        ]
        confluence_trades = [
            t
            for t in all_trades
            if t.get("phase1_enhancements", {}).get("confluence_detected", False)
        ]
        dynamic_trades = [
            t
            for t in all_trades
            if t.get("phase1_enhancements", {}).get("dynamic_sizing_applied", False)
        ]

        # Calculate enhancement-specific performance
        def calc_performance(trade_list):
            if not trade_list:
                return {"trades": 0, "win_rate": 0, "avg_profit": 0}
            wins = [t for t in trade_list if t["profit_usd"] > 0]
            return {
                "trades": len(trade_list),
                "win_rate": round(len(wins) / len(trade_list) * 100, 1),
                "avg_profit": round(
                    sum(t["profit_usd"] for t in trade_list) / len(trade_list), 2
                ),
                "total_profit": round(sum(t["profit_usd"] for t in trade_list), 2),
            }

        return {
            "total_trades_analyzed": len(all_trades),
            "session_based_trading": calc_performance(session_trades),
            "confluence_detection": calc_performance(confluence_trades),
            "dynamic_position_sizing": calc_performance(dynamic_trades),
            "enhancement_adoption_rates": {
                "session_filtering": round(
                    len(session_trades) / len(all_trades) * 100, 1
                ),
                "confluence_detection": round(
                    len(confluence_trades) / len(all_trades) * 100, 1
                ),
                "dynamic_sizing": round(len(dynamic_trades) / len(all_trades) * 100, 1),
            },
        }

    def save_phase1_results(self, results: Dict) -> str:
        """Save Phase 1 Enhanced Strategy backtest results."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save JSON results
            json_filename = f"enhanced_daily_phase1_backtest_{timestamp}.json"
            json_path = f"/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-frontend/public/data/strategy/{json_filename}"

            with open(json_path, "w") as f:
                json.dump(results, f, indent=2, default=str)

            # Save markdown report
            md_filename = f"enhanced_daily_phase1_report_{timestamp}.md"
            md_path = f"/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-frontend/public/data/strategy/{md_filename}"

            self._create_phase1_report(results, md_path)

            logger.info(f"Phase 1 backtest results saved:")
            logger.info(f"JSON: {json_path}")
            logger.info(f"Report: {md_path}")

            return json_path

        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return None

    def _create_phase1_report(self, results: Dict, filepath: str):
        """Create comprehensive Phase 1 enhancement report."""
        with open(filepath, "w") as f:
            f.write("# Enhanced Daily Strategy - Phase 1 Backtest Report\n\n")

            summary = results["backtest_summary"]
            overall = summary["overall_statistics"]

            f.write(f"**Strategy:** {summary['strategy']}\n")
            f.write(f"**Backtest Date:** {summary['backtest_date']}\n")
            f.write(f"**Pairs Tested:** {summary['pairs_tested']}\n")
            f.write(
                f"**Initial Balance:** ${summary['initial_balance_per_pair']:,} per pair\n\n"
            )

            f.write("## Phase 1 Enhancements Tested\n\n")
            for enhancement in summary["enhancements_tested"]:
                f.write(f"- {enhancement}\n")
            f.write("\n")

            f.write("## Overall Performance\n\n")
            f.write(f"- **Total Trades:** {overall['total_trades']}\n")
            f.write(
                f"- **Overall Win Rate:** {overall.get('overall_win_rate', 'N/A')}%\n"
            )
            f.write(f"- **Total Return:** ${overall['total_return_usd']:,.2f}\n")
            f.write(
                f"- **Overall Return %:** {overall.get('overall_return_pct', 'N/A')}%\n"
            )
            f.write(
                f"- **Best Performer:** {overall['best_pair']} ({overall['best_return']:.2f}%)\n"
            )
            f.write(
                f"- **Worst Performer:** {overall['worst_pair']} ({overall['worst_return']:.2f}%)\n\n"
            )

            f.write("## Phase 1 Enhancement Impact\n\n")
            if "phase1_impact" in overall:
                impact = overall["phase1_impact"]
                f.write(
                    f"- **Session-Filtered Trades:** {impact['total_session_filtered']} ({impact.get('session_filter_impact', 0)}%)\n"
                )
                f.write(
                    f"- **Confluence Trades:** {impact['total_confluence_trades']} ({impact.get('confluence_impact', 0)}%)\n"
                )
                f.write(
                    f"- **Dynamic-Sized Trades:** {impact['total_dynamic_sized']} ({impact.get('dynamic_sizing_impact', 0)}%)\n\n"
                )

            f.write("## Individual Pair Performance\n\n")
            f.write(
                "| Pair | Trades | Win Rate | Return (%) | Return ($) | Session Filter | Confluence | Dynamic Sizing |\n"
            )
            f.write(
                "|------|--------|----------|------------|------------|----------------|------------|----------------|\n"
            )

            for pair, result in results["pair_results"].items():
                if "metrics" in result:
                    m = result["metrics"]
                    p1 = m.get("phase1_metrics", {})
                    f.write(
                        f"| {pair} | {m['total_trades']} | {m['win_rate']}% | {m['total_return_pct']:.2f}% | ${m['total_return_usd']:,.2f} | {p1.get('session_filter_percentage', 0):.1f}% | {p1.get('confluence_percentage', 0):.1f}% | {p1.get('dynamic_sizing_percentage', 0):.1f}% |\n"
                    )
                else:
                    f.write(f"| {pair} | ERROR | - | - | - | - | - | - |\n")

            f.write("\n## Phase 1 Enhancement Analysis\n\n")
            if "phase1_summary" in results:
                summary = results["phase1_summary"]
                if "error" not in summary:
                    f.write(
                        f"**Total Trades Analyzed:** {summary['total_trades_analyzed']}\n\n"
                    )

                    f.write("### Session-Based Trading Impact\n")
                    session = summary["session_based_trading"]
                    f.write(f"- Trades: {session['trades']}\n")
                    f.write(f"- Win Rate: {session['win_rate']}%\n")
                    f.write(f"- Average Profit: ${session['avg_profit']}\n")
                    f.write(f"- Total Profit: ${session['total_profit']}\n\n")

                    f.write("### Confluence Detection Impact\n")
                    confluence = summary["confluence_detection"]
                    f.write(f"- Trades: {confluence['trades']}\n")
                    f.write(f"- Win Rate: {confluence['win_rate']}%\n")
                    f.write(f"- Average Profit: ${confluence['avg_profit']}\n")
                    f.write(f"- Total Profit: ${confluence['total_profit']}\n\n")

                    f.write("### Dynamic Position Sizing Impact\n")
                    dynamic = summary["dynamic_position_sizing"]
                    f.write(f"- Trades: {dynamic['trades']}\n")
                    f.write(f"- Win Rate: {dynamic['win_rate']}%\n")
                    f.write(f"- Average Profit: ${dynamic['avg_profit']}\n")
                    f.write(f"- Total Profit: ${dynamic['total_profit']}\n\n")

            f.write("## Conclusion\n\n")
            f.write(
                "This backtest represents the TRUE Enhanced Daily Strategy with all Phase 1 enhancements:\n"
            )
            f.write(
                "1. **Session-Based Trading** - JPY pairs only trade during optimal Asian session\n"
            )
            f.write(
                "2. **Support/Resistance Confluence** - Multi-factor level detection and scoring\n"
            )
            f.write(
                "3. **Dynamic Position Sizing** - Risk scaling from 0.5% to 3% based on signal strength\n\n"
            )
            f.write(
                "These results demonstrate the actual performance of the sophisticated Phase 1 Enhanced Strategy,\n"
            )
            f.write("not the basic EMA crossover strategy tested previously.\n")


def main():
    """Main execution function."""
    logger.info("=== Phase 1 Enhanced Daily Strategy Backtest ===")

    # Initialize Phase 1 backtester
    backtester = Phase1EnhancedBacktester(initial_balance=100000)

    # Run comprehensive Phase 1 backtest
    results = backtester.run_comprehensive_phase1_backtest()

    # Save results
    output_file = backtester.save_phase1_results(results)

    if output_file:
        logger.info("Phase 1 backtest completed successfully!")

        # Print summary
        overall = results["backtest_summary"]["overall_statistics"]
        print("\n" + "=" * 70)
        print("PHASE 1 ENHANCED DAILY STRATEGY BACKTEST SUMMARY")
        print("=" * 70)
        print(f"Total Trades: {overall['total_trades']}")
        print(f"Overall Win Rate: {overall.get('overall_win_rate', 'N/A')}%")
        print(f"Total Return: ${overall['total_return_usd']:,.2f}")
        print(f"Overall Return %: {overall.get('overall_return_pct', 'N/A')}%")
        print(f"Best Pair: {overall['best_pair']} ({overall['best_return']:.2f}%)")
        print(f"Worst Pair: {overall['worst_pair']} ({overall['worst_return']:.2f}%)")

        if "phase1_impact" in overall:
            impact = overall["phase1_impact"]
            print("\nPhase 1 Enhancement Impact:")
            print(
                f"Session Filtering: {impact.get('session_filter_impact', 0)}% of trades"
            )
            print(
                f"Confluence Detection: {impact.get('confluence_impact', 0)}% of trades"
            )
            print(
                f"Dynamic Sizing: {impact.get('dynamic_sizing_impact', 0)}% of trades"
            )

        print("=" * 70)
        print(
            "This represents the REAL Enhanced Daily Strategy with Phase 1 enhancements!"
        )
        print("=" * 70)
    else:
        logger.error("Phase 1 backtest failed to complete")


if __name__ == "__main__":
    main()
