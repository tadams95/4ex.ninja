"""
Emergency Backtesting Framework

This module provides rapid backtesting capabilities to validate current production
parameters against recent historical data. It's designed to identify performance
gaps after infrastructure optimizations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from api.oanda_api import OandaAPI
from config.settings import MONGO_CONNECTION_STRING
from pymongo import MongoClient

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class EmergencyBacktester:
    """
    Emergency backtesting engine for rapid validation of current production parameters.
    """

    def __init__(self):
        self.oanda_client = OandaAPI()
        self.mongo_client = MongoClient(
            MONGO_CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True
        )
        self.db = self.mongo_client["streamed_prices"]
        self.logger = logging.getLogger(__name__)

        # Results storage
        self.results_dir = Path(__file__).parent / "reports"
        self.results_dir.mkdir(exist_ok=True)

    def validate_current_parameters(self, pair: str, timeframe: str) -> Dict:
        """
        Run 3-month rolling backtest with current production parameters.

        Args:
            pair: Currency pair (e.g., 'EUR_USD')
            timeframe: Timeframe (e.g., 'H4', 'D')

        Returns:
            Dict containing performance metrics and validation results
        """
        try:
            self.logger.info(f"Starting validation for {pair} {timeframe}")

            # Load current production parameters
            params = self.load_production_parameters(pair, timeframe)
            if not params:
                return {"error": f"No parameters found for {pair} {timeframe}"}

            # Fetch 3 months of historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            data = self.fetch_historical_data(pair, timeframe, start_date, end_date)

            if data is None or data.empty:
                return {"error": f"No historical data available for {pair} {timeframe}"}

            # Run backtest with current parameters
            trades = self.run_backtest(data, params)

            # Generate performance metrics
            metrics = self.calculate_performance_metrics(trades)

            # Add metadata
            metrics.update(
                {
                    "pair": pair,
                    "timeframe": timeframe,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "parameters": params,
                    "data_points": len(data),
                    "validation_timestamp": datetime.now().isoformat(),
                }
            )

            # Save results
            self.save_validation_results(pair, timeframe, metrics)

            self.logger.info(f"Validation completed for {pair} {timeframe}")
            return metrics

        except Exception as e:
            self.logger.error(f"Validation failed for {pair} {timeframe}: {str(e)}")
            return {"error": str(e)}

    def load_production_parameters(self, pair: str, timeframe: str) -> Optional[Dict]:
        """
        Load current production parameters from strategy files.

        Args:
            pair: Currency pair
            timeframe: Timeframe

        Returns:
            Dictionary of strategy parameters or None if not found
        """
        try:
            # Construct strategy filename based on naming convention
            strategy_filename = f"MA_{pair}_{timeframe}_strat.py"
            strategy_path = project_root / "src" / "strategies" / strategy_filename

            if not strategy_path.exists():
                self.logger.warning(f"Strategy file not found: {strategy_path}")
                return None

            # Read and parse strategy file to extract parameters
            with open(strategy_path, "r") as f:
                content = f.read()

            # Extract parameters from __init__ method
            params = self._parse_strategy_parameters(content)

            self.logger.info(f"Loaded parameters for {pair} {timeframe}: {params}")
            return params

        except Exception as e:
            self.logger.error(
                f"Failed to load parameters for {pair} {timeframe}: {str(e)}"
            )
            return None

    def _parse_strategy_parameters(self, content: str) -> Dict:
        """
        Parse strategy parameters from Python file content.

        Args:
            content: Python file content as string

        Returns:
            Dictionary of extracted parameters
        """
        import re

        params = {}

        # Extract parameters from __init__ method - more flexible pattern
        init_pattern = r"def __init__\(.*?\):(.*?)(?=def\s+\w+|class\s+\w+|\Z)"
        init_match = re.search(init_pattern, content, re.DOTALL)

        if init_match:
            init_content = init_match.group(1)

            # Extract parameter assignments with more flexible patterns
            param_patterns = {
                "slow_ma": r"slow_ma[:\s]*int\s*=\s*(\d+)",
                "fast_ma": r"fast_ma[:\s]*int\s*=\s*(\d+)",
                "atr_period": r"atr_period[:\s]*int\s*=\s*(\d+)",
                "sl_atr_multiplier": r"sl_atr_multiplier[:\s]*float\s*=\s*([\d.]+)",
                "tp_atr_multiplier": r"tp_atr_multiplier[:\s]*float\s*=\s*([\d.]+)",
                "min_atr_value": r"min_atr_value[:\s]*float\s*=\s*([\d.]+)",
                "min_rr_ratio": r"min_rr_ratio[:\s]*float\s*=\s*([\d.]+)",
            }

            for param_name, pattern in param_patterns.items():
                match = re.search(pattern, init_content)
                if match:
                    value = match.group(1)
                    params[param_name] = float(value) if "." in value else int(value)

        # If the above didn't work, try a different approach
        if not params:
            # Look for parameter lines directly
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if "=" in line and any(
                    param in line
                    for param in [
                        "slow_ma",
                        "fast_ma",
                        "atr_period",
                        "sl_atr_multiplier",
                        "tp_atr_multiplier",
                        "min_atr_value",
                        "min_rr_ratio",
                    ]
                ):
                    # Try to extract parameter from line like "slow_ma: int = 140,"
                    param_match = re.search(r"(\w+):\s*\w+\s*=\s*([\d.]+)", line)
                    if param_match:
                        param_name = param_match.group(1)
                        value = param_match.group(2)
                        params[param_name] = (
                            float(value) if "." in value else int(value)
                        )

        return params

    def fetch_historical_data(
        self, pair: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLC data for backtesting.

        Args:
            pair: Currency pair
            timeframe: Timeframe
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with OHLC data or None if failed
        """
        try:
            # Try to fetch from MongoDB first
            collection_name = f"{pair}_{timeframe}"
            collection = self.db[collection_name]

            # Query data within date range
            query = {"time": {"$gte": start_date, "$lte": end_date}}

            cursor = collection.find(query).sort("time", 1)
            data = list(cursor)

            if not data:
                self.logger.warning(f"No data found in MongoDB for {pair} {timeframe}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Ensure required columns exist
            required_columns = ["time", "o", "h", "l", "c"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                self.logger.error(f"Missing required columns: {missing_columns}")
                return None

            # Rename columns to standard format
            df = df.rename(
                columns={
                    "time": "timestamp",
                    "o": "open",
                    "h": "high",
                    "l": "low",
                    "c": "close",
                }
            )

            # Convert timestamp to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
                df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Sort by timestamp
            df = df.sort_values("timestamp").reset_index(drop=True)

            self.logger.info(f"Fetched {len(df)} data points for {pair} {timeframe}")
            return df

        except Exception as e:
            self.logger.error(
                f"Failed to fetch historical data for {pair} {timeframe}: {str(e)}"
            )
            return None

    def run_backtest(self, data: pd.DataFrame, params: Dict) -> List[Dict]:
        """
        Run backtest with moving average strategy.

        Args:
            data: Historical OHLC data
            params: Strategy parameters

        Returns:
            List of trade dictionaries
        """
        try:
            trades = []

            # Calculate moving averages
            slow_ma = params.get("slow_ma", 140)
            fast_ma = params.get("fast_ma", 40)
            atr_period = params.get("atr_period", 14)

            data["slow_ma"] = data["close"].rolling(window=slow_ma).mean()
            data["fast_ma"] = data["close"].rolling(window=fast_ma).mean()

            # Calculate ATR
            data["tr"] = np.maximum(
                data["high"] - data["low"],
                np.maximum(
                    abs(data["high"] - data["close"].shift(1)),
                    abs(data["low"] - data["close"].shift(1)),
                ),
            )
            data["atr"] = data["tr"].rolling(window=atr_period).mean()

            # Generate signals
            data["signal"] = 0
            data.loc[data["fast_ma"] > data["slow_ma"], "signal"] = 1  # Buy signal
            data.loc[data["fast_ma"] < data["slow_ma"], "signal"] = -1  # Sell signal

            # Find crossovers
            data["signal_change"] = data["signal"].diff()

            # Process trades
            in_trade = False
            current_trade = None

            sl_multiplier = params.get("sl_atr_multiplier", 1.5)
            tp_multiplier = params.get("tp_atr_multiplier", 2.0)
            min_atr = params.get("min_atr_value", 0.0003)

            for i in range(1, len(data)):
                row = data.iloc[i]

                # Check for signal change
                if (
                    abs(row["signal_change"]) == 2
                ):  # Signal changed from -1 to 1 or 1 to -1
                    # Close existing trade if any
                    if in_trade and current_trade:
                        current_trade["exit_price"] = row["close"]
                        current_trade["exit_time"] = row["timestamp"]
                        current_trade["exit_reason"] = "signal_change"

                        # Calculate trade result
                        if current_trade["direction"] == "BUY":
                            pips = (
                                current_trade["exit_price"]
                                - current_trade["entry_price"]
                            ) * 10000
                        else:
                            pips = (
                                current_trade["entry_price"]
                                - current_trade["exit_price"]
                            ) * 10000

                        current_trade["pips"] = pips
                        trades.append(current_trade)

                    # Check if new signal is valid
                    if row["atr"] >= min_atr:
                        # Start new trade
                        current_trade = {
                            "entry_time": row["timestamp"],
                            "entry_price": row["close"],
                            "direction": "BUY" if row["signal"] == 1 else "SELL",
                            "atr_at_entry": row["atr"],
                            "sl_price": (
                                row["close"] - (row["atr"] * sl_multiplier)
                                if row["signal"] == 1
                                else row["close"] + (row["atr"] * sl_multiplier)
                            ),
                            "tp_price": (
                                row["close"] + (row["atr"] * tp_multiplier)
                                if row["signal"] == 1
                                else row["close"] - (row["atr"] * tp_multiplier)
                            ),
                        }
                        in_trade = True

                # Check for SL/TP hits if in trade
                elif in_trade and current_trade:
                    hit_sl = False
                    hit_tp = False

                    if current_trade["direction"] == "BUY":
                        hit_sl = row["low"] <= current_trade["sl_price"]
                        hit_tp = row["high"] >= current_trade["tp_price"]
                    else:
                        hit_sl = row["high"] >= current_trade["sl_price"]
                        hit_tp = row["low"] <= current_trade["tp_price"]

                    if hit_sl or hit_tp:
                        current_trade["exit_time"] = row["timestamp"]
                        current_trade["exit_reason"] = (
                            "stop_loss" if hit_sl else "take_profit"
                        )
                        current_trade["exit_price"] = (
                            current_trade["sl_price"]
                            if hit_sl
                            else current_trade["tp_price"]
                        )

                        # Calculate trade result
                        if current_trade["direction"] == "BUY":
                            pips = (
                                current_trade["exit_price"]
                                - current_trade["entry_price"]
                            ) * 10000
                        else:
                            pips = (
                                current_trade["entry_price"]
                                - current_trade["exit_price"]
                            ) * 10000

                        current_trade["pips"] = pips
                        trades.append(current_trade)

                        in_trade = False
                        current_trade = None

            self.logger.info(f"Generated {len(trades)} trades from backtest")
            return trades

        except Exception as e:
            self.logger.error(f"Backtest failed: {str(e)}")
            return []

    def calculate_performance_metrics(self, trades: List[Dict]) -> Dict:
        """
        Calculate comprehensive performance metrics.

        Args:
            trades: List of trade dictionaries

        Returns:
            Dictionary of performance metrics
        """
        if not trades:
            return {
                "error": "No trades generated",
                "total_trades": 0,
                "total_pips": 0,
                "win_rate": 0,
                "average_win_pips": 0,
                "average_loss_pips": 0,
                "profit_factor": 0,
                "max_drawdown": 0,
                "sharpe_ratio": 0,
            }

        # Basic metrics
        total_pips = sum(trade.get("pips", 0) for trade in trades)
        winning_trades = [t for t in trades if t.get("pips", 0) > 0]
        losing_trades = [t for t in trades if t.get("pips", 0) < 0]

        win_rate = len(winning_trades) / len(trades) if trades else 0
        avg_win = np.mean([t["pips"] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t["pips"] for t in losing_trades]) if losing_trades else 0

        # Profit factor
        total_wins = sum(t["pips"] for t in winning_trades) if winning_trades else 0
        total_losses = (
            abs(sum(t["pips"] for t in losing_trades)) if losing_trades else 0
        )
        profit_factor = (
            total_wins / total_losses
            if total_losses > 0
            else float("inf") if total_wins > 0 else 0
        )

        # Calculate max drawdown and Sharpe ratio
        max_drawdown = self.calculate_max_drawdown(trades)
        sharpe_ratio = self.calculate_sharpe_ratio(trades)

        return {
            "total_trades": len(trades),
            "total_pips": round(total_pips, 2),
            "win_rate": round(win_rate, 4),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "average_win_pips": round(avg_win, 2),
            "average_loss_pips": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "best_trade_pips": max([t.get("pips", 0) for t in trades]),
            "worst_trade_pips": min([t.get("pips", 0) for t in trades]),
            "average_trade_pips": round(total_pips / len(trades), 2),
        }

    def calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown from trade list."""
        if not trades:
            return 0.0

        # Calculate running balance
        running_balance = 0
        peak_balance = 0
        max_drawdown = 0

        for trade in trades:
            running_balance += trade.get("pips", 0)
            peak_balance = max(peak_balance, running_balance)
            drawdown = peak_balance - running_balance
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def calculate_sharpe_ratio(self, trades: List[Dict]) -> float:
        """Calculate Sharpe ratio from trade list."""
        if not trades:
            return 0.0

        returns = [trade.get("pips", 0) for trade in trades]

        if len(returns) < 2:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)

        if std_return == 0:
            return 0.0

        # Annualize (assuming trades are roughly monthly for simplicity)
        sharpe = (mean_return * 12) / (std_return * np.sqrt(12))

        return sharpe

    def save_validation_results(self, pair: str, timeframe: str, metrics: Dict) -> None:
        """
        Save validation results to JSON file.

        Args:
            pair: Currency pair
            timeframe: Timeframe
            metrics: Performance metrics dictionary
        """
        try:
            filename = f"validation_{pair}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.results_dir / filename

            with open(filepath, "w") as f:
                json.dump(metrics, f, indent=2, default=str)

            self.logger.info(f"Validation results saved to {filepath}")

        except Exception as e:
            self.logger.error(f"Failed to save validation results: {str(e)}")

    def validate_all_strategies(self) -> Dict:
        """
        Run validation for all available strategies.

        Returns:
            Dictionary with results for all strategies
        """
        results = {}

        # Get all strategy files
        strategies_dir = project_root / "src" / "strategies"
        strategy_files = [f for f in strategies_dir.glob("MA_*_strat.py")]

        for strategy_file in strategy_files:
            # Parse filename to get pair and timeframe
            filename = strategy_file.stem
            parts = filename.split("_")

            if len(parts) >= 4:
                pair = f"{parts[1]}_{parts[2]}"
                timeframe = parts[3]

                self.logger.info(f"Validating {pair} {timeframe}")
                result = self.validate_current_parameters(pair, timeframe)
                results[f"{pair}_{timeframe}"] = result

        return results


def main():
    """Main function for running emergency validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Emergency Backtesting Validation")
    parser.add_argument("--pair", help="Currency pair (e.g., EUR_USD)")
    parser.add_argument("--timeframe", help="Timeframe (e.g., H4, D)")
    parser.add_argument("--all", action="store_true", help="Validate all strategies")

    args = parser.parse_args()

    backtester = EmergencyBacktester()

    if args.all:
        print("Running validation for all strategies...")
        results = backtester.validate_all_strategies()

        print("\n=== VALIDATION SUMMARY ===")
        for strategy, result in results.items():
            if "error" in result:
                print(f"{strategy}: ERROR - {result['error']}")
            else:
                print(
                    f"{strategy}: {result['total_trades']} trades, "
                    f"{result['total_pips']:.1f} pips, "
                    f"{result['win_rate']:.1%} win rate"
                )

    elif args.pair and args.timeframe:
        print(f"Running validation for {args.pair} {args.timeframe}...")
        result = backtester.validate_current_parameters(args.pair, args.timeframe)

        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print("\n=== VALIDATION RESULTS ===")
            print(f"Total Trades: {result['total_trades']}")
            print(f"Total Pips: {result['total_pips']:.2f}")
            print(f"Win Rate: {result['win_rate']:.1%}")
            print(f"Average Win: {result['average_win_pips']:.2f} pips")
            print(f"Average Loss: {result['average_loss_pips']:.2f} pips")
            print(f"Profit Factor: {result['profit_factor']:.2f}")
            print(f"Max Drawdown: {result['max_drawdown']:.2f} pips")
            print(f"Sharpe Ratio: {result['sharpe_ratio']:.4f}")

    else:
        print("Please specify --pair and --timeframe, or use --all flag")


if __name__ == "__main__":
    main()
