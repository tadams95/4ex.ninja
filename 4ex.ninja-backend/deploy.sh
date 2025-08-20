#!/bin/bash

# Clean Backend Deployment Script
# Deploys the clean, production-focused backend to Digital Ocean droplet

set -e

echo "🚀 Starting Clean Backend Deployment..."

# Configuration
DROPLET_IP="165.227.5.89"
DROPLET_USER="root"
BACKEND_DIR="/opt/4ex-ninja-backend"
SERVICE_NAME="4ex-ninja-backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we can connect to the droplet
print_status "Checking connection to droplet..."
if ! ssh -o ConnectTimeout=10 $DROPLET_USER@$DROPLET_IP "echo 'Connection successful'" > /dev/null 2>&1; then
    print_error "Cannot connect to droplet at $DROPLET_IP"
    exit 1
fi

print_status "Connection to droplet successful"

# Create deployment package
print_status "Creating deployment package..."
cd "$(dirname "$0")"

# Create temporary directory for clean files
TEMP_DIR=$(mktemp -d)
cp -r . "$TEMP_DIR/4ex-ninja-backend-clean"
cd "$TEMP_DIR"

# Create tarball
tar -czf backend-clean.tar.gz 4ex-ninja-backend-clean/

print_status "Deployment package created"

# Upload to droplet
print_status "Uploading backend to droplet..."
scp backend-clean.tar.gz $DROPLET_USER@$DROPLET_IP:/tmp/

# Deploy on droplet
print_status "Deploying on droplet..."
ssh $DROPLET_USER@$DROPLET_IP << 'EOF'
    set -e
    
    # Stop existing service if running
    if systemctl is-active --quiet 4ex-ninja-backend; then
        echo "Stopping existing service..."
        systemctl stop 4ex-ninja-backend
    fi
    
    # Backup existing deployment if it exists
    if [ -d "/opt/4ex-ninja-backend" ]; then
        echo "Backing up existing deployment..."
        mv /opt/4ex-ninja-backend /opt/4ex-ninja-backend.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Extract new deployment
    echo "Extracting new deployment..."
    cd /tmp
    tar -xzf backend-clean.tar.gz
    
    # Move to final location
    mv 4ex-ninja-backend-clean /opt/4ex-ninja-backend
    cd /opt/4ex-ninja-backend
    
    # Create and activate virtual environment
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies in virtual environment
    echo "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create environment file
    echo "Creating environment configuration..."
    cat > .env << 'ENVEOF'
ENVIRONMENT=production
MONGODB_URL=mongodb://localhost:27017/4ex_ninja
DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL:-}
OANDA_API_KEY=${OANDA_API_KEY:-}
OANDA_ACCOUNT_ID=${OANDA_ACCOUNT_ID:-}
REDIS_URL=redis://localhost:6379
ENVEOF

    # Create systemd service
    echo "Creating systemd service..."
    cat > /etc/systemd/system/4ex-ninja-backend.service << 'SERVICEEOF'
[Unit]
Description=4ex.ninja Clean Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/4ex-ninja-backend
Environment=PATH=/opt/4ex-ninja-backend/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/opt/4ex-ninja-backend/venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

    # Reload systemd and start service
    echo "Starting service..."
    systemctl daemon-reload
    systemctl enable 4ex-ninja-backend
    systemctl start 4ex-ninja-backend
    
    # Wait a moment for service to start
    sleep 3
    
    # Check service status
    echo "Checking service status..."
    systemctl status 4ex-ninja-backend --no-pager -l
    
    echo "Deployment completed!"
EOF

# Cleanup
rm -rf "$TEMP_DIR"

# Test deployment
print_status "Testing deployment..."
sleep 5

if curl -s "http://$DROPLET_IP:8000/health" > /dev/null; then
    print_status "✅ Deployment successful! Backend is responding"
    print_status "🌐 Backend URL: http://$DROPLET_IP:8000"
    print_status "📊 Health Check: http://$DROPLET_IP:8000/health"
    print_status "⚙️  Strategy Config: http://$DROPLET_IP:8000/strategy/config"
else
    print_warning "❌ Backend may not be responding yet. Check logs on droplet:"
    print_warning "   ssh $DROPLET_USER@$DROPLET_IP"
    print_warning "   journalctl -u 4ex-ninja-backend -f"
fi

echo ""
print_status "🎉 Clean Backend Deployment Complete!"
print_status "Next steps:"
print_status "1. Verify optimal MA strategy configuration"
print_status "2. Test signal generation endpoints"
print_status "3. Monitor performance metrics"
