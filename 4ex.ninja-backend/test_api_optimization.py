#!/usr/bin/env python3
"""
Test script to validate API response optimization features.
"""

import requests
import json
import time
import gzip
from typing import Dict, Any


def test_api_optimization(base_url: str = "http://127.0.0.1:8003"):
    """Test various API optimization features."""

    print("🧪 Testing API Response Optimizations\n")

    # Test 1: Basic response
    print("1️⃣ Testing basic signals response...")
    response = requests.get(f"{base_url}/api/v1/signals/?limit=2")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📦 Response size: {len(response.content)} bytes")
        print(f"   📋 Has metadata: {'meta' in data}")
        print(f"   🔢 Data count: {len(data.get('data', []))}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    print()

    # Test 2: Field selection
    print("2️⃣ Testing field selection...")
    response = requests.get(
        f"{base_url}/api/v1/signals/?limit=2&fields=id,pair,signal_type"
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📦 Response size: {len(response.content)} bytes")
        if data.get("data"):
            first_item = data["data"][0]
            print(f"   🎯 Fields in response: {list(first_item.keys())}")
            field_selection = data.get("meta", {}).get("field_selection", {})
            print(
                f"   🔍 Field selection enabled: {field_selection.get('enabled', False)}"
            )
    else:
        print(f"   ❌ Failed: {response.status_code}")
    print()

    # Test 3: Compression support
    print("3️⃣ Testing gzip compression...")
    headers = {"Accept-Encoding": "gzip"}
    response = requests.get(f"{base_url}/api/v1/signals/?limit=10", headers=headers)
    if response.status_code == 200:
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📦 Response size: {len(response.content)} bytes")
        print(
            f"   🗜️ Content-Encoding: {response.headers.get('content-encoding', 'none')}"
        )
        print(
            f"   📊 Compression supported: {'gzip' in response.headers.get('content-encoding', '')}"
        )
    else:
        print(f"   ❌ Failed: {response.status_code}")
    print()

    # Test 4: Market data optimization
    print("4️⃣ Testing market data optimization...")
    response = requests.get(
        f"{base_url}/api/v1/market-data/?limit=5&fields=instrument,timestamp,close"
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📦 Response size: {len(response.content)} bytes")
        print(f"   📋 Has pagination meta: {'meta' in data}")
        if data.get("meta"):
            print(
                f"   📄 Pagination type: {data['meta'].get('pagination_type', 'none')}"
            )
    else:
        print(f"   ❌ Failed: {response.status_code}")
    print()

    # Test 5: Latest price with field selection
    print("5️⃣ Testing latest price with field selection...")
    response = requests.get(
        f"{base_url}/api/v1/market-data/latest/EUR_USD?fields=instrument,bid,ask,spread"
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📦 Response size: {len(response.content)} bytes")
        if data.get("data"):
            print(f"   🎯 Fields in response: {list(data['data'].keys())}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    print()

    # Test 6: Performance comparison
    print("6️⃣ Testing performance comparison...")
    # Full response
    start_time = time.time()
    response_full = requests.get(f"{base_url}/api/v1/signals/?limit=10")
    full_time = time.time() - start_time

    # Optimized response
    start_time = time.time()
    response_opt = requests.get(
        f"{base_url}/api/v1/signals/?limit=10&fields=id,pair,signal_type",
        headers={"Accept-Encoding": "gzip"},
    )
    opt_time = time.time() - start_time

    if response_full.status_code == 200 and response_opt.status_code == 200:
        print(
            f"   ✅ Full response: {len(response_full.content)} bytes in {full_time:.3f}s"
        )
        print(
            f"   ✅ Optimized response: {len(response_opt.content)} bytes in {opt_time:.3f}s"
        )
        savings = (
            (len(response_full.content) - len(response_opt.content))
            / len(response_full.content)
        ) * 100
        print(f"   💾 Size reduction: {savings:.1f}%")

    print("\n🎉 API Response Optimization Testing Complete!")


if __name__ == "__main__":
    test_api_optimization()
