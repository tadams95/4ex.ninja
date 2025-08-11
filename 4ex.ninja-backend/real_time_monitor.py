#!/usr/bin/env python3
"""
Real-time Memory Monitor for Digital Ocean Droplet

Monitors system resources while your strategy runs to ensure
optimal performance and detect any memory leaks or issues.
"""

import time
import psutil
import subprocess
from datetime import datetime


def get_redis_memory():
    """Get Redis memory usage."""
    try:
        result = subprocess.run(
            ["redis-cli", "-a", "4exninja_redis_2025", "INFO", "memory"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "used_memory_human:" in line:
                    return line.split(":")[1].strip()
    except:
        pass
    return "N/A"


def get_strategy_processes():
    """Get strategy process information."""
    processes = []
    for proc in psutil.process_iter(
        ["pid", "name", "cmdline", "memory_percent", "cpu_percent"]
    ):
        try:
            if any(
                "MA_Unified_Strat" in str(cmd) for cmd in proc.info["cmdline"] or []
            ):
                processes.append(
                    {
                        "pid": proc.info["pid"],
                        "memory_percent": round(proc.info["memory_percent"], 1),
                        "cpu_percent": round(proc.info["cpu_percent"], 1),
                    }
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes


def monitor_system():
    """Main monitoring loop."""
    print("🖥️  Real-time System Monitor for 4ex.ninja Strategy")
    print("=" * 60)
    print("Press Ctrl+C to stop monitoring")
    print()

    try:
        while True:
            # System memory
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Disk usage
            disk = psutil.disk_usage("/")

            # Redis memory
            redis_memory = get_redis_memory()

            # Strategy processes
            strategy_procs = get_strategy_processes()

            # Clear screen and display
            print(f"\033[2J\033[H")  # Clear screen
            print(
                "🖥️  4ex.ninja System Monitor - "
                + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            )
            print("=" * 60)

            # System overview
            print(
                f"💾 Memory: {memory.used//1024//1024:,}MB / {memory.total//1024//1024:,}MB ({memory.percent:.1f}%)"
            )
            print(
                f"🔄 Swap:   {swap.used//1024//1024:,}MB / {swap.total//1024//1024:,}MB ({swap.percent:.1f}%)"
            )
            print(f"💻 CPU:    {cpu_percent:.1f}%")
            print(
                f"💿 Disk:   {disk.used//1024//1024//1024:.1f}GB / {disk.total//1024//1024//1024:.1f}GB ({disk.used/disk.total*100:.1f}%)"
            )
            print(f"🔧 Redis:  {redis_memory}")

            # Strategy processes
            print(f"\n📈 Strategy Processes ({len(strategy_procs)} active):")
            if strategy_procs:
                for proc in strategy_procs:
                    print(
                        f"   PID {proc['pid']}: Memory {proc['memory_percent']:.1f}%, CPU {proc['cpu_percent']:.1f}%"
                    )
            else:
                print("   ⚠️  No strategy processes detected")

            # Health indicators
            print(f"\n🚦 Health Status:")

            # Memory health
            if memory.percent < 70:
                memory_status = "🟢 GOOD"
            elif memory.percent < 85:
                memory_status = "🟡 MODERATE"
            else:
                memory_status = "🔴 HIGH"
            print(f"   Memory: {memory_status}")

            # CPU health
            if cpu_percent < 50:
                cpu_status = "🟢 GOOD"
            elif cpu_percent < 80:
                cpu_status = "🟡 MODERATE"
            else:
                cpu_status = "🔴 HIGH"
            print(f"   CPU: {cpu_status}")

            # Process health
            if len(strategy_procs) >= 1:
                proc_status = "🟢 RUNNING"
            else:
                proc_status = "🔴 STOPPED"
            print(f"   Strategy: {proc_status}")

            print(f"\n⏱️  Next update in 5 seconds... (Ctrl+C to stop)")

            time.sleep(5)

    except KeyboardInterrupt:
        print(f"\n\n👋 Monitoring stopped by user")
        print("Final system state:")
        memory = psutil.virtual_memory()
        print(f"   Memory: {memory.percent:.1f}%")
        print(f"   Strategy processes: {len(get_strategy_processes())}")


if __name__ == "__main__":
    monitor_system()
