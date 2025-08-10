"""
System Resource Metrics Monitor

Tracks system-level performance metrics including CPU, memory, disk usage,
and network statistics for production monitoring.
"""

import asyncio
import logging
import psutil
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional
from collections import deque


@dataclass
class SystemMetrics:
    """System performance metrics snapshot."""
    
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    open_file_descriptors: int


class SystemMetricsMonitor:
    """Monitors system resource usage and performance."""
    
    def __init__(self, max_history: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.max_history = max_history
        self._metrics_history = deque(maxlen=max_history)
        self._last_network_counters = None
        self._monitoring = False
        self._monitor_task = None
        
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous system monitoring."""
        if self._monitoring:
            self.logger.warning("System monitoring already running")
            return
            
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval_seconds))
        self.logger.info(f"Started system monitoring with {interval_seconds}s interval")
        
    async def stop_monitoring(self):
        """Stop system monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped system monitoring")
        
    async def _monitor_loop(self, interval_seconds: int):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                metrics = await self._collect_metrics()
                self._metrics_history.append(metrics)
                
                # Log warnings for high resource usage
                await self._check_resource_alerts(metrics)
                
            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {e}")
                
            await asyncio.sleep(interval_seconds)
            
    async def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # Run CPU-intensive operations in thread pool
        loop = asyncio.get_event_loop()
        
        # CPU metrics
        cpu_percent = await loop.run_in_executor(None, psutil.cpu_percent, 1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Network metrics
        network = psutil.net_io_counters()
        
        # Process metrics
        process_count = len(psutil.pids())
        
        # File descriptor count (Unix-like systems)
        try:
            open_fds = len(psutil.Process().open_files())
        except (psutil.AccessDenied, OSError):
            open_fds = 0
            
        return SystemMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_usage_percent=disk.percent,
            disk_free_gb=disk.free / (1024 * 1024 * 1024),
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            process_count=process_count,
            open_file_descriptors=open_fds
        )
        
    async def _check_resource_alerts(self, metrics: SystemMetrics):
        """Check for resource usage alerts."""
        alerts = []
        
        if metrics.cpu_percent > 80:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            
        if metrics.memory_percent > 85:
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
            
        if metrics.disk_usage_percent > 90:
            alerts.append(f"High disk usage: {metrics.disk_usage_percent:.1f}%")
            
        if metrics.open_file_descriptors > 1000:
            alerts.append(f"High file descriptor usage: {metrics.open_file_descriptors}")
            
        for alert in alerts:
            self.logger.warning(f"System resource alert: {alert}")
            
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent metrics snapshot."""
        return self._metrics_history[-1] if self._metrics_history else None
        
    def get_metrics_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get summary statistics for the last N minutes."""
        if not self._metrics_history:
            return {"error": "No metrics available"}
            
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [
            m for m in self._metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": f"No metrics available for last {minutes} minutes"}
            
        return {
            "timeframe_minutes": minutes,
            "sample_count": len(recent_metrics),
            "cpu": {
                "avg_percent": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
                "max_percent": max(m.cpu_percent for m in recent_metrics),
                "min_percent": min(m.cpu_percent for m in recent_metrics)
            },
            "memory": {
                "avg_percent": sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
                "max_percent": max(m.memory_percent for m in recent_metrics),
                "current_used_mb": recent_metrics[-1].memory_used_mb,
                "current_available_mb": recent_metrics[-1].memory_available_mb
            },
            "disk": {
                "current_usage_percent": recent_metrics[-1].disk_usage_percent,
                "current_free_gb": recent_metrics[-1].disk_free_gb
            },
            "network": {
                "total_bytes_sent": recent_metrics[-1].network_bytes_sent,
                "total_bytes_recv": recent_metrics[-1].network_bytes_recv
            },
            "processes": {
                "current_count": recent_metrics[-1].process_count,
                "avg_count": sum(m.process_count for m in recent_metrics) / len(recent_metrics)
            }
        }
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status for health checks."""
        current = self.get_current_metrics()
        if not current:
            return {"status": "unknown", "reason": "No metrics available"}
            
        issues = []
        status = "healthy"
        
        if current.cpu_percent > 90:
            issues.append(f"Critical CPU usage: {current.cpu_percent:.1f}%")
            status = "critical"
        elif current.cpu_percent > 80:
            issues.append(f"High CPU usage: {current.cpu_percent:.1f}%")
            status = "warning" if status == "healthy" else status
            
        if current.memory_percent > 95:
            issues.append(f"Critical memory usage: {current.memory_percent:.1f}%")
            status = "critical"
        elif current.memory_percent > 85:
            issues.append(f"High memory usage: {current.memory_percent:.1f}%")
            status = "warning" if status == "healthy" else status
            
        if current.disk_usage_percent > 95:
            issues.append(f"Critical disk usage: {current.disk_usage_percent:.1f}%")
            status = "critical"
        elif current.disk_usage_percent > 90:
            issues.append(f"High disk usage: {current.disk_usage_percent:.1f}%")
            status = "warning" if status == "healthy" else status
            
        return {
            "status": status,
            "timestamp": current.timestamp,
            "issues": issues,
            "metrics": {
                "cpu_percent": current.cpu_percent,
                "memory_percent": current.memory_percent,
                "disk_usage_percent": current.disk_usage_percent,
                "process_count": current.process_count
            }
        }


# Global instance
system_metrics_monitor = SystemMetricsMonitor()
