#!/usr/bin/env python3
"""
Simple EMA optimization test - no complex loops, just direct testing
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Add backend directory to path
sys.path.insert(0, "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend")


def calculate_ema(data, period):
    """Calculate EMA for given period"""
    return data.ewm(span=period).mean()


def simple_backtest(data, ema_fast, ema_slow):
    """
    Simple backtest with realistic parameters
    - 1.5% stop loss, 3% take profit
    - Trading costs: 2 pips spread + 0.5 pips slippage
    """
    df = data.copy()
    df["ema_fast"] = calculate_ema(df["close"], ema_fast)
    df["ema_slow"] = calculate_ema(df["close"], ema_slow)

    # Generate signals
    df["signal"] = 0
    df.loc[df["ema_fast"] > df["ema_slow"], "signal"] = 1  # Long
    df.loc[df["ema_fast"] < df["ema_slow"], "signal"] = -1  # Short

    # Find signal changes
    df["position"] = df["signal"].diff()

    trades = []
    balance = 10000.0
    position = 0
    entry_price = 0

    for i in range(len(df)):
        if df.iloc[i]["position"] != 0 and position == 0:
            # Enter trade
            position = df.iloc[i]["signal"]
            entry_price = df.iloc[i]["close"]

        elif position != 0:
            # Check exit conditions
            current_price = df.iloc[i]["close"]

            # Calculate returns
            if position == 1:  # Long position
                stop_loss = entry_price * 0.985  # 1.5% stop loss
                take_profit = entry_price * 1.03  # 3% take profit

                if current_price <= stop_loss:
                    # Stop loss hit
                    return_pct = (stop_loss - entry_price) / entry_price
                    trades.append(
                        {"type": "LONG", "return": return_pct, "exit": "STOP_LOSS"}
                    )
                    position = 0
                elif current_price >= take_profit:
                    # Take profit hit
                    return_pct = (take_profit - entry_price) / entry_price
                    trades.append(
                        {"type": "LONG", "return": return_pct, "exit": "TAKE_PROFIT"}
                    )
                    position = 0

            else:  # Short position
                stop_loss = entry_price * 1.015  # 1.5% stop loss
                take_profit = entry_price * 0.97  # 3% take profit

                if current_price >= stop_loss:
                    # Stop loss hit
                    return_pct = (entry_price - stop_loss) / entry_price
                    trades.append(
                        {"type": "SHORT", "return": return_pct, "exit": "STOP_LOSS"}
                    )
                    position = 0
                elif current_price <= take_profit:
                    # Take profit hit
                    return_pct = (entry_price - take_profit) / entry_price
                    trades.append(
                        {"type": "SHORT", "return": return_pct, "exit": "TAKE_PROFIT"}
                    )
                    position = 0

    # Calculate performance metrics
    if not trades:
        return {
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
            "total_trades": 0,
            "win_rate": 0,
            "total_return_pct": 0,
            "trades": [],
        }

    winning_trades = [t for t in trades if t["return"] > 0]
    win_rate = len(winning_trades) / len(trades) * 100
    total_return = sum(t["return"] for t in trades) * 100  # Convert to percentage

    # Apply trading costs (2.5 pips total cost per trade)
    cost_per_trade = 0.0025  # 0.25% cost per trade (spread + slippage)
    total_costs = len(trades) * cost_per_trade * 100
    net_return = total_return - total_costs

    return {
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "total_trades": len(trades),
        "winning_trades": len(winning_trades),
        "win_rate": round(win_rate, 1),
        "gross_return_pct": round(total_return, 1),
        "trading_costs_pct": round(total_costs, 1),
        "net_return_pct": round(net_return, 1),
        "trades": trades[:5],  # Sample of first 5 trades
    }


def main():
    """Run simple EMA optimization"""
    print("🚀 Simple EMA Optimization Test")
    print("=" * 50)

    # Load USD_JPY data
    data_file = "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/backtest_data/historical_data/USD_JPY_H4_5Y.json"

    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        return

    print("📊 Loading USD_JPY H4 data...")
    with open(data_file, "r") as f:
        json_data = json.load(f)

    # Convert JSON to DataFrame
    df_list = []
    for candle in json_data["data"]:
        df_list.append(
            {
                "time": pd.to_datetime(candle["timestamp"]),
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"]),
            }
        )

    data = pd.DataFrame(df_list)
    data.set_index("time", inplace=True)

    # Use last 2000 rows for testing (about 1 year of H4 data)
    test_data = data.tail(2000)
    print(
        f"✅ Using {len(test_data)} rows ({test_data.index[0]} to {test_data.index[-1]})"
    )

    # Test EMA combinations
    fast_periods = [10, 15, 20, 25]
    slow_periods = [40, 45, 50, 55]

    print(
        f"\n🔬 Testing {len(fast_periods)} x {len(slow_periods)} = {len(fast_periods) * len(slow_periods)} combinations"
    )
    print("-" * 50)

    results = []

    for ema_fast in fast_periods:
        for ema_slow in slow_periods:
            if ema_fast >= ema_slow:
                continue

            print(f"Testing EMA {ema_fast}/{ema_slow}...", end=" ")

            result = simple_backtest(test_data, ema_fast, ema_slow)
            results.append(result)

            print(
                f"Trades: {result['total_trades']}, Win Rate: {result['win_rate']}%, Return: {result['net_return_pct']}%"
            )

    # Find best results
    print("\n📈 TOP 5 RESULTS BY NET RETURN:")
    print("-" * 70)

    best_results = sorted(results, key=lambda x: x["net_return_pct"], reverse=True)[:5]

    for i, result in enumerate(best_results, 1):
        print(
            f"{i}. EMA {result['ema_fast']}/{result['ema_slow']}: "
            f"{result['net_return_pct']}% return, "
            f"{result['win_rate']}% win rate, "
            f"{result['total_trades']} trades"
        )

    # Find best by win rate
    print("\n🎯 TOP 3 RESULTS BY WIN RATE:")
    print("-" * 70)

    best_winrate = sorted(results, key=lambda x: x["win_rate"], reverse=True)[:3]

    for i, result in enumerate(best_winrate, 1):
        print(
            f"{i}. EMA {result['ema_fast']}/{result['ema_slow']}: "
            f"{result['win_rate']}% win rate, "
            f"{result['net_return_pct']}% return, "
            f"{result['total_trades']} trades"
        )

    # Save results
    output_file = "simple_ema_optimization_results.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                "test_period": f"{test_data.index[0]} to {test_data.index[-1]}",
                "total_combinations_tested": len(results),
                "best_by_return": best_results[0],
                "best_by_winrate": best_winrate[0],
                "all_results": results,
            },
            f,
            indent=2,
            default=str,
        )

    print(f"\n💾 Results saved to: {output_file}")
    print("\n✅ Simple optimization completed successfully!")

    # Recommend best parameters
    best = best_results[0]
    print(f"\n🏆 RECOMMENDED PARAMETERS:")
    print(f"   EMA Fast: {best['ema_fast']}")
    print(f"   EMA Slow: {best['ema_slow']}")
    print(f"   Expected Win Rate: {best['win_rate']}%")
    print(f"   Expected Return: {best['net_return_pct']}% (after costs)")
    print(f"   Expected Trades: {best['total_trades']} per year")


if __name__ == "__main__":
    main()
