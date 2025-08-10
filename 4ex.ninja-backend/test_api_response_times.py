#!/usr/bin/env python3
"""
API Response Time Testing Script

Tests various API endpoints and measures response times.
"""

import time
import requests
import statistics
import asyncio
import aiohttp
from typing import Dict, List, Tuple
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))


class APIResponseTimeAnalyzer:
    def __init__(self, base_url: str = "http://127.0.0.1:9000"):
        self.base_url = base_url
        self.results = []

    def test_endpoint(
        self, endpoint: str, method: str = "GET", iterations: int = 5
    ) -> Dict:
        """Test a single endpoint multiple times and return statistics."""
        print(f"\n🧪 Testing {method} {endpoint}")

        response_times = []
        status_codes = []
        response_sizes = []
        errors = []

        for i in range(iterations):
            try:
                start_time = time.perf_counter()

                if method.upper() == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                elif method.upper() == "POST":
                    response = requests.post(
                        f"{self.base_url}{endpoint}", json={}, timeout=30
                    )

                end_time = time.perf_counter()
                response_time = (end_time - start_time) * 1000  # Convert to ms

                response_times.append(response_time)
                status_codes.append(response.status_code)
                response_sizes.append(len(response.content))

                print(
                    f"   Request {i+1}: {response_time:.2f}ms | Status: {response.status_code}"
                )

            except Exception as e:
                errors.append(str(e))
                print(f"   Request {i+1}: ERROR - {str(e)}")

        if response_times:
            stats = {
                "endpoint": endpoint,
                "method": method,
                "iterations": iterations,
                "successful_requests": len(response_times),
                "errors": len(errors),
                "avg_response_time_ms": statistics.mean(response_times),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times),
                "median_response_time_ms": statistics.median(response_times),
                "p95_response_time_ms": self._percentile(response_times, 0.95),
                "p99_response_time_ms": self._percentile(response_times, 0.99),
                "status_codes": list(set(status_codes)),
                "avg_response_size_bytes": (
                    statistics.mean(response_sizes) if response_sizes else 0
                ),
                "error_rate": len(errors) / iterations * 100,
            }
        else:
            stats = {
                "endpoint": endpoint,
                "method": method,
                "iterations": iterations,
                "errors": len(errors),
                "error_rate": 100,
                "error_messages": errors,
            }

        self.results.append(stats)
        return stats

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        sorted_data = sorted(data)
        index = int(percentile * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]

    def test_common_endpoints(self):
        """Test commonly used endpoints."""
        endpoints = [
            # Core API endpoints
            ("/", "GET"),
            ("/docs", "GET"),
            ("/health", "GET"),
            # Performance monitoring endpoints
            ("/api/v1/performance/", "GET"),
            ("/api/v1/performance/metrics", "GET"),
            ("/api/v1/performance/system", "GET"),
            # Market data endpoints (if they exist)
            ("/api/v1/signals/", "GET"),
            ("/api/v1/market-data/", "GET"),
            # Auth endpoints (might not work without proper auth)
            ("/api/v1/auth/health", "GET"),
        ]

        print("🚀 Starting API Response Time Analysis")
        print(f"Base URL: {self.base_url}")
        print(f"Testing {len(endpoints)} endpoints with 5 iterations each")

        for endpoint, method in endpoints:
            try:
                self.test_endpoint(endpoint, method)
            except Exception as e:
                print(f"❌ Failed to test {endpoint}: {e}")

    def generate_report(self) -> str:
        """Generate a comprehensive performance report."""
        if not self.results:
            return "❌ No test results available"

        report = "\n" + "=" * 80 + "\n"
        report += "📊 API RESPONSE TIME ANALYSIS REPORT\n"
        report += "=" * 80 + "\n"

        # Overall statistics
        successful_tests = [
            r for r in self.results if r.get("successful_requests", 0) > 0
        ]

        if successful_tests:
            all_response_times = []
            for result in successful_tests:
                # Create a list with avg response time repeated for each successful request
                times = [result["avg_response_time_ms"]] * result.get(
                    "successful_requests", 1
                )
                all_response_times.extend(times)

            report += f"\n🎯 OVERALL PERFORMANCE SUMMARY:\n"
            report += f"   • Total Endpoints Tested: {len(self.results)}\n"
            report += f"   • Successful Endpoints: {len(successful_tests)}\n"
            report += f"   • Average Response Time: {statistics.mean(all_response_times):.2f}ms\n"
            report += f"   • Fastest Response: {min(all_response_times):.2f}ms\n"
            report += f"   • Slowest Response: {max(all_response_times):.2f}ms\n"
            report += f"   • 95th Percentile: {self._percentile(all_response_times, 0.95):.2f}ms\n"

        # Individual endpoint results
        report += f"\n📈 DETAILED ENDPOINT RESULTS:\n"
        report += "-" * 80 + "\n"

        for result in self.results:
            if result.get("successful_requests", 0) > 0:
                endpoint = result["endpoint"]
                method = result["method"]
                avg_time = result["avg_response_time_ms"]
                p95_time = result["p95_response_time_ms"]
                error_rate = result["error_rate"]

                status = (
                    "🟢 EXCELLENT"
                    if avg_time < 100
                    else (
                        "🟡 GOOD"
                        if avg_time < 500
                        else "🟠 NEEDS IMPROVEMENT" if avg_time < 1000 else "🔴 POOR"
                    )
                )

                report += f"\n{method} {endpoint}\n"
                report += f"   Status: {status}\n"
                report += f"   Average: {avg_time:.2f}ms | P95: {p95_time:.2f}ms | Error Rate: {error_rate:.1f}%\n"
                report += f"   Range: {result['min_response_time_ms']:.2f}ms - {result['max_response_time_ms']:.2f}ms\n"

                if result.get("status_codes"):
                    report += f"   Status Codes: {result['status_codes']}\n"
            else:
                report += f"\n❌ {result['method']} {result['endpoint']}\n"
                report += f"   FAILED - Error Rate: 100%\n"
                if "error_messages" in result:
                    report += f"   Errors: {result['error_messages'][:2]}\n"  # Show first 2 errors

        # Performance recommendations
        report += f"\n💡 PERFORMANCE RECOMMENDATIONS:\n"
        report += "-" * 80 + "\n"

        slow_endpoints = [
            r for r in successful_tests if r["avg_response_time_ms"] > 500
        ]
        if slow_endpoints:
            report += "🐌 SLOW ENDPOINTS (>500ms):\n"
            for result in slow_endpoints:
                report += f"   • {result['method']} {result['endpoint']}: {result['avg_response_time_ms']:.2f}ms\n"
            report += "\n"

        fast_endpoints = [
            r for r in successful_tests if r["avg_response_time_ms"] < 100
        ]
        if fast_endpoints:
            report += "⚡ FAST ENDPOINTS (<100ms):\n"
            for result in fast_endpoints:
                report += f"   • {result['method']} {result['endpoint']}: {result['avg_response_time_ms']:.2f}ms\n"
            report += "\n"

        failed_endpoints = [
            r for r in self.results if r.get("successful_requests", 0) == 0
        ]
        if failed_endpoints:
            report += "🚫 FAILED ENDPOINTS:\n"
            for result in failed_endpoints:
                report += f"   • {result['method']} {result['endpoint']}\n"
            report += "\n"

        report += "📋 ACTION ITEMS:\n"
        if slow_endpoints:
            report += "   1. Investigate and optimize slow endpoints (>500ms)\n"
        if failed_endpoints:
            report += "   2. Fix failing endpoints and ensure proper error handling\n"
        report += (
            "   3. Consider adding response caching for frequently accessed endpoints\n"
        )
        report += "   4. Monitor response times in production with alerting\n"

        report += "\n" + "=" * 80 + "\n"

        return report


def main():
    """Main function to run the API response time analysis."""

    # First, let's start the server programmatically
    print("🚀 Starting API Response Time Analysis...")

    analyzer = APIResponseTimeAnalyzer()

    # Test if server is running
    try:
        response = requests.get(f"{analyzer.base_url}/", timeout=5)
        print(f"✅ Server is running at {analyzer.base_url}")
    except Exception as e:
        print(f"❌ Server is not running at {analyzer.base_url}")
        print(f"Error: {e}")
        print("\nTo run this analysis:")
        print(
            "1. Start the server: PYTHONPATH=./src JWT_SECRET_KEY='test-key' python3 -m uvicorn app:app --host 127.0.0.1 --port 9000"
        )
        print("2. Run this script: python3 test_api_response_times.py")
        return

    # Run the tests
    analyzer.test_common_endpoints()

    # Generate and print report
    report = analyzer.generate_report()
    print(report)

    # Save report to file
    with open("api_response_time_report.txt", "w") as f:
        f.write(report)

    print("📄 Report saved to: api_response_time_report.txt")


if __name__ == "__main__":
    main()
