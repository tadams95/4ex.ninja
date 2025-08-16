#!/bin/bash

# Phase 2 Backend Monitoring API Deployment Script
# Deploy to Digital Ocean Droplet: 157.230.58.248

set -e

DROPLET_IP="157.230.58.248"
DROPLET_USER="root"
PROJECT_PATH="/var/www/4ex.ninja/4ex.ninja-backend"

echo "🚀 Deploying Phase 2 Backend Monitoring API to droplet..."
echo "Target: $DROPLET_USER@$DROPLET_IP"
echo ""

# 1. Create monitoring directory structure on droplet
echo "📁 Creating monitoring directory structure..."
ssh $DROPLET_USER@$DROPLET_IP "mkdir -p $PROJECT_PATH/src/monitoring"

# 2. Check if monitoring files exist locally (they need to be created first)
if [ ! -d "4ex.ninja-backend/src/monitoring" ]; then
    echo "⚠️  Monitoring directory doesn't exist locally yet."
    echo "    The Phase 2 monitoring files need to be created first."
    echo "    Creating placeholder structure..."
    
    # Create local monitoring directory for future development
    mkdir -p 4ex.ninja-backend/src/monitoring
    
    # Create placeholder files to indicate what needs to be implemented
    cat > 4ex.ninja-backend/src/monitoring/README.md << 'EOF'
# Phase 2 Backend Monitoring API

## Files to Implement:
- dashboard_api.py - Main FastAPI application for monitoring endpoints
- regime_monitor.py - Real-time regime detection monitoring
- performance_tracker.py - Strategy performance tracking
- alert_system.py - Regime change alert system

## Deployment Status:
- Directory structure created on droplet: ✅
- Supervisor configuration ready: ✅
- Files pending implementation: ⏳

## Next Steps:
1. Implement the monitoring API files
2. Run this deployment script again
3. Start the monitoring service
EOF

    echo "📝 Created monitoring directory with implementation guide"
fi

# 3. Deploy any existing monitoring files
echo "📤 Deploying monitoring files..."
if [ -f "4ex.ninja-backend/src/monitoring/dashboard_api.py" ]; then
    scp 4ex.ninja-backend/src/monitoring/dashboard_api.py $DROPLET_USER@$DROPLET_IP:$PROJECT_PATH/src/monitoring/
    echo "  ✅ dashboard_api.py deployed"
else
    echo "  ⏳ dashboard_api.py - pending implementation"
fi

if [ -f "4ex.ninja-backend/src/monitoring/regime_monitor.py" ]; then
    scp 4ex.ninja-backend/src/monitoring/regime_monitor.py $DROPLET_USER@$DROPLET_IP:$PROJECT_PATH/src/monitoring/
    echo "  ✅ regime_monitor.py deployed"
else
    echo "  ⏳ regime_monitor.py - pending implementation"
fi

if [ -f "4ex.ninja-backend/src/monitoring/performance_tracker.py" ]; then
    scp 4ex.ninja-backend/src/monitoring/performance_tracker.py $DROPLET_USER@$DROPLET_IP:$PROJECT_PATH/src/monitoring/
    echo "  ✅ performance_tracker.py deployed"
else
    echo "  ⏳ performance_tracker.py - pending implementation"
fi

if [ -f "4ex.ninja-backend/src/monitoring/alert_system.py" ]; then
    scp 4ex.ninja-backend/src/monitoring/alert_system.py $DROPLET_USER@$DROPLET_IP:$PROJECT_PATH/src/monitoring/
    echo "  ✅ alert_system.py deployed"
else
    echo "  ⏳ alert_system.py - pending implementation"
fi

# Deploy README if it exists
if [ -f "4ex.ninja-backend/src/monitoring/README.md" ]; then
    scp 4ex.ninja-backend/src/monitoring/README.md $DROPLET_USER@$DROPLET_IP:$PROJECT_PATH/src/monitoring/
fi

# 4. Create Supervisor configuration for monitoring API
echo "⚙️  Setting up Supervisor configuration..."
ssh $DROPLET_USER@$DROPLET_IP << 'EOF'
cat > /etc/supervisor/conf.d/4ex-monitoring-api.conf << 'SUPERVISOR_EOF'
[program:4ex-monitoring-api]
command=/var/www/4ex.ninja/venv/bin/python -m uvicorn src.monitoring.dashboard_api:app --host 0.0.0.0 --port 8081
directory=/var/www/4ex.ninja/4ex.ninja-backend
user=4ex
autostart=true
autorestart=true
stdout_logfile=/var/log/4ex-ninja/monitoring_api.log
stderr_logfile=/var/log/4ex-ninja/monitoring_api_error.log
environment=PATH="/var/www/4ex.ninja/venv/bin"
SUPERVISOR_EOF

# Create log directory if it doesn't exist
mkdir -p /var/log/4ex-ninja
chown 4ex:4ex /var/log/4ex-ninja

echo "✅ Supervisor configuration created"
EOF

# 5. Update supervisor and check status
echo "🔄 Updating Supervisor..."
ssh $DROPLET_USER@$DROPLET_IP << 'EOF'
supervisorctl reread
supervisorctl update
echo "📊 Current supervisor status:"
supervisorctl status
EOF

# 6. Create nginx configuration for monitoring API (optional)
echo "🌐 Setting up Nginx proxy for monitoring API..."
ssh $DROPLET_USER@$DROPLET_IP << 'EOF'
cat > /etc/nginx/sites-available/4ex-monitoring << 'NGINX_EOF'
server {
    listen 80;
    server_name monitoring.4ex.ninja;
    
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for real-time updates
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINX_EOF

# Enable the site (optional - requires domain setup)
# ln -sf /etc/nginx/sites-available/4ex-monitoring /etc/nginx/sites-enabled/
# nginx -t && systemctl reload nginx

echo "🌐 Nginx configuration created (not enabled yet)"
echo "   To enable: ln -sf /etc/nginx/sites-available/4ex-monitoring /etc/nginx/sites-enabled/"
EOF

echo ""
echo "🎉 Phase 2 Monitoring API Deployment Complete!"
echo ""
echo "📍 Access Points:"
echo "   • System Monitoring: http://157.230.58.248:8080"
echo "   • Phase 2 API: http://157.230.58.248:8081 (when implemented)"
echo ""
echo "📊 Status Check:"
echo "   ssh root@157.230.58.248 'supervisorctl status'"
echo ""
echo "📝 Next Steps:"
echo "   1. Implement the monitoring API files"
echo "   2. Run: supervisorctl start 4ex-monitoring-api"
echo "   3. Check logs: tail -f /var/log/4ex-ninja/monitoring_api.log"
