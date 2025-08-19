#!/usr/bin/env python3
"""
Test Backtest Page API Endpoints
Verify all new endpoints can load data successfully
"""

import sys
import os
from pathlib import Path

# Add src to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir / "src"))

import asyncio
from backtesting.backtest_api import (
    get_top_performance,
    get_visual_datasets,
    get_single_visual_dataset,
    get_methodology_content,
    get_equity_curves,
    get_backtest_page_summary,
)


async def test_endpoints():
    """Test all new backtest page endpoints"""

    print("🧪 Testing Backtest Page API Endpoints...")
    print("=" * 50)

    # Test 1: Performance data
    print("\n📊 1. Testing /backtest/page/performance")
    try:
        result = await get_top_performance()
        print(f"   ✅ Status: {result['status']}")
        print(f"   📈 Strategies: {len(result['data']['top_performing_strategies'])}")
        print(
            f"   🎯 Top strategy: {result['data']['top_performing_strategies'][0]['currency_pair']}"
        )
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 2: Visual datasets
    print("\n🎨 2. Testing /backtest/page/visual-datasets")
    try:
        result = await get_visual_datasets()
        print(f"   ✅ Status: {result['status']}")
        print(f"   📊 Datasets: {len(result['data']['datasets'])}")
        print(f"   🗂️  Available: {list(result['data']['datasets'].keys())}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Single dataset
    print("\n📈 3. Testing /backtest/page/visual-datasets/risk_return_scatter")
    try:
        result = await get_single_visual_dataset("risk_return_scatter")
        print(f"   ✅ Status: {result['status']}")
        print(f"   🎯 Dataset: {result['dataset']}")
        print(f"   📊 Data points: {len(result['data']['data'])}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 4: Methodology content
    print("\n📋 4. Testing /backtest/page/methodology")
    try:
        result = await get_methodology_content()
        print(f"   ✅ Status: {result['status']}")
        print(
            f"   📝 Strategy doc length: {len(result['data']['strategy_methodology'])} chars"
        )
        print(
            f"   📊 Attribution doc length: {len(result['data']['performance_attribution'])} chars"
        )
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 5: Equity curves
    print("\n📈 5. Testing /backtest/page/equity-curves")
    try:
        result = await get_equity_curves()
        print(f"   ✅ Status: {result['status']}")
        print(f"   📊 Strategies: {len(result['data']['equity_curves'])}")
        print(f"   📅 Period: {result['data']['period']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 6: Summary for hero section
    print("\n🎯 6. Testing /backtest/page/summary")
    try:
        result = await get_backtest_page_summary()
        print(f"   ✅ Status: {result['status']}")
        print(
            f"   📈 Top return: {result['data']['hero_metrics']['top_annual_return']}"
        )
        print(f"   ⚖️  Top Sharpe: {result['data']['hero_metrics']['top_sharpe_ratio']}")
        print(
            f"   📊 Strategies analyzed: {result['data']['hero_metrics']['strategies_analyzed']}"
        )
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n🎉 API Endpoint Testing Complete!")
    print("\n📋 Available Endpoints:")
    print("   • GET /api/v1/backtest/page/performance")
    print("   • GET /api/v1/backtest/page/visual-datasets")
    print("   • GET /api/v1/backtest/page/visual-datasets/{dataset_name}")
    print("   • GET /api/v1/backtest/page/methodology")
    print("   • GET /api/v1/backtest/page/equity-curves")
    print("   • GET /api/v1/backtest/page/summary")


if __name__ == "__main__":
    asyncio.run(test_endpoints())
