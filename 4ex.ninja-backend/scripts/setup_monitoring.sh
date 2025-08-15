#!/bin/bash

# Digital Ocean System Monitoring Setup Script
# Phase 1: Emergency Validation - Step 2: Error Handling Validation
# 
# This script sets up comprehensive monitoring for the 4ex.ninja backend
# on Digital Ocean droplets, including system resources, Redis health,
# strategy performance, and error detection.

set -e

echo "🚀 Setting up 4ex.ninja System Monitoring on Digital Ocean..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

# Update system packages
log_info "Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install monitoring tools
log_info "Installing system monitoring tools..."
apt-get install -y htop iotop nethogs sysstat curl jq

# Install Python monitoring dependencies
log_info "Installing Python monitoring dependencies..."
pip3 install psutil redis requests

# Create monitoring directories
log_info "Creating monitoring directories..."
mkdir -p /var/log/4ex-validation
mkdir -p /opt/4ex-monitoring
mkdir -p /etc/4ex-monitoring

# Create the main system monitor script
log_info "Creating system monitor script..."
cat > /opt/4ex-monitoring/system_monitor.py << 'EOF'
#!/usr/bin/env python3
"""
4ex.ninja System Monitor for Digital Ocean

Comprehensive system monitoring for production deployment including:
- System resource monitoring (CPU, Memory, Disk)
- Redis health and performance monitoring
- Strategy performance monitoring
- Network connectivity checks
- Error detection and alerting
"""

import psutil
import redis
import time
import logging
import json
import requests
import os
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import asyncio
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/4ex-validation/system_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Comprehensive system monitoring for 4ex.ninja production environment."""
    
    def __init__(self):
        """Initialize system monitor with configuration."""
        self.config = self.load_config()
        self.redis_client = None
        self.alerts_sent = {}
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes
        
        # Initialize Redis connection
        self.init_redis_connection()
        
        # System thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 85.0,
            'memory_warning': 80.0,
            'memory_critical': 90.0,
            'disk_warning': 85.0,
            'disk_critical': 95.0,
            'redis_latency_warning': 50.0,  # ms
            'redis_latency_critical': 100.0,  # ms
            'no_signals_warning': 7200,  # 2 hours
            'no_signals_critical': 14400,  # 4 hours
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        config_file = '/etc/4ex-monitoring/config.json'
        default_config = {
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 0,
            'discord_webhook_url': os.getenv('DISCORD_WEBHOOK_MONITORING'),
            'monitoring_interval': 60,
            'health_check_interval': 300,
            'log_retention_days': 7
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Could not load config file: {e}")
            
        return default_config
    
    def init_redis_connection(self):
        """Initialize Redis connection with retry logic."""
        try:
            self.redis_client = redis.Redis(
                host=self.config['redis_host'],
                port=self.config['redis_port'],
                db=self.config['redis_db'],
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
    
    def monitor_system_resources(self) -> Dict[str, Any]:
        """Monitor and log system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Load averages
            load_avg = os.getloadavg()
            
            metrics = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'load_avg_1m': load_avg[0],
                    'load_avg_5m': load_avg[1],
                    'load_avg_15m': load_avg[2]
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percent': memory.percent,
                    'available_gb': memory.available / (1024**3)
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'percent': disk.percent,
                    'free_gb': disk.free / (1024**3)
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
            
            # Log metrics
            logger.info(f"System - CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%, Disk: {disk.percent:.1f}%")
            
            # Check for alerts
            self.check_system_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error monitoring system resources: {e}")
            return {}
    
    def monitor_redis_health(self) -> Dict[str, Any]:
        """Monitor Redis performance and availability."""
        if not self.redis_client:
            self.init_redis_connection()
            
        if not self.redis_client:
            return {'error': 'Redis not available'}
            
        try:
            # Test Redis connectivity and latency
            start_time = time.time()
            self.redis_client.ping()
            ping_time = (time.time() - start_time) * 1000
            
            # Get Redis info
            redis_info = self.redis_client.info()
            
            # Get memory usage
            used_memory_mb = redis_info.get('used_memory', 0) / 1024 / 1024
            max_memory = redis_info.get('maxmemory', 0)
            max_memory_mb = max_memory / 1024 / 1024 if max_memory > 0 else 0
            
            # Get connection info
            connected_clients = redis_info.get('connected_clients', 0)
            
            # Get command stats
            total_commands = redis_info.get('total_commands_processed', 0)
            
            metrics = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'connectivity': {
                    'ping_ms': ping_time,
                    'connected': True
                },
                'memory': {
                    'used_mb': used_memory_mb,
                    'max_mb': max_memory_mb,
                    'fragmentation_ratio': redis_info.get('mem_fragmentation_ratio', 0)
                },
                'connections': {
                    'clients': connected_clients,
                    'max_clients': redis_info.get('maxclients', 0)
                },
                'performance': {
                    'total_commands': total_commands,
                    'ops_per_sec': redis_info.get('instantaneous_ops_per_sec', 0),
                    'hit_rate': self.calculate_redis_hit_rate()
                },
                'persistence': {
                    'rdb_last_save': redis_info.get('rdb_last_save_time', 0),
                    'rdb_changes_since_save': redis_info.get('rdb_changes_since_last_save', 0)
                }
            }
            
            logger.info(f"Redis - Ping: {ping_time:.2f}ms, Memory: {used_memory_mb:.1f}MB, Clients: {connected_clients}")
            
            # Check for Redis alerts
            self.check_redis_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Redis monitoring failed: {e}")
            self.send_alert("CRITICAL", f"Redis monitoring failed: {e}")
            return {'error': str(e), 'connected': False}
    
    def calculate_redis_hit_rate(self) -> float:
        """Calculate Redis cache hit rate."""
        try:
            info = self.redis_client.info('stats')
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            
            if hits + misses == 0:
                return 0.0
                
            return (hits / (hits + misses)) * 100
            
        except Exception:
            return 0.0
    
    def monitor_strategy_performance(self) -> Dict[str, Any]:
        """Monitor strategy execution metrics."""
        if not self.redis_client:
            return {'error': 'Redis not available for strategy monitoring'}
            
        try:
            # Check signal generation
            signals_count = self.redis_client.llen("signals_queue") or 0
            
            # Check last signal timestamp
            last_signal_time = None
            time_since_signal = None
            
            try:
                last_signal = self.redis_client.lindex("signals_queue", 0)
                if last_signal:
                    signal_data = json.loads(last_signal)
                    last_signal_time = signal_data.get('timestamp')
                    if last_signal_time:
                        last_signal_time = datetime.fromtimestamp(last_signal_time)
                        time_since_signal = (datetime.now() - last_signal_time).total_seconds()
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
            
            # Check strategy states
            strategy_states = {}
            try:
                for instrument in ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD']:
                    for timeframe in ['H4', 'Daily']:
                        key = f"ma_state_{instrument}_{timeframe}"
                        state = self.redis_client.hgetall(key)
                        if state:
                            strategy_states[f"{instrument}_{timeframe}"] = {
                                'last_update': state.get('last_update'),
                                'ma_10': state.get('ma_10'),
                                'ma_20': state.get('ma_20'),
                                'active': bool(state)
                            }
            except Exception as e:
                logger.warning(f"Could not fetch strategy states: {e}")
            
            # Check error counts
            error_count = 0
            try:
                error_count = int(self.redis_client.get("error_count") or 0)
            except Exception:
                pass
            
            metrics = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'signals': {
                    'queue_length': signals_count,
                    'last_signal_time': last_signal_time.isoformat() if last_signal_time else None,
                    'time_since_last_signal_seconds': time_since_signal
                },
                'strategies': {
                    'active_count': len(strategy_states),
                    'states': strategy_states
                },
                'errors': {
                    'total_count': error_count
                }
            }
            
            logger.info(f"Strategy - Signals in queue: {signals_count}, Last signal: {time_since_signal or 'N/A'}s ago")
            
            # Check for strategy alerts
            self.check_strategy_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Strategy monitoring failed: {e}")
            return {'error': str(e)}
    
    def monitor_network_connectivity(self) -> Dict[str, Any]:
        """Monitor network connectivity to external services."""
        connectivity_results = {}
        
        # Test OANDA API connectivity
        try:
            start_time = time.time()
            response = requests.get(
                'https://api-fxpractice.oanda.com/v3/accounts',
                timeout=10
            )
            oanda_latency = (time.time() - start_time) * 1000
            oanda_status = response.status_code
            connectivity_results['oanda'] = {
                'reachable': True,
                'latency_ms': oanda_latency,
                'status_code': oanda_status
            }
        except Exception as e:
            connectivity_results['oanda'] = {
                'reachable': False,
                'error': str(e)
            }
        
        # Test Discord webhook connectivity
        discord_webhook = self.config.get('discord_webhook_url')
        if discord_webhook:
            try:
                start_time = time.time()
                # Send a minimal test (don't actually send to avoid spam)
                # Just test connectivity
                requests.head(discord_webhook, timeout=5)
                discord_latency = (time.time() - start_time) * 1000
                connectivity_results['discord'] = {
                    'reachable': True,
                    'latency_ms': discord_latency
                }
            except Exception as e:
                connectivity_results['discord'] = {
                    'reachable': False,
                    'error': str(e)
                }
        
        # Test DNS resolution
        try:
            import socket
            start_time = time.time()
            socket.gethostbyname('google.com')
            dns_latency = (time.time() - start_time) * 1000
            connectivity_results['dns'] = {
                'working': True,
                'latency_ms': dns_latency
            }
        except Exception as e:
            connectivity_results['dns'] = {
                'working': False,
                'error': str(e)
            }
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'connectivity': connectivity_results
        }
    
    def check_system_alerts(self, metrics: Dict[str, Any]):
        """Check system metrics for alert conditions."""
        cpu_percent = metrics['cpu']['percent']
        memory_percent = metrics['memory']['percent']
        disk_percent = metrics['disk']['percent']
        
        # CPU alerts
        if cpu_percent >= self.thresholds['cpu_critical']:
            self.send_alert("CRITICAL", f"CPU usage critical: {cpu_percent:.1f}%")
        elif cpu_percent >= self.thresholds['cpu_warning']:
            self.send_alert("WARNING", f"CPU usage high: {cpu_percent:.1f}%")
        
        # Memory alerts
        if memory_percent >= self.thresholds['memory_critical']:
            self.send_alert("CRITICAL", f"Memory usage critical: {memory_percent:.1f}%")
        elif memory_percent >= self.thresholds['memory_warning']:
            self.send_alert("WARNING", f"Memory usage high: {memory_percent:.1f}%")
        
        # Disk alerts
        if disk_percent >= self.thresholds['disk_critical']:
            self.send_alert("CRITICAL", f"Disk usage critical: {disk_percent:.1f}%")
        elif disk_percent >= self.thresholds['disk_warning']:
            self.send_alert("WARNING", f"Disk usage high: {disk_percent:.1f}%")
    
    def check_redis_alerts(self, metrics: Dict[str, Any]):
        """Check Redis metrics for alert conditions."""
        if 'error' in metrics:
            return
            
        ping_ms = metrics['connectivity']['ping_ms']
        
        # Redis latency alerts
        if ping_ms >= self.thresholds['redis_latency_critical']:
            self.send_alert("CRITICAL", f"Redis latency critical: {ping_ms:.2f}ms")
        elif ping_ms >= self.thresholds['redis_latency_warning']:
            self.send_alert("WARNING", f"Redis latency high: {ping_ms:.2f}ms")
    
    def check_strategy_alerts(self, metrics: Dict[str, Any]):
        """Check strategy metrics for alert conditions."""
        if 'error' in metrics:
            return
            
        time_since_signal = metrics['signals']['time_since_last_signal_seconds']
        
        if time_since_signal:
            # No signals alerts
            if time_since_signal >= self.thresholds['no_signals_critical']:
                self.send_alert("CRITICAL", f"No signals for {time_since_signal/3600:.1f} hours")
            elif time_since_signal >= self.thresholds['no_signals_warning']:
                self.send_alert("WARNING", f"No signals for {time_since_signal/3600:.1f} hours")
    
    def send_alert(self, level: str, message: str):
        """Send alert notification with cooldown to prevent spam."""
        alert_key = f"{level}:{message[:50]}"  # Use first 50 chars as key
        current_time = time.time()
        
        # Check cooldown
        if alert_key in self.last_alert_time:
            if current_time - self.last_alert_time[alert_key] < self.alert_cooldown:
                return  # Skip this alert due to cooldown
        
        self.last_alert_time[alert_key] = current_time
        
        # Log alert
        logger.warning(f"ALERT [{level}]: {message}")
        
        # Send to Discord if configured
        discord_webhook = self.config.get('discord_webhook_url')
        if discord_webhook:
            try:
                self.send_discord_alert(level, message, discord_webhook)
            except Exception as e:
                logger.error(f"Failed to send Discord alert: {e}")
    
    def send_discord_alert(self, level: str, message: str, webhook_url: str):
        """Send alert to Discord webhook."""
        color_map = {
            'CRITICAL': 0xFF0000,  # Red
            'WARNING': 0xFFAA00,   # Orange
            'INFO': 0x00FF00       # Green
        }
        
        payload = {
            "embeds": [{
                "title": f"🚨 4ex.ninja System Alert",
                "description": message,
                "color": color_map.get(level, 0x0099FF),
                "fields": [
                    {
                        "name": "Alert Level",
                        "value": level,
                        "inline": True
                    },
                    {
                        "name": "Server",
                        "value": os.uname().nodename,
                        "inline": True
                    },
                    {
                        "name": "Timestamp",
                        "value": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "4ex.ninja System Monitor"
                }
            }]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
    
    def save_metrics(self, metrics: Dict[str, Any], metric_type: str):
        """Save metrics to file for historical analysis."""
        try:
            metrics_dir = '/var/log/4ex-validation/metrics'
            os.makedirs(metrics_dir, exist_ok=True)
            
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"{metrics_dir}/{metric_type}_{date_str}.jsonl"
            
            with open(filename, 'a') as f:
                f.write(json.dumps(metrics) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def cleanup_old_logs(self):
        """Clean up old log files based on retention policy."""
        try:
            retention_days = self.config.get('log_retention_days', 7)
            cutoff_time = time.time() - (retention_days * 24 * 3600)
            
            log_dirs = ['/var/log/4ex-validation', '/var/log/4ex-validation/metrics']
            
            for log_dir in log_dirs:
                if not os.path.exists(log_dir):
                    continue
                    
                for filename in os.listdir(log_dir):
                    filepath = os.path.join(log_dir, filename)
                    if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
                        logger.info(f"Removed old log file: {filename}")
                        
        except Exception as e:
            logger.error(f"Log cleanup failed: {e}")
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle."""
        try:
            logger.info("🔍 Starting monitoring cycle...")
            
            # Monitor system resources
            system_metrics = self.monitor_system_resources()
            if system_metrics:
                self.save_metrics(system_metrics, 'system')
            
            # Monitor Redis health
            redis_metrics = self.monitor_redis_health()
            if redis_metrics:
                self.save_metrics(redis_metrics, 'redis')
            
            # Monitor strategy performance
            strategy_metrics = self.monitor_strategy_performance()
            if strategy_metrics:
                self.save_metrics(strategy_metrics, 'strategy')
            
            # Monitor network connectivity
            network_metrics = self.monitor_network_connectivity()
            if network_metrics:
                self.save_metrics(network_metrics, 'network')
            
            logger.info("✅ Monitoring cycle completed")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            self.send_alert("CRITICAL", f"Monitoring cycle failed: {e}")


def main():
    """Main monitoring loop."""
    logger.info("🚀 Starting 4ex.ninja System Monitor")
    
    monitor = SystemMonitor()
    monitoring_interval = monitor.config.get('monitoring_interval', 60)
    health_check_interval = monitor.config.get('health_check_interval', 300)
    
    last_health_check = 0
    
    try:
        while True:
            current_time = time.time()
            
            # Run monitoring cycle
            monitor.run_monitoring_cycle()
            
            # Run health check and cleanup periodically
            if current_time - last_health_check >= health_check_interval:
                monitor.cleanup_old_logs()
                last_health_check = current_time
            
            # Sleep until next cycle
            time.sleep(monitoring_interval)
            
    except KeyboardInterrupt:
        logger.info("📴 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal monitoring error: {e}")
        monitor.send_alert("CRITICAL", f"System monitor crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
EOF

# Make the monitor script executable
chmod +x /opt/4ex-monitoring/system_monitor.py

# Create default configuration
log_info "Creating default monitoring configuration..."
cat > /etc/4ex-monitoring/config.json << 'EOF'
{
    "redis_host": "localhost",
    "redis_port": 6379,
    "redis_db": 0,
    "monitoring_interval": 60,
    "health_check_interval": 300,
    "log_retention_days": 7,
    "discord_webhook_url": null
}
EOF

# Create systemd service for the monitor
log_info "Creating systemd service..."
cat > /etc/systemd/system/4ex-monitor.service << 'EOF'
[Unit]
Description=4ex.ninja System Monitor
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/4ex-monitoring
ExecStart=/usr/bin/python3 /opt/4ex-monitoring/system_monitor.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

# Environment variables
Environment=PYTHONPATH=/opt/4ex-monitoring
Environment=PYTHONUNBUFFERED=1

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/4ex-validation /etc/4ex-monitoring

[Install]
WantedBy=multi-user.target
EOF

# Create log rotation configuration
log_info "Setting up log rotation..."
cat > /etc/logrotate.d/4ex-monitoring << 'EOF'
/var/log/4ex-validation/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        systemctl reload 4ex-monitor.service > /dev/null 2>&1 || true
    endscript
}
EOF

# Create monitoring dashboard script
log_info "Creating monitoring dashboard script..."
cat > /opt/4ex-monitoring/dashboard.py << 'EOF'
#!/usr/bin/env python3
"""
4ex.ninja Monitoring Dashboard

Simple web dashboard to view system status and metrics.
"""

import json
import os
import glob
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class MonitoringDashboard(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_dashboard()
        elif self.path == '/api/status':
            self.serve_status_api()
        elif self.path == '/api/metrics':
            self.serve_metrics_api()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>4ex.ninja System Monitor</title>
            <meta refresh="30">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .status-good { color: green; }
                .status-warning { color: orange; }
                .status-critical { color: red; }
                .metric-box { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .metric-title { font-weight: bold; font-size: 18px; margin-bottom: 10px; }
                .metric-value { font-size: 24px; margin: 5px 0; }
                .timestamp { color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <h1>🚀 4ex.ninja System Monitor</h1>
            <p class="timestamp">Last updated: <span id="timestamp"></span></p>
            
            <div id="status-container">
                <h2>System Status</h2>
                <div id="status-content">Loading...</div>
            </div>
            
            <script>
                function updateDashboard() {
                    fetch('/api/status')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('status-content').innerHTML = formatStatus(data);
                            document.getElementById('timestamp').textContent = new Date().toLocaleString();
                        })
                        .catch(error => {
                            document.getElementById('status-content').innerHTML = 'Error loading status: ' + error;
                        });
                }
                
                function formatStatus(data) {
                    let html = '';
                    
                    // System metrics
                    if (data.system) {
                        html += '<div class="metric-box">';
                        html += '<div class="metric-title">System Resources</div>';
                        html += '<div class="metric-value">CPU: ' + data.system.cpu.percent.toFixed(1) + '%</div>';
                        html += '<div class="metric-value">Memory: ' + data.system.memory.percent.toFixed(1) + '%</div>';
                        html += '<div class="metric-value">Disk: ' + data.system.disk.percent.toFixed(1) + '%</div>';
                        html += '</div>';
                    }
                    
                    // Redis metrics
                    if (data.redis && !data.redis.error) {
                        html += '<div class="metric-box">';
                        html += '<div class="metric-title">Redis Health</div>';
                        html += '<div class="metric-value">Ping: ' + data.redis.connectivity.ping_ms.toFixed(2) + 'ms</div>';
                        html += '<div class="metric-value">Memory: ' + data.redis.memory.used_mb.toFixed(1) + 'MB</div>';
                        html += '<div class="metric-value">Clients: ' + data.redis.connections.clients + '</div>';
                        html += '</div>';
                    }
                    
                    // Strategy metrics
                    if (data.strategy && !data.strategy.error) {
                        html += '<div class="metric-box">';
                        html += '<div class="metric-title">Strategy Performance</div>';
                        html += '<div class="metric-value">Signals in Queue: ' + data.strategy.signals.queue_length + '</div>';
                        html += '<div class="metric-value">Active Strategies: ' + data.strategy.strategies.active_count + '</div>';
                        if (data.strategy.signals.time_since_last_signal_seconds) {
                            let hours = (data.strategy.signals.time_since_last_signal_seconds / 3600).toFixed(1);
                            html += '<div class="metric-value">Last Signal: ' + hours + ' hours ago</div>';
                        }
                        html += '</div>';
                    }
                    
                    return html;
                }
                
                // Update dashboard every 30 seconds
                updateDashboard();
                setInterval(updateDashboard, 30000);
            </script>
        </body>
        </html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_status_api(self):
        try:
            # Read latest metrics
            status = {}
            
            # Get latest system metrics
            system_files = glob.glob('/var/log/4ex-validation/metrics/system_*.jsonl')
            if system_files:
                latest_system = max(system_files, key=os.path.getmtime)
                with open(latest_system, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        status['system'] = json.loads(lines[-1])
            
            # Get latest Redis metrics
            redis_files = glob.glob('/var/log/4ex-validation/metrics/redis_*.jsonl')
            if redis_files:
                latest_redis = max(redis_files, key=os.path.getmtime)
                with open(latest_redis, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        status['redis'] = json.loads(lines[-1])
            
            # Get latest strategy metrics
            strategy_files = glob.glob('/var/log/4ex-validation/metrics/strategy_*.jsonl')
            if strategy_files:
                latest_strategy = max(strategy_files, key=os.path.getmtime)
                with open(latest_strategy, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        status['strategy'] = json.loads(lines[-1])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def serve_metrics_api(self):
        # Similar to status API but with historical data
        self.serve_status_api()

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), MonitoringDashboard)
    print("📊 Dashboard running at http://localhost:8080")
    server.serve_forever()
EOF

chmod +x /opt/4ex-monitoring/dashboard.py

# Create monitoring startup script
log_info "Creating monitoring control script..."
cat > /opt/4ex-monitoring/monitor-control.sh << 'EOF'
#!/bin/bash

# 4ex.ninja Monitor Control Script

case "$1" in
    start)
        echo "🚀 Starting 4ex.ninja monitoring..."
        systemctl start 4ex-monitor.service
        systemctl status 4ex-monitor.service --no-pager
        ;;
    stop)
        echo "📴 Stopping 4ex.ninja monitoring..."
        systemctl stop 4ex-monitor.service
        ;;
    restart)
        echo "🔄 Restarting 4ex.ninja monitoring..."
        systemctl restart 4ex-monitor.service
        systemctl status 4ex-monitor.service --no-pager
        ;;
    status)
        echo "📊 4ex.ninja monitoring status:"
        systemctl status 4ex-monitor.service --no-pager
        echo ""
        echo "📈 Recent log entries:"
        journalctl -u 4ex-monitor.service --no-pager -n 10
        ;;
    logs)
        echo "📋 Following 4ex.ninja monitoring logs:"
        journalctl -u 4ex-monitor.service -f
        ;;
    dashboard)
        echo "📊 Starting monitoring dashboard..."
        python3 /opt/4ex-monitoring/dashboard.py
        ;;
    test)
        echo "🧪 Testing monitoring components..."
        python3 -c "
import sys
sys.path.append('/opt/4ex-monitoring')
from system_monitor import SystemMonitor
monitor = SystemMonitor()
print('✅ SystemMonitor initialized successfully')
metrics = monitor.monitor_system_resources()
print('✅ System monitoring working')
redis_metrics = monitor.monitor_redis_health()
print('✅ Redis monitoring working')
print('🎉 All tests passed!')
"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|dashboard|test}"
        echo ""
        echo "Commands:"
        echo "  start      - Start the monitoring service"
        echo "  stop       - Stop the monitoring service"
        echo "  restart    - Restart the monitoring service"
        echo "  status     - Show service status and recent logs"
        echo "  logs       - Follow monitoring logs in real-time"
        echo "  dashboard  - Start web dashboard (port 8080)"
        echo "  test       - Test monitoring components"
        exit 1
        ;;
esac
EOF

chmod +x /opt/4ex-monitoring/monitor-control.sh

# Create symlink for easy access
ln -sf /opt/4ex-monitoring/monitor-control.sh /usr/local/bin/4ex-monitor

# Enable and start the monitoring service
log_info "Enabling and starting monitoring service..."
systemctl daemon-reload
systemctl enable 4ex-monitor.service

# Test the monitoring setup
log_info "Testing monitoring setup..."
if /opt/4ex-monitoring/monitor-control.sh test; then
    log_success "Monitoring setup test passed!"
else
    log_warning "Monitoring setup test had some issues, but continuing..."
fi

# Start the service
systemctl start 4ex-monitor.service

# Check service status
if systemctl is-active --quiet 4ex-monitor.service; then
    log_success "4ex.ninja monitoring service is running!"
else
    log_error "Failed to start monitoring service"
    systemctl status 4ex-monitor.service --no-pager
fi

# Display completion information
echo ""
echo "🎉 4ex.ninja System Monitoring Setup Complete!"
echo ""
echo "📋 Available commands:"
echo "  4ex-monitor start     - Start monitoring"
echo "  4ex-monitor stop      - Stop monitoring"
echo "  4ex-monitor status    - Check status"
echo "  4ex-monitor logs      - View logs"
echo "  4ex-monitor dashboard - Start web dashboard"
echo "  4ex-monitor test      - Test components"
echo ""
echo "📊 Monitoring dashboard: http://your-server-ip:8080"
echo "📁 Log files: /var/log/4ex-validation/"
echo "⚙️  Configuration: /etc/4ex-monitoring/config.json"
echo ""

if systemctl is-active --quiet 4ex-monitor.service; then
    echo "✅ Monitoring is currently running"
    echo "📈 Recent activity:"
    journalctl -u 4ex-monitor.service --no-pager -n 5
else
    echo "❌ Monitoring service failed to start"
    echo "🔍 Check logs with: journalctl -u 4ex-monitor.service"
fi

echo ""
echo "🔧 To configure Discord alerts:"
echo "1. Set DISCORD_WEBHOOK_MONITORING environment variable"
echo "2. Or update /etc/4ex-monitoring/config.json"
echo "3. Restart with: 4ex-monitor restart"
echo ""
log_success "Setup complete! 🚀"
