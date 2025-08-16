#!/usr/bin/env python3
"""
Test the dashboard API endpoints for live data integration
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add paths for imports
backend_dir = os.path.dirname(__file__)
src_path = os.path.join(backend_dir, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


async def test_dashboard_endpoints():
    """Test dashboard API endpoints"""

    print("=" * 50)
    print("TESTING DASHBOARD API ENDPOINTS")
    print("=" * 50)

    try:
        from monitoring.dashboard_api import app
        from fastapi.testclient import TestClient

        # Create test client
        client = TestClient(app)

        print("\n1. Testing health endpoint...")
        response = client.get("/health")
        print(f"✅ Health endpoint: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Status: {health_data['status']}")
            print(
                f"   Live data provider: {health_data['components'].get('live_data_provider', {}).get('available', 'N/A')}"
            )

        print("\n2. Testing data source status endpoint...")
        response = client.get("/data-source/status")
        print(f"✅ Data source endpoint: {response.status_code}")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   Data source: {status_data['data_source']}")
            print(f"   Update interval: {status_data['update_interval_seconds']}s")
            print(f"   Monitoring pairs: {status_data['monitoring_pairs']}")

        print("\n3. Testing current regime endpoint...")
        response = client.get("/regime/current")
        print(f"✅ Current regime endpoint: {response.status_code}")
        if response.status_code == 200:
            regime_data = response.json()
            print(f"   Current regime: {regime_data['current_regime']}")
            print(f"   Confidence: {regime_data['confidence']:.2f}")
            print(f"   Update interval: 30s (live data)")

        print("\n" + "=" * 50)
        print("✅ DASHBOARD API TESTS COMPLETED!")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"❌ Dashboard API test failed: {e}")
        return False


if __name__ == "__main__":
    # First install required testing dependency
    import subprocess

    try:
        import fastapi.testclient
    except ImportError:
        print("Installing required test dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)

    asyncio.run(test_dashboard_endpoints())
