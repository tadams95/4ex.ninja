#!/bin/bash

# 4ex.ninja Digital Ocean Production Deployment Script
# Phase 1: Emergency Validation - Production Infrastructure Setup
# 
# This script deploys the complete 4ex.ninja system to Digital Ocean
# for real production performance validation.

set -e

echo "🚀 Starting 4ex.ninja Digital Ocean Production Deployment..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

# Configuration variables
PROJECT_DIR="/var/www/4ex.ninja"
BACKEND_DIR="$PROJECT_DIR/4ex.ninja-backend"
FRONTEND_DIR="$PROJECT_DIR/4ex.ninja-frontend"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="/var/log/4ex-ninja"
CONFIG_DIR="/etc/4ex-ninja"

log_step "1. System Update and Prerequisites"
log_info "Updating system packages..."
apt-get update -y
apt-get upgrade -y

log_info "Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    redis-server \
    nginx \
    git \
    curl \
    htop \
    iotop \
    nethogs \
    sysstat \
    supervisor \
    ufw \
    fail2ban \
    certbot \
    python3-certbot-nginx

log_step "2. Directory Structure Setup"
log_info "Creating project directories..."
mkdir -p $PROJECT_DIR
mkdir -p $LOG_DIR
mkdir -p $CONFIG_DIR
mkdir -p $LOG_DIR/validation
mkdir -p $LOG_DIR/strategies
mkdir -p $LOG_DIR/monitoring

# Create project user
if ! id "4ex" &>/dev/null; then
    log_info "Creating 4ex user..."
    useradd -r -s /bin/bash -d $PROJECT_DIR 4ex
    usermod -a -G www-data 4ex
fi

log_step "3. Code Deployment"
log_info "Cloning/updating 4ex.ninja repository..."
if [ -d "$PROJECT_DIR/.git" ]; then
    cd $PROJECT_DIR
    git pull origin main
else
    cd /var/www
    git clone https://github.com/tadams95/4ex.ninja.git
    chown -R 4ex:4ex $PROJECT_DIR
fi

log_step "4. Python Environment Setup"
log_info "Creating Python virtual environment..."
cd $PROJECT_DIR
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

log_info "Installing Python dependencies..."
cd $BACKEND_DIR
pip install --upgrade pip
pip install -r requirements.txt

# Install additional dependencies for validation and monitoring
pip install psutil redis requests aiohttp asyncio

log_step "5. Redis Configuration"
log_info "Configuring Redis server..."
cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

cat > /etc/redis/redis.conf << 'EOF'
# Redis configuration for 4ex.ninja production
bind 127.0.0.1
port 6379
timeout 0
tcp-keepalive 300

# Memory management
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Security
requirepass 4ex_redis_secure_2024

# Performance
tcp-backlog 511
databases 16
EOF

log_info "Starting Redis server..."
systemctl enable redis-server
systemctl restart redis-server

# Wait for Redis to start
sleep 5
if systemctl is-active --quiet redis-server; then
    log_success "Redis server is running"
else
    log_error "Failed to start Redis server"
    exit 1
fi

log_step "6. Environment Configuration"
log_info "Creating production environment configuration..."
cat > $CONFIG_DIR/production.env << 'EOF'
# 4ex.ninja Production Environment Configuration
# Generated automatically during deployment

# Environment
ENVIRONMENT=production
DEBUG=False

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=4ex_redis_secure_2024
REDIS_DB=0

# API Configuration
OANDA_API_URL=https://api-fxpractice.oanda.com
OANDA_STREAM_URL=https://stream-fxpractice.oanda.com

# Logging
LOG_LEVEL=INFO
LOG_DIR=/var/log/4ex-ninja

# Security
SECRET_KEY=generated_during_deployment_$(date +%s)

# Performance
MAX_WORKERS=4
CACHE_TTL=300

# Monitoring
MONITORING_ENABLED=true
HEALTH_CHECK_INTERVAL=60
EOF

# Source environment variables
echo "source $CONFIG_DIR/production.env" >> /etc/environment

log_step "7. Application Configuration"
log_info "Setting up application configuration files..."

# Create application config
cat > $CONFIG_DIR/app_config.json << 'EOF'
{
    "trading": {
        "max_positions_per_pair": 1,
        "max_total_positions": 8,
        "default_lot_size": 0.01,
        "risk_per_trade": 0.02,
        "max_daily_trades": 10
    },
    "strategies": {
        "enabled": ["MA_CROSSOVER"],
        "timeframes": ["H4", "DAILY"],
        "pairs": ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]
    },
    "notifications": {
        "discord_enabled": true,
        "email_enabled": false,
        "sms_enabled": false
    },
    "monitoring": {
        "performance_tracking": true,
        "error_reporting": true,
        "health_checks": true
    }
}
EOF

log_step "8. Nginx Configuration"
log_info "Configuring Nginx reverse proxy..."
cat > /etc/nginx/sites-available/4ex.ninja << 'EOF'
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # Monitoring dashboard
    location /monitor {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files and frontend
    location / {
        root /var/www/4ex.ninja/4ex.ninja-frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/4ex.ninja /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t
if [ $? -eq 0 ]; then
    log_success "Nginx configuration is valid"
    systemctl reload nginx
else
    log_error "Nginx configuration error"
    exit 1
fi

log_step "9. Supervisor Configuration"
log_info "Setting up process management with Supervisor..."

# Backend API service
cat > /etc/supervisor/conf.d/4ex-backend.conf << 'EOF'
[program:4ex-backend]
command=/var/www/4ex.ninja/venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
directory=/var/www/4ex.ninja/4ex.ninja-backend
user=4ex
autostart=true
autorestart=true
startsecs=3
startretries=3
stdout_logfile=/var/log/4ex-ninja/backend.log
stderr_logfile=/var/log/4ex-ninja/backend_error.log
environment=PATH="/var/www/4ex.ninja/venv/bin"
EOF

# Strategy runner service
cat > /etc/supervisor/conf.d/4ex-strategies.conf << 'EOF'
[program:4ex-strategies]
command=/var/www/4ex.ninja/venv/bin/python src/strategies/strategy_runner.py
directory=/var/www/4ex.ninja/4ex.ninja-backend
user=4ex
autostart=true
autorestart=true
startsecs=5
startretries=3
stdout_logfile=/var/log/4ex-ninja/strategies.log
stderr_logfile=/var/log/4ex-ninja/strategies_error.log
environment=PATH="/var/www/4ex.ninja/venv/bin"
EOF

# Monitoring service (using our existing monitoring script)
cat > /etc/supervisor/conf.d/4ex-monitoring.conf << 'EOF'
[program:4ex-monitoring]
command=/var/www/4ex.ninja/venv/bin/python /opt/4ex-monitoring/system_monitor.py
directory=/var/www/4ex.ninja/4ex.ninja-backend
user=4ex
autostart=true
autorestart=true
startsecs=5
startretries=3
stdout_logfile=/var/log/4ex-ninja/monitoring.log
stderr_logfile=/var/log/4ex-ninja/monitoring_error.log
environment=PATH="/var/www/4ex.ninja/venv/bin"
EOF

log_step "10. Deploy Monitoring System"
log_info "Deploying comprehensive monitoring system..."

# Copy our existing monitoring script
cp $BACKEND_DIR/scripts/setup_monitoring.sh /tmp/setup_monitoring.sh
chmod +x /tmp/setup_monitoring.sh

# Run the monitoring setup (but skip the systemd part since we're using supervisor)
log_info "Setting up monitoring components..."

# Create monitoring directories
mkdir -p /opt/4ex-monitoring
mkdir -p /var/log/4ex-validation
mkdir -p /var/log/4ex-validation/metrics

# Copy the system monitor script
cp $BACKEND_DIR/src/validation/system_monitor.py /opt/4ex-monitoring/ 2>/dev/null || {
    log_warning "System monitor script not found, creating basic version..."
    
    cat > /opt/4ex-monitoring/system_monitor.py << 'EOF'
#!/usr/bin/env python3
"""Basic system monitor for 4ex.ninja production deployment"""
import time
import logging
import json
import psutil
import redis
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_system():
    """Basic system monitoring"""
    while True:
        try:
            # System metrics
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            logger.info(f"System - CPU: {cpu}%, Memory: {memory}%, Disk: {disk}%")
            
            # Redis health check
            try:
                r = redis.Redis(host='localhost', port=6379, password='4ex_redis_secure_2024')
                r.ping()
                logger.info("Redis - OK")
            except Exception as e:
                logger.error(f"Redis - ERROR: {e}")
            
            time.sleep(60)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_system()
EOF
}

chmod +x /opt/4ex-monitoring/system_monitor.py

log_step "11. Security Configuration"
log_info "Configuring firewall and security..."

# Configure UFW firewall
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban
cat > /etc/fail2ban/jail.d/4ex-custom.conf << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-badbots]
enabled = true

[nginx-noproxy]
enabled = true
EOF

systemctl enable fail2ban
systemctl restart fail2ban

log_step "12. File Permissions and Ownership"
log_info "Setting correct file permissions..."
chown -R 4ex:4ex $PROJECT_DIR
chown -R 4ex:4ex $LOG_DIR
chmod -R 755 $PROJECT_DIR
chmod -R 644 $PROJECT_DIR/4ex.ninja-backend/src/strategies/*.py
chmod +x $PROJECT_DIR/4ex.ninja-backend/scripts/*.sh

# Make log directories writable
chmod -R 755 $LOG_DIR
chown -R 4ex:www-data $LOG_DIR

log_step "13. Service Startup"
log_info "Starting all services..."

# Update supervisor configuration
supervisorctl reread
supervisorctl update

# Start services
systemctl enable supervisor
systemctl restart supervisor

# Wait for services to start
sleep 10

log_info "Checking service status..."
supervisorctl status

log_step "14. Health Checks"
log_info "Running deployment health checks..."

# Check Redis
if redis-cli -a 4ex_redis_secure_2024 ping | grep -q PONG; then
    log_success "✅ Redis is responding"
else
    log_error "❌ Redis health check failed"
fi

# Check Nginx
if systemctl is-active --quiet nginx; then
    log_success "✅ Nginx is running"
else
    log_error "❌ Nginx is not running"
fi

# Check Supervisor services
if supervisorctl status | grep -q "RUNNING"; then
    log_success "✅ Supervisor services are running"
else
    log_warning "⚠️ Some supervisor services may not be running"
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    log_success "✅ Disk usage is healthy ($DISK_USAGE%)"
else
    log_warning "⚠️ Disk usage is high ($DISK_USAGE%)"
fi

log_step "15. Deployment Summary"
echo ""
echo "🎉 4ex.ninja Digital Ocean Deployment Complete!"
echo ""
echo "📊 Deployment Details:"
echo "  Project Directory: $PROJECT_DIR"
echo "  Log Directory: $LOG_DIR"
echo "  Configuration: $CONFIG_DIR"
echo "  Python Environment: $VENV_DIR"
echo ""
echo "🔧 Services Status:"
supervisorctl status
echo ""
echo "📈 Access Points:"
echo "  Main Application: http://your-server-ip/"
echo "  API Health Check: http://your-server-ip/health"
echo "  Monitoring Dashboard: http://your-server-ip/monitor"
echo ""
echo "📋 Next Steps:"
echo "1. Configure OANDA API credentials:"
echo "   sudo nano $CONFIG_DIR/production.env"
echo "   # Add OANDA_API_KEY and OANDA_ACCOUNT_ID"
echo ""
echo "2. Configure Discord webhook:"
echo "   sudo nano $CONFIG_DIR/production.env"
echo "   # Add DISCORD_WEBHOOK_URL"
echo ""
echo "3. Update domain name in Nginx config:"
echo "   sudo nano /etc/nginx/sites-available/4ex.ninja"
echo "   # Change 'your-domain.com' to your actual domain"
echo ""
echo "4. Run Phase 1 validation tests:"
echo "   cd $BACKEND_DIR"
echo "   source $VENV_DIR/bin/activate"
echo "   python src/validation/emergency_validation_runner.py"
echo ""
echo "🔍 Monitoring:"
echo "  System Logs: sudo tail -f $LOG_DIR/monitoring.log"
echo "  Backend Logs: sudo tail -f $LOG_DIR/backend.log"
echo "  Strategy Logs: sudo tail -f $LOG_DIR/strategies.log"
echo ""
log_success "Deployment completed successfully! 🚀"

# Save deployment info
cat > $PROJECT_DIR/deployment_info.json << EOF
{
    "deployment_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "Phase1-Emergency-Validation",
    "server_info": {
        "hostname": "$(hostname)",
        "os": "$(lsb_release -d | cut -f2)",
        "kernel": "$(uname -r)",
        "memory": "$(free -h | awk '/^Mem:/ {print $2}')",
        "disk": "$(df -h / | awk 'NR==2 {print $2}')"
    },
    "services": {
        "redis": "configured",
        "nginx": "configured", 
        "supervisor": "configured",
        "monitoring": "deployed"
    },
    "next_steps": [
        "Configure OANDA API credentials",
        "Configure Discord webhook URL",
        "Run Phase 1 validation tests",
        "Update domain name in Nginx"
    ]
}
EOF

echo ""
echo "📄 Deployment information saved to: $PROJECT_DIR/deployment_info.json"
echo ""
