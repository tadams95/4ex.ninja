#!/usr/bin/env python3
"""
Test script for export functionality and chart data endpoints
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from monitoring.dashboard_api import (
    _convert_to_csv,
    _convert_performance_to_csv,
    _regime_to_numeric,
)


async def test_csv_conversion():
    """Test CSV conversion functionality"""
    print("Testing CSV conversion...")

    # Sample regime data
    sample_regime_data = [
        {
            "timestamp": "2024-01-01T12:00:00",
            "regime": "trending_high_vol",
            "confidence": 0.85,
            "volatility": 0.02,
            "trend_direction": "up",
            "pair_data": {
                "EUR/USD": {"price": 1.0850, "volume": 1000},
                "GBP/USD": {"price": 1.2650, "volume": 800},
            },
        },
        {
            "timestamp": "2024-01-01T12:30:00",
            "regime": "ranging_low_vol",
            "confidence": 0.72,
            "volatility": 0.01,
            "trend_direction": "sideways",
            "pair_data": {
                "EUR/USD": {"price": 1.0845, "volume": 950},
                "GBP/USD": {"price": 1.2655, "volume": 750},
            },
        },
    ]

    pairs = ["EUR/USD", "GBP/USD"]
    csv_result = await _convert_to_csv(sample_regime_data, pairs)

    print("CSV Result:")
    print(csv_result)
    print()


async def test_performance_csv():
    """Test performance CSV conversion"""
    print("Testing Performance CSV conversion...")

    sample_performance_data = [
        {
            "regime": "trending_high_vol",
            "total_return": 0.15,
            "sharpe_ratio": 1.8,
            "max_drawdown": -0.05,
            "win_rate": 0.65,
        },
        {
            "regime": "ranging_low_vol",
            "total_return": 0.08,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.03,
            "win_rate": 0.58,
        },
    ]

    csv_result = await _convert_performance_to_csv(sample_performance_data)

    print("Performance CSV Result:")
    print(csv_result)
    print()


def test_regime_to_numeric():
    """Test regime to numeric conversion"""
    print("Testing regime to numeric conversion...")

    regimes = [
        "trending_high_vol",
        "trending_low_vol",
        "ranging_high_vol",
        "ranging_low_vol",
        "unknown",
    ]

    for regime in regimes:
        numeric_value = _regime_to_numeric(regime)
        print(f"{regime} -> {numeric_value}")

    print()


async def main():
    """Run all tests"""
    print("=== Testing Export Functionality ===")
    print()

    await test_csv_conversion()
    await test_performance_csv()
    test_regime_to_numeric()

    print("=== All tests completed ===")


if __name__ == "__main__":
    asyncio.run(main())
