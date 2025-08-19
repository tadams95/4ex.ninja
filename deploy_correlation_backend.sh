#!/bin/bash

# Deploy Updated Backend with Correlation Trend Analysis
# This script deploys our latest backend code to the Digital Ocean droplet

set -e

echo "🚀 DEPLOYING UPDATED BACKEND WITH CORRELATION TRENDS"
echo "====================================================="

DROPLET_IP="157.230.58.248"
BACKEND_DIR="/var/www/4ex.ninja/4ex.ninja-backend"
LOCAL_BACKEND="./4ex.ninja-backend"

echo "📋 Pre-deployment checks..."

# Check if local backend exists
if [ ! -d "$LOCAL_BACKEND" ]; then
    echo "❌ Local backend directory not found: $LOCAL_BACKEND"
    exit 1
fi

# Check for key files
if [ ! -f "$LOCAL_BACKEND/src/api/routes/risk.py" ]; then
    echo "❌ Risk API routes not found in local backend"
    exit 1
fi

if [ ! -f "$LOCAL_BACKEND/src/risk/correlation_trends.py" ]; then
    echo "❌ Correlation trends module not found in local backend"
    exit 1
fi

echo "✅ Local backend files verified"

# Test SSH connection
ssh -o ConnectTimeout=10 root@$DROPLET_IP 'echo "SSH connection verified"'

echo "🛑 Stopping current backend service..."
ssh root@$DROPLET_IP "systemctl stop 4ex-backend.service"

echo "📦 Creating backup of current deployment..."
ssh root@$DROPLET_IP "
cd /var/www/4ex.ninja
cp -r 4ex.ninja-backend 4ex.ninja-backend.backup.$(date +%Y%m%d_%H%M%S)
echo 'Backup created'
"

echo "🔄 Syncing updated backend code..."
rsync -avz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='logs/' \
    --exclude='*.log' \
    --exclude='venv/' \
    $LOCAL_BACKEND/ root@$DROPLET_IP:$BACKEND_DIR/

echo "📋 Installing updated dependencies..."
ssh root@$DROPLET_IP "
cd $BACKEND_DIR
/var/www/4ex.ninja/venv/bin/pip install -r requirements.txt
echo 'Dependencies updated'
"

echo "🔄 Updating systemd service configuration..."
ssh root@$DROPLET_IP "
# Update the service to use the correct working directory and PYTHONPATH
cat > /etc/systemd/system/4ex-backend.service << EOF
[Unit]
Description=4ex.ninja Backend Service with Correlation Trend Analysis
After=network.target

[Service]
Type=simple
User=fourex
WorkingDirectory=$BACKEND_DIR/src
Environment=PATH=/var/www/4ex.ninja/venv/bin
Environment=PYTHONPATH=$BACKEND_DIR/src:$BACKEND_DIR
ExecStart=/var/www/4ex.ninja/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo 'Service configuration updated'
"

echo "🚀 Starting updated backend service..."
ssh root@$DROPLET_IP "systemctl start 4ex-backend.service"

echo "⏳ Waiting for service to start..."
sleep 5

echo "✅ Verifying deployment..."
ssh root@$DROPLET_IP "systemctl status 4ex-backend.service --no-pager"

echo ""
echo "🔍 Testing correlation trend endpoints..."
python3 -c "
import requests
import time

# Give the service a moment to fully start
time.sleep(3)

droplet_url = 'http://$DROPLET_IP:8000'

try:
    # Test health endpoint
    response = requests.get(f'{droplet_url}/health', timeout=10)
    print(f'Health check: {response.status_code}')
    
    # Test correlation trends endpoint
    response = requests.get(f'{droplet_url}/api/risk/correlation-trends?hours=24', timeout=10)
    print(f'Correlation trends: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print(f'✅ Correlation trends working! Got {len(data.get(\"trends\", []))} trends')
    else:
        print(f'❌ Correlation trends failed: {response.text[:200]}')
        
except Exception as e:
    print(f'❌ Testing failed: {e}')
"

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================="
echo "✅ Updated backend deployed with correlation trend analysis"
echo "✅ Service running on port 8000"
echo "📊 Correlation trends API available at: http://$DROPLET_IP:8000/api/risk/correlation-trends"
