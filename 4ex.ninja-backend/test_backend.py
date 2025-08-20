#!/usr/bin/env python3
"""
Test script for the clean backend
Verifies all endpoints and core functionality before deployment.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional


class BackendTester:
    """Test runner for the clean backend."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_health_check(self) -> Dict[str, Any]:
        """Test health check endpoint."""
        print("🔍 Testing health check...")

        if not self.session:
            return {"status": "error", "error": "No session available"}

        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Health check passed: {data['status']}")
                    print(f"   📊 Strategy count: {data['strategy_count']}")
                    return {"status": "pass", "data": data}
                else:
                    print(f"   ❌ Health check failed with status {response.status}")
                    return {"status": "fail", "error": f"Status {response.status}"}

        except Exception as e:
            print(f"   ❌ Health check error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def test_strategy_config(self) -> Dict[str, Any]:
        """Test strategy configuration endpoints."""
        print("🔍 Testing strategy configuration...")

        if not self.session:
            return {"status": "error", "error": "No session available"}

        try:
            # Test get all configs
            async with self.session.get(f"{self.base_url}/strategy/config") as response:
                if response.status == 200:
                    data = await response.json()
                    configs = data.get("configs", {})
                    print(f"   ✅ Got {len(configs)} strategy configurations")

                    # Verify optimal parameters
                    for pair, config in configs.items():
                        if config.get("fast_ma") != 50 or config.get("slow_ma") != 200:
                            print(f"   ⚠️  Non-optimal parameters for {pair}")
                        else:
                            print(f"   ✅ Optimal parameters confirmed for {pair}")

                    return {"status": "pass", "data": data}
                else:
                    print(f"   ❌ Strategy config failed with status {response.status}")
                    return {"status": "fail", "error": f"Status {response.status}"}

        except Exception as e:
            print(f"   ❌ Strategy config error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def test_signal_generation(self) -> Dict[str, Any]:
        """Test signal generation for EUR_USD_D."""
        print("🔍 Testing signal generation...")

        if not self.session:
            return {"status": "error", "error": "No session available"}

        try:
            request_data = {"pair": "EUR_USD_D", "force_recalculate": True}

            async with self.session.post(
                f"{self.base_url}/signals/generate", json=request_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    signal = data.get("signal", {})
                    print(
                        f"   ✅ Generated {signal.get('signal_type')} signal for EUR_USD"
                    )
                    print(f"   💰 Price: {signal.get('price')}")
                    print(f"   📈 Fast MA: {signal.get('fast_ma')}")
                    print(f"   📊 Slow MA: {signal.get('slow_ma')}")
                    print(f"   🎯 Confidence: {signal.get('confidence', 0):.1%}")
                    return {"status": "pass", "data": data}
                else:
                    print(
                        f"   ❌ Signal generation failed with status {response.status}"
                    )
                    text = await response.text()
                    print(f"   📄 Response: {text}")
                    return {"status": "fail", "error": f"Status {response.status}"}

        except Exception as e:
            print(f"   ❌ Signal generation error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def test_all_signals(self) -> Dict[str, Any]:
        """Test bulk signal generation."""
        print("🔍 Testing bulk signal generation...")

        if not self.session:
            return {"status": "error", "error": "No session available"}

        try:
            async with self.session.post(
                f"{self.base_url}/signals/generate-all"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    signals = data.get("signals", [])
                    print(f"   ✅ Generated {len(signals)} signals")

                    # Show signal summary
                    signal_types = {}
                    for signal in signals:
                        signal_type = signal.get("signal_type")
                        signal_types[signal_type] = signal_types.get(signal_type, 0) + 1

                    for signal_type, count in signal_types.items():
                        print(f"   📊 {signal_type}: {count} signals")

                    return {"status": "pass", "data": data}
                else:
                    print(
                        f"   ❌ Bulk signal generation failed with status {response.status}"
                    )
                    return {"status": "fail", "error": f"Status {response.status}"}

        except Exception as e:
            print(f"   ❌ Bulk signal generation error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics endpoint."""
        print("🔍 Testing performance metrics...")

        if not self.session:
            return {"status": "error", "error": "No session available"}

        try:
            async with self.session.get(
                f"{self.base_url}/performance/EUR_USD"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    metrics = data.get("metrics", {})
                    print(f"   ✅ Performance metrics retrieved")
                    print(f"   📈 Total Return: {metrics.get('total_return', 0):.2f}%")
                    print(f"   🎯 Win Rate: {metrics.get('win_rate', 0):.1%}")
                    print(f"   📊 Total Trades: {metrics.get('total_trades', 0)}")
                    return {"status": "pass", "data": data}
                else:
                    print(
                        f"   ❌ Performance metrics failed with status {response.status}"
                    )
                    return {"status": "fail", "error": f"Status {response.status}"}

        except Exception as e:
            print(f"   ❌ Performance metrics error: {str(e)}")
            return {"status": "error", "error": str(e)}


async def run_tests():
    """Run all tests."""
    print("🧪 Starting Clean Backend Tests")
    print("=" * 50)

    async with BackendTester() as tester:
        tests = [
            ("Health Check", tester.test_health_check),
            ("Strategy Config", tester.test_strategy_config),
            ("Signal Generation", tester.test_signal_generation),
            ("Bulk Signals", tester.test_all_signals),
            ("Performance Metrics", tester.test_performance_metrics),
        ]

        results = {}
        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            print(f"\n🔬 Running {test_name}...")
            result = await test_func()
            results[test_name] = result

            if result["status"] == "pass":
                passed += 1
                print(f"   ✅ {test_name} PASSED")
            else:
                print(
                    f"   ❌ {test_name} FAILED: {result.get('error', 'Unknown error')}"
                )

        print("\n" + "=" * 50)
        print(f"🏁 Test Summary: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Backend is ready for deployment.")
            return True
        else:
            print("⚠️  Some tests failed. Check the backend before deploying.")
            return False


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    exit(0 if success else 1)
