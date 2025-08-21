#!/usr/bin/env python3
"""
Quick test for fixed EMA optimization (no infinite loops)
"""

import os
import sys
import pandas as pd
import logging
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from parameter_optimization.ema_period_optimization import EMAParameterOptimizer


def test_quick_optimization():
    """Test the fixed optimization without infinite loops"""
    print("🔧 Testing Fixed EMA Optimization...")

    # Initialize optimizer
    optimizer = EMAParameterOptimizer()

    # Load small dataset for quick test
    test_pair = "USD_JPY"

    try:
        # Check if data exists
        data_file = f"{backend_dir}/backtest_data/{test_pair}_H4_data.csv"

        if not os.path.exists(data_file):
            print(f"❌ Data file not found: {data_file}")
            return False

        print(f"📊 Loading test data for {test_pair}...")
        data = pd.read_csv(data_file, index_col=0, parse_dates=True)

        if len(data) < 1000:
            print(f"❌ Insufficient data: {len(data)} rows")
            return False

        # Test with limited data (last 500 rows for quick test)
        test_data = data.tail(500)
        print(f"✅ Using {len(test_data)} rows for test")

        # Test single EMA combination to verify no infinite loop
        print("🧪 Testing single EMA combination...")
        result = optimizer.backtest_ema_combination(test_pair, test_data, 20, 50)

        if "error" in result:
            print(f"❌ Test failed: {result['error']}")
            return False

        print("✅ Single combination test successful!")
        print(f"   Win Rate: {result.get('win_rate', 'N/A')}%")
        print(f"   Total Trades: {result.get('total_trades', 'N/A')}")
        print(f"   Return: {result.get('total_return_pct', 'N/A')}%")

        # Test optimization with limited parameters (2x2 = 4 combinations)
        print("\n🚀 Testing limited optimization (2x2 combinations)...")

        optimization_params = {
            "ema_fast_range": [15, 20],  # Only 2 fast values
            "ema_slow_range": [45, 50],  # Only 2 slow values
            "target_win_rate": 50.0,
            "priority": "improve_performance",
        }

        optimization_result = optimizer.optimize_pair_ema_parameters(
            test_pair, test_data, optimization_params
        )

        if "error" in optimization_result:
            print(f"❌ Optimization failed: {optimization_result['error']}")
            return False

        print("✅ Limited optimization successful!")
        print(f"   Best EMA Fast: {optimization_result.get('ema_fast', 'N/A')}")
        print(f"   Best EMA Slow: {optimization_result.get('ema_slow', 'N/A')}")
        print(f"   Best Win Rate: {optimization_result.get('win_rate', 'N/A')}%")
        print(
            f"   Expected Return: {optimization_result.get('total_return_pct', 'N/A')}%"
        )

        return True

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_quick_optimization()

    if success:
        print("\n🎉 All tests passed! Fixed optimization is working properly.")
        print("💡 You can now run the full optimization safely.")
    else:
        print(
            "\n❌ Tests failed. Check the issues above before running full optimization."
        )
