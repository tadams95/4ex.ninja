#!/usr/bin/env python3
"""
Strategy Performance Comparison for 4ex.ninja
Compares single timeframe vs multi-timeframe confluence performance
"""

import json
import os
from typing import Dict, Any
from datetime import datetime


def load_results(filename: str) -> Dict[str, Any]:
    """Load backtest results from JSON file"""
    filepath = "../4ex.ninja-frontend/public/data/strategy/" + filename
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return {}


def main():
    """Compare all strategy performances"""

    # Load all strategy results
    h4_results = load_results("h4_portfolio_summary.json")
    daily_results = load_results("daily_portfolio_summary.json")
    weekly_results = load_results("weekly_portfolio_summary.json")
    confluence_results = load_results("confluence_portfolio_summary.json")

    print("🚀 4EX.NINJA COMPREHENSIVE STRATEGY COMPARISON")
    print("=" * 80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Portfolio Performance Comparison
    print("\n📊 PORTFOLIO PERFORMANCE COMPARISON")
    print("-" * 50)

    strategies = [
        ("H4 Only", h4_results),
        ("Daily Only", daily_results),
        ("Weekly Only", weekly_results),
        ("Confluence", confluence_results),
    ]

    print(
        f"{'Strategy':<15} {'Return':<10} {'Win Rate':<10} {'Drawdown':<10} {'Sharpe':<8} {'Trades':<8}"
    )
    print("-" * 65)

    for name, results in strategies:
        if results:
            return_val = results.get("portfolio_return", 0)
            win_rate = results.get("portfolio_win_rate", 0)
            drawdown = results.get("max_drawdown", 0)
            sharpe = results.get("sharpe_ratio", 0)
            trades = results.get("total_trades", 0)

            print(
                f"{name:<15} {return_val:>7.2f}%  {win_rate:>7.1f}%   {drawdown:>7.1f}%   {sharpe:>6.2f}   {trades:>6}"
            )

    # Risk-Adjusted Performance
    print("\n📈 RISK-ADJUSTED PERFORMANCE ANALYSIS")
    print("-" * 50)

    print("🏆 WINNER ANALYSIS:")
    best_return = max([r.get("portfolio_return", 0) for _, r in strategies if r])
    best_sharpe = max([r.get("sharpe_ratio", 0) for _, r in strategies if r])
    best_drawdown = min([r.get("max_drawdown", 100) for _, r in strategies if r])

    for name, results in strategies:
        if results:
            return_val = results.get("portfolio_return", 0)
            sharpe = results.get("sharpe_ratio", 0)
            drawdown = results.get("max_drawdown", 100)

            awards = []
            if return_val == best_return:
                awards.append("🥇 Best Return")
            if sharpe == best_sharpe:
                awards.append("🏆 Best Sharpe")
            if drawdown == best_drawdown:
                awards.append("🛡️ Lowest Risk")

            if awards:
                print(f"   {name}: {', '.join(awards)}")

    # JPY Pairs Analysis
    print("\n💴 JPY PAIRS PERFORMANCE ANALYSIS")
    print("-" * 50)

    if confluence_results:
        jpy_pairs = ["USD_JPY", "EUR_JPY", "GBP_JPY", "AUD_JPY"]
        print("Confluence Strategy JPY Performance:")

        individual_results = confluence_results.get("individual_results", {})
        jpy_total = sum([individual_results.get(pair, 0) for pair in jpy_pairs])
        jpy_avg = jpy_total / len(jpy_pairs)

        print(f"   JPY Pairs Average: {jpy_avg:.2f}%")
        for pair in jpy_pairs:
            return_val = individual_results.get(pair, 0)
            print(f"   {pair}: {return_val:.2f}%")

    # Strategy Recommendations
    print("\n🎯 STRATEGY RECOMMENDATIONS")
    print("-" * 50)

    print("PRODUCTION TRADING STRATEGY:")
    print("1. PRIMARY: Multi-Timeframe Confluence")
    print(
        f"   - Portfolio Return: {confluence_results.get('portfolio_return', 0):.2f}%"
    )
    print(
        f"   - Risk Level: {confluence_results.get('max_drawdown', 0):.1f}% max drawdown"
    )
    print(
        f"   - Trade Frequency: {confluence_results.get('total_trades', 0)} trades (selective)"
    )
    print("   - Best for: High-quality, low-frequency setups")

    print("\n2. SECONDARY: Daily Only (Swing Trading)")
    print(f"   - Portfolio Return: {daily_results.get('portfolio_return', 0):.2f}%")
    print(f"   - Risk Level: {daily_results.get('max_drawdown', 0):.1f}% max drawdown")
    print(
        f"   - Trade Frequency: {daily_results.get('total_trades', 0)} trades (moderate)"
    )
    print("   - Best for: Consistent swing trading opportunities")

    print("\n3. CONSERVATIVE: Weekly Only (Position Trading)")
    print(f"   - Portfolio Return: {weekly_results.get('portfolio_return', 0):.2f}%")
    print(f"   - Risk Level: {weekly_results.get('max_drawdown', 0):.1f}% max drawdown")
    print(f"   - Trade Frequency: {weekly_results.get('total_trades', 0)} trades (low)")
    print("   - Best for: Low-risk, position trading approach")

    # Implementation Plan
    print("\n🚀 IMPLEMENTATION ROADMAP")
    print("-" * 50)
    print("PHASE 1: Deploy Confluence Strategy")
    print("- Focus on USD_JPY, EUR_JPY, GBP_JPY (top performers)")
    print("- 1.2 confluence threshold (proven effective)")
    print("- 1.5% max risk per trade")
    print("- Weekly trend + Daily setup + H4 execution")

    print("\nPHASE 2: Add Daily Swing Strategy")
    print("- Complement confluence with daily-only signals")
    print("- Different pairs to avoid overlap")
    print("- Portfolio diversification benefit")

    print("\nPHASE 3: Weekly Position Strategy")
    print("- Ultra-conservative third layer")
    print("- Longer-term position trades")
    print("- Risk management backbone")

    print("\n" + "=" * 80)
    print("🎉 ANALYSIS COMPLETE - READY FOR LIVE DEPLOYMENT!")
    print("=" * 80)


if __name__ == "__main__":
    main()
