#!/usr/bin/env python3
"""
Multi-Pair EMA Optimization - Realistic Results
Expanding beyond USD_JPY to optimize all major pairs
"""

import os
import sys
import pandas as pd
import json
from datetime import datetime


def load_pair_data(pair):
    """Load historical data for a currency pair"""
    data_file = f"/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/backtest_data/historical_data/{pair}_H4_5Y.json"

    if not os.path.exists(data_file):
        return None

    with open(data_file, "r") as f:
        json_data = json.load(f)

    # Convert to DataFrame
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
    return data


def calculate_ema(data, period):
    """Calculate EMA for given period"""
    return data.ewm(span=period).mean()


def realistic_backtest(data, ema_fast, ema_slow, pair_name):
    """
    Realistic backtest with proper risk management
    - 1.5% stop loss, 3% take profit
    - Trading costs vary by pair
    """
    # Trading costs by pair (spread + slippage in pips)
    trading_costs = {
        "USD_JPY": 2.5,
        "EUR_USD": 2.0,
        "GBP_USD": 2.5,
        "USD_CHF": 3.0,
        "AUD_USD": 2.5,
        "USD_CAD": 2.5,
        "EUR_JPY": 3.0,
        "GBP_JPY": 3.5,
        "AUD_JPY": 3.5,
        "EUR_GBP": 2.5,
    }

    df = data.tail(2000).copy()  # Use last 2000 H4 candles (~1 year)

    if len(df) < 200:
        return {"error": "Insufficient data"}

    df["ema_fast"] = calculate_ema(df["close"], ema_fast)
    df["ema_slow"] = calculate_ema(df["close"], ema_slow)

    # Generate signals
    df["signal"] = 0
    df.loc[df["ema_fast"] > df["ema_slow"], "signal"] = 1  # Long
    df.loc[df["ema_fast"] < df["ema_slow"], "signal"] = -1  # Short

    # Find signal changes
    df["position"] = df["signal"].diff()

    trades = []
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
                    return_pct = (stop_loss - entry_price) / entry_price
                    trades.append(
                        {"type": "LONG", "return": return_pct, "exit": "STOP_LOSS"}
                    )
                    position = 0
                elif current_price >= take_profit:
                    return_pct = (take_profit - entry_price) / entry_price
                    trades.append(
                        {"type": "LONG", "return": return_pct, "exit": "TAKE_PROFIT"}
                    )
                    position = 0

            else:  # Short position
                stop_loss = entry_price * 1.015  # 1.5% stop loss
                take_profit = entry_price * 0.97  # 3% take profit

                if current_price >= stop_loss:
                    return_pct = (entry_price - stop_loss) / entry_price
                    trades.append(
                        {"type": "SHORT", "return": return_pct, "exit": "STOP_LOSS"}
                    )
                    position = 0
                elif current_price <= take_profit:
                    return_pct = (entry_price - take_profit) / entry_price
                    trades.append(
                        {"type": "SHORT", "return": return_pct, "exit": "TAKE_PROFIT"}
                    )
                    position = 0

    # Calculate performance metrics
    if not trades:
        return {
            "pair": pair_name,
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
            "total_trades": 0,
            "win_rate": 0,
            "net_return_pct": 0,
            "status": "no_trades",
        }

    winning_trades = [t for t in trades if t["return"] > 0]
    win_rate = len(winning_trades) / len(trades) * 100
    gross_return = sum(t["return"] for t in trades) * 100

    # Apply trading costs
    cost_per_trade = (
        trading_costs.get(pair_name, 2.5) * 0.001
    )  # Convert pips to percentage
    total_costs = len(trades) * cost_per_trade * 100
    net_return = gross_return - total_costs

    return {
        "pair": pair_name,
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "total_trades": len(trades),
        "winning_trades": len(winning_trades),
        "win_rate": round(win_rate, 1),
        "gross_return_pct": round(gross_return, 1),
        "trading_costs_pct": round(total_costs, 1),
        "net_return_pct": round(net_return, 1),
        "avg_return_per_trade": round(net_return / len(trades), 2),
        "status": "completed",
    }


def optimize_pair(pair_name, data):
    """Optimize EMA parameters for a specific pair"""
    print(f"\n🔍 Optimizing {pair_name}...")

    # Test ranges (focused on promising areas)
    fast_periods = [15, 20, 25, 30]
    slow_periods = [45, 50, 55, 60]

    results = []
    best_result = None
    best_score = -999

    for ema_fast in fast_periods:
        for ema_slow in slow_periods:
            if ema_fast >= ema_slow:
                continue

            result = realistic_backtest(data, ema_fast, ema_slow, pair_name)

            if result.get("status") == "completed" and result["total_trades"] >= 5:
                results.append(result)

                # Score based on win rate + return (with minimum trade requirement)
                score = result["win_rate"] * 0.4 + result["net_return_pct"] * 0.6

                if score > best_score:
                    best_score = score
                    best_result = result

                print(
                    f"   EMA {ema_fast}/{ema_slow}: {result['win_rate']}% WR, "
                    f"{result['net_return_pct']}% return, {result['total_trades']} trades"
                )

    return best_result, results


def main():
    """Run multi-pair optimization"""
    print("🚀 Multi-Pair EMA Optimization")
    print("=" * 60)
    print("Testing realistic parameters across major currency pairs...")

    # Major currency pairs to optimize
    pairs_to_test = [
        "USD_JPY",
        "EUR_USD",
        "GBP_USD",
        "USD_CHF",
        "AUD_USD",
        "USD_CAD",
        "EUR_JPY",
        "GBP_JPY",
        "AUD_JPY",
        "EUR_GBP",
    ]

    optimization_results = {}
    all_results = {}

    for pair in pairs_to_test:
        print(f"\n📊 Loading {pair} data...")
        data = load_pair_data(pair)

        if data is None:
            print(f"❌ No data available for {pair}")
            continue

        if len(data) < 2000:
            print(f"❌ Insufficient data for {pair}: {len(data)} candles")
            continue

        print(f"✅ Loaded {len(data)} H4 candles for {pair}")

        best_result, all_pair_results = optimize_pair(pair, data)

        if best_result:
            optimization_results[pair] = best_result
            all_results[pair] = all_pair_results

            print(
                f"🏆 Best for {pair}: EMA {best_result['ema_fast']}/{best_result['ema_slow']}"
            )
            print(f"   Win Rate: {best_result['win_rate']}%")
            print(f"   Net Return: {best_result['net_return_pct']}%")
            print(f"   Trades: {best_result['total_trades']}")
        else:
            print(f"❌ No viable parameters found for {pair}")

    # Generate summary
    print(f"\n📈 OPTIMIZATION SUMMARY")
    print("=" * 60)

    if optimization_results:
        # Rank by net return
        ranked_pairs = sorted(
            optimization_results.items(),
            key=lambda x: x[1]["net_return_pct"],
            reverse=True,
        )

        print("🏆 TOP PERFORMERS BY NET RETURN:")
        for i, (pair, result) in enumerate(ranked_pairs[:5], 1):
            print(
                f"{i}. {pair}: {result['net_return_pct']}% return, "
                f"{result['win_rate']}% WR, EMA {result['ema_fast']}/{result['ema_slow']}"
            )

        # Rank by win rate
        ranked_by_winrate = sorted(
            optimization_results.items(), key=lambda x: x[1]["win_rate"], reverse=True
        )

        print(f"\n🎯 TOP PERFORMERS BY WIN RATE:")
        for i, (pair, result) in enumerate(ranked_by_winrate[:5], 1):
            print(
                f"{i}. {pair}: {result['win_rate']}% WR, "
                f"{result['net_return_pct']}% return, EMA {result['ema_fast']}/{result['ema_slow']}"
            )

        # Generate optimized parameters file
        optimized_params = {}
        for pair, result in optimization_results.items():
            optimized_params[pair] = {
                "ema_fast": result["ema_fast"],
                "ema_slow": result["ema_slow"],
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "optimization_status": "REALISTIC_EMA_OPTIMIZED",
                "optimization_date": "2025-08-20",
                "expected_performance": {
                    "win_rate": f"{result['win_rate']}%",
                    "annual_return": f"{result['net_return_pct']}%",
                    "trades_per_year": result["total_trades"],
                    "avg_return_per_trade": f"{result['avg_return_per_trade']}%",
                },
                "backtest_results": {
                    "total_trades": result["total_trades"],
                    "winning_trades": result["winning_trades"],
                    "gross_return_pct": result["gross_return_pct"],
                    "trading_costs_pct": result["trading_costs_pct"],
                    "net_return_pct": result["net_return_pct"],
                },
            }

        # Save results
        output_data = {
            "optimization_date": datetime.now().isoformat(),
            "methodology": "Realistic backtesting with 1.5% SL, 3% TP, proper trading costs",
            "optimized_parameters": optimized_params,
            "summary": {
                "pairs_tested": len(pairs_to_test),
                "pairs_optimized": len(optimization_results),
                "best_pair": ranked_pairs[0][0] if ranked_pairs else None,
                "best_return": (
                    ranked_pairs[0][1]["net_return_pct"] if ranked_pairs else None
                ),
                "best_winrate": (
                    ranked_by_winrate[0][1]["win_rate"] if ranked_by_winrate else None
                ),
            },
            "detailed_results": all_results,
        }

        with open("multi_pair_optimization_results.json", "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\n💾 Results saved to: multi_pair_optimization_results.json")
        print(
            f"✅ Optimization completed! {len(optimization_results)} pairs optimized."
        )

        # Update enhanced_daily_strategy parameters
        enhanced_params_file = "realistic_optimized_parameters.json"
        with open(enhanced_params_file, "w") as f:
            json.dump(optimized_params, f, indent=2)

        print(f"📝 Enhanced strategy parameters saved to: {enhanced_params_file}")

    else:
        print("❌ No pairs could be optimized. Check data availability.")


if __name__ == "__main__":
    main()
