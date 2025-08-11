#!/usr/bin/env python3
"""
Simple Memory and Performance Check for Digital Ocean Droplet
Lightweight version that works without complex dependencies
"""

import subprocess
import sys
import time
import json
from datetime import datetime


def check_system_memory():
    """Check system memory usage using basic system tools."""
    print("💾 SYSTEM MEMORY USAGE")
    print("-" * 30)

    try:
        # Use 'free' command to get memory info
        result = subprocess.run(["free", "-h"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "Mem:" in line or "Swap:" in line:
                    print(f"   {line}")

        # Get memory percentage
        result = subprocess.run(["free"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "Mem:" in line:
                    parts = line.split()
                    total = int(parts[1])
                    used = int(parts[2])
                    available = int(parts[6])

                    usage_percent = (used / total) * 100
                    print(f"\n   Memory Usage: {usage_percent:.1f}%")
                    print(f"   Available: {available/1024/1024:.2f} GB")

                    if usage_percent > 80:
                        print("   ⚠️ WARNING: High memory usage!")
                    else:
                        print("   ✅ Memory usage healthy")
                    break
    except Exception as e:
        print(f"   ❌ Could not check memory: {e}")


def check_redis_status():
    """Check if Redis is running and basic memory usage."""
    print("\n🔧 REDIS STATUS")
    print("-" * 30)

    try:
        # Check if Redis is running
        result = subprocess.run(
            ["redis-cli", "ping"], capture_output=True, text=True, timeout=5
        )

        if result.returncode == 0 and "PONG" in result.stdout:
            print("   ✅ Redis server is running")

            # Get Redis memory info
            result = subprocess.run(
                ["redis-cli", "INFO", "memory"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "used_memory_human:" in line:
                        memory = line.split(":")[1].strip()
                        print(f"   Redis Memory: {memory}")
                    elif "used_memory_peak_human:" in line:
                        peak = line.split(":")[1].strip()
                        print(f"   Peak Memory: {peak}")

            # Get number of keys
            result = subprocess.run(
                ["redis-cli", "DBSIZE"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                keys = result.stdout.strip()
                print(f"   Cached Keys: {keys}")
        else:
            print("   ❌ Redis server not responding")
            print("   💡 Install with: sudo apt install redis-server")
            print("   💡 Start with: sudo systemctl start redis")

    except FileNotFoundError:
        print("   ❌ Redis not installed")
        print("   💡 Install with: sudo apt install redis-server")
    except Exception as e:
        print(f"   ❌ Error checking Redis: {e}")


def check_python_processes():
    """Check Python process memory usage."""
    print("\n🐍 PYTHON PROCESS MEMORY")
    print("-" * 30)

    try:
        # Find Python processes related to 4ex.ninja
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

        if result.returncode == 0:
            lines = result.stdout.split("\n")
            python_processes = []

            for line in lines:
                if "python" in line.lower() and (
                    "4ex" in line or "uvicorn" in line or "app" in line
                ):
                    parts = line.split()
                    if len(parts) >= 11:
                        cpu_percent = parts[2]
                        mem_percent = parts[3]
                        memory_kb = parts[5]

                        try:
                            memory_mb = int(memory_kb) / 1024
                            python_processes.append(
                                {
                                    "cpu": cpu_percent,
                                    "memory_percent": mem_percent,
                                    "memory_mb": memory_mb,
                                    "command": " ".join(parts[10:])[:60] + "...",
                                }
                            )
                        except (ValueError, IndexError):
                            continue

            if python_processes:
                total_memory = sum(p["memory_mb"] for p in python_processes)
                print(f"   Total Python Memory: {total_memory:.1f} MB")

                for proc in python_processes:
                    print(
                        f"   Process: {proc['memory_percent']}% ({proc['memory_mb']:.1f}MB) - {proc['command']}"
                    )

                if total_memory < 500:
                    print("   ✅ Memory usage within acceptable range")
                else:
                    print("   ⚠️ High memory usage - consider optimization")
            else:
                print("   ℹ️ No 4ex.ninja Python processes found")

    except Exception as e:
        print(f"   ❌ Error checking processes: {e}")


def check_disk_usage():
    """Check disk usage."""
    print("\n💽 DISK USAGE")
    print("-" * 30)

    try:
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                header = lines[0]
                data = lines[1]
                print(f"   {header}")
                print(f"   {data}")

                # Extract usage percentage
                parts = data.split()
                if len(parts) >= 5:
                    usage_str = parts[4]  # e.g., "45%"
                    usage_percent = int(usage_str.replace("%", ""))

                    if usage_percent > 90:
                        print("   🚨 CRITICAL: Disk usage very high!")
                    elif usage_percent > 80:
                        print("   ⚠️ WARNING: Disk usage high")
                    else:
                        print("   ✅ Disk usage healthy")
    except Exception as e:
        print(f"   ❌ Error checking disk: {e}")


def test_signal_accuracy_concern():
    """Address the specific MA accuracy concern."""
    print("\n🎯 MA ACCURACY VALIDATION")
    print("-" * 30)
    print("   Your concern about MA accuracy with Redis caching is valid!")
    print("   The system should:")
    print("   1. Store complete MA state in Redis (last N values)")
    print("   2. Update incrementally with new candles")
    print("   3. Fall back to full calculation if cache missing")
    print()
    print("   🔍 To verify MA accuracy:")

    # Check if Redis has MA state keys
    try:
        result = subprocess.run(
            ["redis-cli", "KEYS", "*ma_state*"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            keys = result.stdout.strip().split("\n")
            print(f"   ✅ Found {len(keys)} MA state cache entries")

            # Show a sample key
            if keys:
                sample_key = keys[0]
                print(f"   📝 Sample cache key: {sample_key}")

                # Get the cached data to see its structure
                result = subprocess.run(
                    ["redis-cli", "GET", sample_key],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    data = result.stdout.strip()
                    if len(data) > 100:
                        data = data[:100] + "..."
                    print(f"   📊 Sample data: {data}")
        else:
            print("   ⚠️ No MA state cache found - caching may not be active")
            print("   💡 This could explain accuracy concerns!")

    except Exception as e:
        print(f"   ❌ Could not check MA cache: {e}")

    print("\n   📋 Recommendations:")
    print("   1. Run full performance test: python validate_performance.py")
    print("   2. Compare MA calculations with/without cache")
    print("   3. Verify incremental vs full calculation accuracy")


def main():
    """Run all basic checks."""
    print("🚀 4EX.NINJA BASIC PERFORMANCE CHECK")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Run all checks
    check_system_memory()
    check_redis_status()
    check_python_processes()
    check_disk_usage()
    test_signal_accuracy_concern()

    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    print("This basic check shows your system status.")
    print("For detailed performance validation, run:")
    print("   python validate_performance.py")
    print()
    print("For continuous monitoring, run:")
    print("   python src/infrastructure/monitoring/memory_monitor.py --continuous")
    print()
    print("🎯 Your MA accuracy concern is important!")
    print("The Redis cache must properly store MA states to maintain accuracy.")
    print("If cache is empty or not working, signals may be inaccurate.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Check interrupted by user")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback

        traceback.print_exc()
