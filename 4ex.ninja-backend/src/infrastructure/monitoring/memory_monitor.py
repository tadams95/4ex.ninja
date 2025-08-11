"""
Memory Monitoring Service for Digital Ocean Droplet
Continuous monitoring of memory usage, Redis cache, and system resources
"""

import asyncio
import logging
import time
import psutil
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


class MemoryMonitor:
    """Monitor memory usage and system resources on Digital Ocean droplet."""

    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client = None
        self.monitoring_active = False
        self.log_file = Path("logs/memory_usage.log")

        # Ensure logs directory exists
        self.log_file.parent.mkdir(exist_ok=True)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize Redis connection for monitoring."""
        if REDIS_AVAILABLE and redis:
            try:
                self.redis_client = redis.Redis(
                    host=self.redis_host, port=self.redis_port, decode_responses=True
                )
                await self.redis_client.ping()
                self.logger.info("✅ Connected to Redis for memory monitoring")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not connect to Redis: {e}")
                self.redis_client = None

    def get_system_memory_info(self) -> Dict[str, Union[str, float]]:
        """Get comprehensive system memory information."""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_memory_gb": memory.total / (1024**3),
            "available_memory_gb": memory.available / (1024**3),
            "used_memory_gb": memory.used / (1024**3),
            "memory_usage_percent": memory.percent,
            "cached_memory_gb": getattr(memory, "cached", 0) / (1024**3),
            "buffer_memory_gb": getattr(memory, "buffers", 0) / (1024**3),
            "swap_total_gb": swap.total / (1024**3),
            "swap_used_gb": swap.used / (1024**3),
            "swap_usage_percent": swap.percent,
        }

    def get_process_memory_info(self) -> Dict[str, float]:
        """Get memory usage for current Python process."""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()

        return {
            "process_rss_mb": memory_info.rss / (1024**2),  # Resident Set Size
            "process_vms_mb": memory_info.vms / (1024**2),  # Virtual Memory Size
            "process_memory_percent": memory_percent,
            "process_pid": process.pid,
            "process_threads": process.num_threads(),
            "process_open_files": len(process.open_files()),
            "process_connections": len(process.connections()),
        }

    async def get_redis_memory_info(self) -> Dict[str, Any]:
        """Get detailed Redis memory usage information."""
        redis_info = {
            "redis_available": False,
            "redis_memory_used_mb": 0,
            "redis_memory_peak_mb": 0,
            "redis_keys_count": 0,
            "redis_memory_fragmentation_ratio": 0,
            "redis_memory_efficiency_percent": 0,
        }

        if self.redis_client:
            try:
                info = await self.redis_client.info("memory")
                redis_info.update(
                    {
                        "redis_available": True,
                        "redis_memory_used_mb": info.get("used_memory", 0) / (1024**2),
                        "redis_memory_peak_mb": info.get("used_memory_peak", 0)
                        / (1024**2),
                        "redis_memory_fragmentation_ratio": info.get(
                            "mem_fragmentation_ratio", 0
                        ),
                        "redis_memory_efficiency_percent": (
                            (
                                info.get("used_memory_dataset", 0)
                                / max(info.get("used_memory", 1), 1)
                            )
                            * 100
                        ),
                    }
                )

                # Get key count
                keyspace_info = await self.redis_client.info("keyspace")
                total_keys = 0
                for db_name, db_info in keyspace_info.items():
                    if db_name.startswith("db"):
                        # Parse "keys=123,expires=45,avg_ttl=0"
                        keys_count = int(db_info.split("keys=")[1].split(",")[0])
                        total_keys += keys_count

                redis_info["redis_keys_count"] = total_keys

            except Exception as e:
                self.logger.error(f"Failed to get Redis memory info: {e}")

        return redis_info

    def get_disk_usage_info(self) -> Dict[str, float]:
        """Get disk usage information for the droplet."""
        disk = psutil.disk_usage("/")

        return {
            "disk_total_gb": disk.total / (1024**3),
            "disk_used_gb": disk.used / (1024**3),
            "disk_free_gb": disk.free / (1024**3),
            "disk_usage_percent": (disk.used / disk.total) * 100,
        }

    def get_cpu_info(self) -> Dict[str, Union[float, int]]:
        """Get CPU usage information."""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        try:
            load_avg = psutil.getloadavg()
        except AttributeError:
            load_avg = (0.0, 0.0, 0.0)  # Windows doesn't have getloadavg

        return {
            "cpu_usage_percent": cpu_percent,
            "cpu_count": cpu_count or 1,
            "load_avg_1min": load_avg[0],
            "load_avg_5min": load_avg[1],
            "load_avg_15min": load_avg[2],
        }

    async def collect_comprehensive_metrics(self) -> Dict[str, Any]:
        """Collect all system metrics in one comprehensive report."""
        metrics = {}

        # System memory
        metrics.update(self.get_system_memory_info())

        # Process memory
        process_info = self.get_process_memory_info()
        metrics.update(process_info)

        # Redis memory
        redis_info = await self.get_redis_memory_info()
        metrics.update(redis_info)

        # Disk usage
        disk_info = self.get_disk_usage_info()
        metrics.update(disk_info)

        # CPU info
        cpu_info = self.get_cpu_info()
        metrics.update(cpu_info)

        return metrics

    def check_memory_alerts(self, metrics: Dict[str, Any]) -> List[str]:
        """Check for memory-related alerts and warnings."""
        alerts = []

        # System memory alerts
        if metrics["memory_usage_percent"] > 90:
            alerts.append(
                f"🚨 CRITICAL: System memory usage {metrics['memory_usage_percent']:.1f}% > 90%"
            )
        elif metrics["memory_usage_percent"] > 80:
            alerts.append(
                f"⚠️ WARNING: System memory usage {metrics['memory_usage_percent']:.1f}% > 80%"
            )

        # Process memory alerts
        if metrics["process_memory_percent"] > 50:
            alerts.append(
                f"⚠️ WARNING: Process memory usage {metrics['process_memory_percent']:.1f}% > 50%"
            )

        # Disk space alerts
        if metrics["disk_usage_percent"] > 90:
            alerts.append(
                f"🚨 CRITICAL: Disk usage {metrics['disk_usage_percent']:.1f}% > 90%"
            )
        elif metrics["disk_usage_percent"] > 80:
            alerts.append(
                f"⚠️ WARNING: Disk usage {metrics['disk_usage_percent']:.1f}% > 80%"
            )

        # CPU alerts
        if metrics["cpu_usage_percent"] > 90:
            alerts.append(
                f"🚨 CRITICAL: CPU usage {metrics['cpu_usage_percent']:.1f}% > 90%"
            )
        elif metrics["cpu_usage_percent"] > 80:
            alerts.append(
                f"⚠️ WARNING: CPU usage {metrics['cpu_usage_percent']:.1f}% > 80%"
            )

        # Redis-specific alerts
        if metrics["redis_available"]:
            if metrics["redis_memory_used_mb"] > 100:  # 100MB threshold
                alerts.append(
                    f"⚠️ WARNING: Redis memory usage {metrics['redis_memory_used_mb']:.1f}MB > 100MB"
                )

            if metrics["redis_memory_fragmentation_ratio"] > 1.5:
                alerts.append(
                    f"⚠️ WARNING: Redis memory fragmentation {metrics['redis_memory_fragmentation_ratio']:.2f} > 1.5"
                )

        return alerts

    def log_metrics_to_file(self, metrics: Dict[str, Any]):
        """Log metrics to file for historical analysis."""
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(metrics) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to log metrics to file: {e}")

    def print_metrics_summary(self, metrics: Dict[str, Any]):
        """Print a formatted summary of current metrics."""
        print("\n" + "=" * 60)
        print("📊 DIGITAL OCEAN DROPLET MEMORY MONITORING")
        print("=" * 60)

        print(f"🕐 Timestamp: {metrics['timestamp']}")
        print()

        # System Memory
        print("💾 System Memory:")
        print(f"   Total: {metrics['total_memory_gb']:.2f} GB")
        print(
            f"   Used: {metrics['used_memory_gb']:.2f} GB ({metrics['memory_usage_percent']:.1f}%)"
        )
        print(f"   Available: {metrics['available_memory_gb']:.2f} GB")
        if metrics["cached_memory_gb"] > 0:
            print(f"   Cached: {metrics['cached_memory_gb']:.2f} GB")
        print()

        # Process Memory
        print("🐍 Python Process:")
        print(f"   RSS Memory: {metrics['process_rss_mb']:.1f} MB")
        print(f"   Virtual Memory: {metrics['process_vms_mb']:.1f} MB")
        print(f"   Memory %: {metrics['process_memory_percent']:.1f}%")
        print(f"   Threads: {metrics['process_threads']}")
        print()

        # Redis Memory
        if metrics["redis_available"]:
            print("🔧 Redis Cache:")
            print(f"   Memory Used: {metrics['redis_memory_used_mb']:.1f} MB")
            print(f"   Memory Peak: {metrics['redis_memory_peak_mb']:.1f} MB")
            print(f"   Keys Count: {metrics['redis_keys_count']}")
            print(
                f"   Fragmentation: {metrics['redis_memory_fragmentation_ratio']:.2f}"
            )
            print(f"   Efficiency: {metrics['redis_memory_efficiency_percent']:.1f}%")
        else:
            print("🔧 Redis Cache: Not Available")
        print()

        # Storage
        print("💽 Disk Usage:")
        print(f"   Total: {metrics['disk_total_gb']:.1f} GB")
        print(
            f"   Used: {metrics['disk_used_gb']:.1f} GB ({metrics['disk_usage_percent']:.1f}%)"
        )
        print(f"   Free: {metrics['disk_free_gb']:.1f} GB")
        print()

        # CPU
        print("🖥️ CPU Usage:")
        print(f"   Current: {metrics['cpu_usage_percent']:.1f}%")
        print(f"   Cores: {metrics['cpu_count']}")
        print(
            f"   Load Avg: {metrics['load_avg_1min']:.2f}, {metrics['load_avg_5min']:.2f}, {metrics['load_avg_15min']:.2f}"
        )
        print()

        # Alerts
        alerts = self.check_memory_alerts(metrics)
        if alerts:
            print("🚨 ALERTS:")
            for alert in alerts:
                print(f"   {alert}")
        else:
            print("✅ All metrics within normal ranges")

        print("=" * 60)

    async def start_continuous_monitoring(self, interval_seconds: int = 300):
        """Start continuous monitoring (default every 5 minutes)."""
        self.logger.info(
            f"🚀 Starting continuous memory monitoring (interval: {interval_seconds}s)"
        )
        self.monitoring_active = True

        while self.monitoring_active:
            try:
                metrics = await self.collect_comprehensive_metrics()

                # Print summary
                self.print_metrics_summary(metrics)

                # Log to file
                self.log_metrics_to_file(metrics)

                # Check for alerts
                alerts = self.check_memory_alerts(metrics)
                for alert in alerts:
                    self.logger.warning(alert)

                # Wait for next interval
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                self.logger.error(f"Error during monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.monitoring_active = False
        self.logger.info("🛑 Memory monitoring stopped")

    async def generate_memory_report(self) -> str:
        """Generate a comprehensive memory usage report."""
        metrics = await self.collect_comprehensive_metrics()

        report = f"""
DIGITAL OCEAN DROPLET MEMORY REPORT
Generated: {metrics['timestamp']}
{'='*50}

SYSTEM OVERVIEW:
- Total RAM: {metrics['total_memory_gb']:.2f} GB
- Memory Usage: {metrics['memory_usage_percent']:.1f}% ({metrics['used_memory_gb']:.2f} GB used)
- Available RAM: {metrics['available_memory_gb']:.2f} GB
- Disk Usage: {metrics['disk_usage_percent']:.1f}% ({metrics['disk_used_gb']:.1f}/{metrics['disk_total_gb']:.1f} GB)

PYTHON PROCESS:
- Process Memory: {metrics['process_rss_mb']:.1f} MB ({metrics['process_memory_percent']:.1f}% of system)
- Virtual Memory: {metrics['process_vms_mb']:.1f} MB
- Threads: {metrics['process_threads']}
- Open Files: {metrics['process_open_files']}
- Network Connections: {metrics['process_connections']}

REDIS CACHE:
- Status: {'Available' if metrics['redis_available'] else 'Not Available'}
"""

        if metrics["redis_available"]:
            report += f"""- Memory Used: {metrics['redis_memory_used_mb']:.1f} MB
- Peak Memory: {metrics['redis_memory_peak_mb']:.1f} MB
- Cached Keys: {metrics['redis_keys_count']}
- Memory Fragmentation: {metrics['redis_memory_fragmentation_ratio']:.2f}
- Memory Efficiency: {metrics['redis_memory_efficiency_percent']:.1f}%
"""

        report += f"""
PERFORMANCE:
- CPU Usage: {metrics['cpu_usage_percent']:.1f}%
- CPU Cores: {metrics['cpu_count']}
- Load Average: {metrics['load_avg_1min']:.2f} (1m), {metrics['load_avg_5min']:.2f} (5m), {metrics['load_avg_15min']:.2f} (15m)

"""

        alerts = self.check_memory_alerts(metrics)
        if alerts:
            report += "ALERTS:\n"
            for alert in alerts:
                report += f"- {alert}\n"
        else:
            report += "STATUS: All metrics within normal ranges ✅\n"

        return report


# CLI interface
async def main():
    """Main CLI interface for memory monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Digital Ocean Droplet Memory Monitor")
    parser.add_argument(
        "--continuous", action="store_true", help="Start continuous monitoring"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Monitoring interval in seconds (default: 300)",
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate single memory report"
    )
    parser.add_argument(
        "--redis-host", default="localhost", help="Redis host (default: localhost)"
    )
    parser.add_argument(
        "--redis-port", type=int, default=6379, help="Redis port (default: 6379)"
    )

    args = parser.parse_args()

    monitor = MemoryMonitor(redis_host=args.redis_host, redis_port=args.redis_port)
    await monitor.initialize()

    try:
        if args.continuous:
            await monitor.start_continuous_monitoring(args.interval)
        elif args.report:
            report = await monitor.generate_memory_report()
            print(report)
        else:
            # Single snapshot
            metrics = await monitor.collect_comprehensive_metrics()
            monitor.print_metrics_summary(metrics)

    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
        monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
