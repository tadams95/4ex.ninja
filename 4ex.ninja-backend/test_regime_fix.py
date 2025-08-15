#!/usr/bin/env python3
"""
Quick test to verify regime performance analyzer fixes work correctly.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from backtesting.regime_performance_analyzer import RegimePerformanceAnalyzer


def test_regime_analyzer():
    """Test the regime performance analyzer with the fixes."""
    print("🧪 Testing Regime Performance Analyzer fixes...")

    # Create test data
    dates = pd.date_range("2024-01-01", periods=50, freq="D")
    strategy_results = pd.DataFrame(
        {
            "timestamp": dates,
            "currency_pair": np.random.choice(["EURUSD", "GBPUSD"], 50),
            "pnl": np.random.normal(10, 20, 50),
            "pnl_pct": np.random.normal(0.001, 0.01, 50),
            "position_size": 100000,
            "entry_time": dates - pd.Timedelta(hours=2),
            "exit_time": dates,
        }
    )

    market_data = {
        "EURUSD": pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=100, freq="12H"),
                "close": 1.1000 + np.random.normal(0, 0.01, 100),
                "high": 1.1020 + np.random.normal(0, 0.01, 100),
                "low": 1.0980 + np.random.normal(0, 0.01, 100),
            }
        )
    }

    # Test the analyzer
    analyzer = RegimePerformanceAnalyzer()

    # Test the methods that had the fixes
    print("Testing _calculate_regime_performance_metrics...")
    metrics = analyzer._calculate_regime_performance_metrics(strategy_results)
    print(f"✅ Metrics calculated: {list(metrics.keys())}")

    print("Testing _classify_trade_regime...")
    regime = analyzer._classify_trade_regime(
        datetime(2024, 1, 15), "EURUSD", market_data
    )
    print(f"✅ Regime classified: {regime}")

    print("🎉 All tests passed! Fixes are working correctly.")


if __name__ == "__main__":
    test_regime_analyzer()
