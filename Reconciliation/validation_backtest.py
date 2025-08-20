#!/usr/bin/env python3
"""
MA_Unified_Strat Validation Backtest
====================================

Purpose: Validate if current live strategy configuration can replicate
documented backtest performance results.

Target Results to Match:
- EUR_USD: 18.0% return, 1.40 Sharpe, 8.0% drawdown
- GBP_USD: 19.8% return, 1.54 Sharpe, 7.3% drawdown
- USD_JPY: 17.1% return, 1.33 Sharpe, 8.4% drawdown

Date: August 19, 2025
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, List

# ==========================================
# CONFIGURATION FROM LIVE STRATEGY
# ==========================================

# Current strat_settings.py parameters
STRATEGY_CONFIGS = {
    "EUR_USD_D": {
        "slow_ma": 20,
        "fast_ma": 10,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,
        "timeframe": "D",
    },
    "GBP_USD_D": {
        "slow_ma": 80,
        "fast_ma": 10,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,
        "timeframe": "D",
    },
    "USD_JPY_D": {
        "slow_ma": 20,
        "fast_ma": 10,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,
        "timeframe": "D",
    },
    # Additional pairs for comprehensive testing
    "AUD_USD_D": {
        "slow_ma": 20,
        "fast_ma": 10,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,
        "timeframe": "D",
    },
    "GBP_JPY_D": {
        "slow_ma": 80,
        "fast_ma": 10,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,
        "timeframe": "D",
    },
    "USD_CAD_D": {
        "slow_ma": 80,
        "fast_ma": 10,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.25,
        "timeframe": "D",
    },
}

# Documented performance targets
DOCUMENTED_TARGETS = {
    "EUR_USD": {"return": 18.0, "sharpe": 1.40, "drawdown": 8.0},
    "GBP_USD": {"return": 19.8, "sharpe": 1.54, "drawdown": 7.3},
    "USD_JPY": {"return": 17.1, "sharpe": 1.33, "drawdown": 8.4},
}

# ==========================================
# DATA LOADING
# ==========================================


def load_historical_data(pair: str, timeframe: str = "D") -> pd.DataFrame:
    """Load historical data from CSV files"""
    base_path = Path(
        "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/backtest_results/historical_data"
    )
    filename = f"{pair}_{timeframe}_20230101_20241231.csv"
    file_path = base_path / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Historical data not found: {file_path}")

    # Load CSV with standard OHLC columns
    df = pd.read_csv(file_path)

    # Standardize column names (handle different possible formats)
    column_mapping = {
        "timestamp": "timestamp",
        "time": "timestamp",
        "date": "timestamp",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }

    # Rename columns to standardized format
    df.columns = df.columns.str.lower()
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})

    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()

    return df


# ==========================================
# TECHNICAL INDICATORS
# ==========================================


def calculate_moving_averages(
    df: pd.DataFrame, fast_period: int, slow_period: int
) -> pd.DataFrame:
    """Calculate fast and slow moving averages"""
    df = df.copy()
    df["fast_ma"] = df["close"].rolling(window=fast_period).mean()
    df["slow_ma"] = df["close"].rolling(window=slow_period).mean()
    return df


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate Average True Range"""
    df = df.copy()
    df["prev_close"] = df["close"].shift(1)
    df["tr1"] = df["high"] - df["low"]
    df["tr2"] = abs(df["high"] - df["prev_close"])
    df["tr3"] = abs(df["low"] - df["prev_close"])
    df["true_range"] = df[["tr1", "tr2", "tr3"]].max(axis=1)
    df["atr"] = df["true_range"].rolling(window=period).mean()
    return df


# ==========================================
# SIGNAL GENERATION
# ==========================================


def generate_ma_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Generate MA crossover signals following MA_Unified_Strat logic"""
    df = df.copy()

    # Signal generation: 1 for long, -1 for short, 0 for no signal
    df["ma_signal"] = 0

    # Long signal: fast MA crosses above slow MA
    df.loc[
        (df["fast_ma"] > df["slow_ma"])
        & (df["fast_ma"].shift(1) <= df["slow_ma"].shift(1)),
        "ma_signal",
    ] = 1

    # Short signal: fast MA crosses below slow MA
    df.loc[
        (df["fast_ma"] < df["slow_ma"])
        & (df["fast_ma"].shift(1) >= df["slow_ma"].shift(1)),
        "ma_signal",
    ] = -1

    return df


# ==========================================
# TRADE EXECUTION & RISK MANAGEMENT
# ==========================================


def execute_trades(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """Execute trades with stop loss and take profit"""
    df = df.copy()

    # Initialize trade tracking columns
    df["position"] = 0  # Current position: 1 long, -1 short, 0 none
    df["entry_price"] = np.nan
    df["stop_loss"] = np.nan
    df["take_profit"] = np.nan
    df["trade_pnl"] = 0.0
    df["cumulative_pnl"] = 0.0

    current_position = 0
    entry_price = None
    stop_loss = None
    take_profit = None
    cumulative_pnl = 0.0

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i - 1]

        # Check for signal
        signal = row["ma_signal"]
        current_price = row["close"]
        current_atr = row["atr"]

        # Exit existing position if stop loss or take profit hit
        if current_position != 0 and entry_price is not None:
            pnl = 0
            exit_triggered = False

            if current_position == 1:  # Long position
                if current_price <= stop_loss or current_price >= take_profit:
                    pnl = current_price - entry_price
                    exit_triggered = True
            elif current_position == -1:  # Short position
                if current_price >= stop_loss or current_price <= take_profit:
                    pnl = entry_price - current_price
                    exit_triggered = True

            if exit_triggered:
                df.iloc[i, df.columns.get_loc("trade_pnl")] = pnl
                cumulative_pnl += pnl
                current_position = 0
                entry_price = None
                stop_loss = None
                take_profit = None

        # Enter new position on signal
        if signal != 0 and current_position == 0 and not pd.isna(current_atr):
            current_position = signal
            entry_price = current_price

            if signal == 1:  # Long position
                stop_loss = entry_price - (config["sl_atr_multiplier"] * current_atr)
                take_profit = entry_price + (config["tp_atr_multiplier"] * current_atr)
            else:  # Short position
                stop_loss = entry_price + (config["sl_atr_multiplier"] * current_atr)
                take_profit = entry_price - (config["tp_atr_multiplier"] * current_atr)

        # Update dataframe
        df.iloc[i, df.columns.get_loc("position")] = current_position
        df.iloc[i, df.columns.get_loc("entry_price")] = entry_price
        df.iloc[i, df.columns.get_loc("stop_loss")] = stop_loss
        df.iloc[i, df.columns.get_loc("take_profit")] = take_profit
        df.iloc[i, df.columns.get_loc("cumulative_pnl")] = cumulative_pnl

    return df


# ==========================================
# PERFORMANCE METRICS
# ==========================================


def calculate_performance_metrics(df: pd.DataFrame) -> Dict:
    """Calculate key performance metrics"""

    # Filter out trades with PnL
    trades = df[df["trade_pnl"] != 0]["trade_pnl"]

    if len(trades) == 0:
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
        }

    # Basic metrics
    total_return = trades.sum()
    total_trades = len(trades)
    winning_trades = trades[trades > 0]
    losing_trades = trades[trades < 0]

    win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
    avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0

    # Annualized return (assuming daily data)
    days_in_backtest = len(df)
    years = days_in_backtest / 365.25
    annualized_return = (total_return / years) if years > 0 else 0

    # Sharpe ratio (simplified - using daily returns)
    if len(trades) > 1:
        daily_returns = trades
        sharpe_ratio = (
            daily_returns.mean() / daily_returns.std() * np.sqrt(252)
            if daily_returns.std() > 0
            else 0
        )
    else:
        sharpe_ratio = 0

    # Maximum drawdown
    cumulative_pnl = df["cumulative_pnl"]
    running_max = cumulative_pnl.cummax()
    drawdown = cumulative_pnl - running_max
    max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0

    return {
        "total_return": round(total_return, 4),
        "annualized_return": round(annualized_return, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "max_drawdown": round(max_drawdown, 4),
        "total_trades": total_trades,
        "win_rate": round(win_rate, 1),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
    }


# ==========================================
# MAIN BACKTEST FUNCTION
# ==========================================


def run_strategy_backtest(pair: str, config: Dict) -> Dict:
    """Run complete backtest for a single pair"""

    print(f"\n🔄 Running backtest for {pair}...")

    try:
        # Load historical data
        df = load_historical_data(pair, config["timeframe"])
        print(
            f"   📊 Loaded {len(df)} data points from {df.index[0]} to {df.index[-1]}"
        )

        # Calculate technical indicators
        df = calculate_moving_averages(df, config["fast_ma"], config["slow_ma"])
        df = calculate_atr(df, period=14)

        # Generate signals
        df = generate_ma_signals(df)

        # Execute trades
        df = execute_trades(df, config)

        # Calculate performance
        performance = calculate_performance_metrics(df)

        print(
            f"   ✅ Backtest complete: {performance['total_trades']} trades, "
            f"{performance['annualized_return']}% return"
        )

        return {
            "pair": pair,
            "config": config,
            "performance": performance,
            "dataframe": df,  # Include for detailed analysis
        }

    except Exception as e:
        print(f"   ❌ Error running backtest for {pair}: {str(e)}")
        return {"pair": pair, "config": config, "error": str(e), "performance": None}


# ==========================================
# VALIDATION COMPARISON
# ==========================================


def compare_with_documented_results(results: List[Dict]) -> Dict:
    """Compare backtest results with documented performance targets"""

    comparison = {}

    for result in results:
        if result["performance"] is None:
            continue

        pair = result["pair"]
        performance = result["performance"]

        # Extract pair name for comparison (remove timeframe suffix)
        pair_name = pair.replace("_D", "").replace("_H4", "")

        if pair_name in DOCUMENTED_TARGETS:
            target = DOCUMENTED_TARGETS[pair_name]

            comparison[pair_name] = {
                "actual": {
                    "return": performance["annualized_return"],
                    "sharpe": performance["sharpe_ratio"],
                    "drawdown": performance["max_drawdown"],
                    "trades": performance["total_trades"],
                    "win_rate": performance["win_rate"],
                },
                "documented": target,
                "variance": {
                    "return_diff": performance["annualized_return"] - target["return"],
                    "sharpe_diff": performance["sharpe_ratio"] - target["sharpe"],
                    "drawdown_diff": performance["max_drawdown"] - target["drawdown"],
                },
            }

    return comparison


# ==========================================
# RESULTS REPORTING
# ==========================================


def generate_validation_report(results: List[Dict], comparison: Dict) -> str:
    """Generate comprehensive validation report"""

    report = []
    report.append("# 🧪 MA_UNIFIED_STRAT VALIDATION RESULTS")
    report.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Test Period:** 2023-01-01 to 2024-12-31")
    report.append("")

    # Executive Summary
    report.append("## 📊 EXECUTIVE SUMMARY")
    report.append("")

    total_tests = len([r for r in results if r["performance"] is not None])
    successful_tests = len(
        [
            r
            for r in results
            if r["performance"] is not None and r["performance"]["total_trades"] > 0
        ]
    )

    report.append(f"- **Total Pairs Tested:** {total_tests}")
    report.append(f"- **Successful Backtests:** {successful_tests}")
    report.append(f"- **Target Pairs Comparison:** {len(comparison)}")
    report.append("")

    # Performance Comparison
    report.append("## 🎯 PERFORMANCE COMPARISON WITH DOCUMENTED RESULTS")
    report.append("")

    if comparison:
        report.append("| Pair | Metric | Actual | Documented | Variance | Status |")
        report.append("|------|--------|--------|------------|----------|--------|")

        for pair, data in comparison.items():
            actual = data["actual"]
            documented = data["documented"]
            variance = data["variance"]

            # Return comparison
            return_status = (
                "✅"
                if abs(variance["return_diff"]) < 5
                else "⚠️" if abs(variance["return_diff"]) < 10 else "❌"
            )
            report.append(
                f"| {pair} | Return | {actual['return']:.1f}% | {documented['return']:.1f}% | {variance['return_diff']:+.1f}% | {return_status} |"
            )

            # Sharpe comparison
            sharpe_status = (
                "✅"
                if abs(variance["sharpe_diff"]) < 0.3
                else "⚠️" if abs(variance["sharpe_diff"]) < 0.5 else "❌"
            )
            report.append(
                f"| {pair} | Sharpe | {actual['sharpe']:.2f} | {documented['sharpe']:.2f} | {variance['sharpe_diff']:+.2f} | {sharpe_status} |"
            )

            # Drawdown comparison
            dd_status = (
                "✅"
                if abs(variance["drawdown_diff"]) < 3
                else "⚠️" if abs(variance["drawdown_diff"]) < 5 else "❌"
            )
            report.append(
                f"| {pair} | Drawdown | {actual['drawdown']:.1f}% | {documented['drawdown']:.1f}% | {variance['drawdown_diff']:+.1f}% | {dd_status} |"
            )

            report.append(f"| {pair} | Trades | {actual['trades']} | - | - | - |")
            report.append(
                f"| {pair} | Win Rate | {actual['win_rate']:.1f}% | - | - | - |"
            )
            report.append("")

    # Detailed Results
    report.append("## 📈 DETAILED BACKTEST RESULTS")
    report.append("")

    for result in results:
        if result["performance"] is None:
            continue

        pair = result["pair"]
        perf = result["performance"]
        config = result["config"]

        report.append(f"### {pair}")
        report.append(
            f"**Configuration:** Fast MA: {config['fast_ma']}, Slow MA: {config['slow_ma']}, "
            f"SL ATR: {config['sl_atr_multiplier']}, TP ATR: {config['tp_atr_multiplier']}"
        )
        report.append("")
        report.append(f"- **Total Return:** {perf['annualized_return']:.2f}%")
        report.append(f"- **Sharpe Ratio:** {perf['sharpe_ratio']:.2f}")
        report.append(f"- **Max Drawdown:** {perf['max_drawdown']:.2f}%")
        report.append(f"- **Total Trades:** {perf['total_trades']}")
        report.append(f"- **Win Rate:** {perf['win_rate']:.1f}%")
        report.append(f"- **Avg Win:** {perf['avg_win']:.4f}")
        report.append(f"- **Avg Loss:** {perf['avg_loss']:.4f}")
        report.append("")

    # Conclusions
    report.append("## 🔍 ANALYSIS & CONCLUSIONS")
    report.append("")

    if comparison:
        high_variance_pairs = []
        for pair, data in comparison.items():
            if abs(data["variance"]["return_diff"]) > 10:
                high_variance_pairs.append(pair)

        if high_variance_pairs:
            report.append(
                f"⚠️ **High Variance Detected:** {', '.join(high_variance_pairs)}"
            )
            report.append(
                "- Current strategy configuration may not match documented optimal parameters"
            )
            report.append(
                "- Recommend proceeding to Phase 2: Strategy Configuration Alignment"
            )
        else:
            report.append(
                "✅ **Strategy Alignment Confirmed:** Current configuration produces similar results"
            )
            report.append("- Live strategy parameters are well-optimized")
            report.append("- Proceed to Phase 3: Frontend Data Pipeline Reconciliation")

    report.append("")
    report.append("## 🎯 NEXT STEPS")
    report.append("")
    report.append(
        "1. **If High Variance:** Extract optimal parameters from documented results"
    )
    report.append("2. **If Aligned:** Continue with frontend data reconciliation")
    report.append("3. **If Issues:** Investigate backtesting methodology differences")

    return "\n".join(report)


# ==========================================
# MAIN EXECUTION
# ==========================================


def main():
    """Run MA_Unified_Strat validation backtest"""

    print("🚀 Starting MA_Unified_Strat Validation Backtest")
    print("=" * 60)

    # Run backtests for all configured strategies
    results = []

    for strategy_name, config in STRATEGY_CONFIGS.items():
        pair = strategy_name.replace("_D", "").replace("_H4", "")
        result = run_strategy_backtest(pair, config)
        results.append(result)

    # Compare with documented results
    print("\n📊 Comparing with documented performance targets...")
    comparison = compare_with_documented_results(results)

    # Generate report
    print("\n📝 Generating validation report...")
    report = generate_validation_report(results, comparison)

    # Save results
    output_dir = Path("/Users/tyrelle/Desktop/4ex.ninja/Reconciliation")

    # Save detailed results as JSON
    results_data = {
        "timestamp": datetime.now().isoformat(),
        "results": [
            {
                "pair": r["pair"],
                "config": r["config"],
                "performance": r["performance"],
                "error": r.get("error"),
            }
            for r in results
        ],
        "comparison": comparison,
    }

    with open(output_dir / "validation_backtest_results.json", "w") as f:
        json.dump(results_data, f, indent=2)

    # Save report as markdown
    with open(output_dir / "Validation_Backtest_Report.md", "w") as f:
        f.write(report)

    print(f"\n✅ Validation backtest complete!")
    print(f"📁 Results saved to: {output_dir}")
    print("\n" + "=" * 60)
    print("SUMMARY:")
    for pair, data in comparison.items():
        variance = data["variance"]["return_diff"]
        status = (
            "✅ ALIGNED"
            if abs(variance) < 5
            else "⚠️ VARIANCE" if abs(variance) < 10 else "❌ HIGH VARIANCE"
        )
        print(
            f"{pair}: {data['actual']['return']:.1f}% vs {data['documented']['return']:.1f}% ({variance:+.1f}%) - {status}"
        )


if __name__ == "__main__":
    main()
