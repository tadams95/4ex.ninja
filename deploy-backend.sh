#!/bin/bash

# 4ex.ninja Backend Deployment Script for Digital Ocean
# This script deploys the backend to run alongside existing infrastructure

set -e

echo "🚀 Deploying 4ex.ninja Backend to Digital Ocean..."

# Configuration
BACKEND_PORT=8000
APP_DIR="/opt/4ex-ninja-backend"
SERVICE_NAME="4ex-ninja-backend"

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy backend files
echo "📦 Copying backend files..."
rsync -av --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='logs/' \
    --exclude='backtest_results/' \
    ./4ex.ninja-backend/ $APP_DIR/

# Install Python dependencies
echo "📋 Installing Python dependencies..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=4ex.ninja Trading Platform Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR/src
Environment=PATH=$APP_DIR/venv/bin
Environment=PYTHONPATH=$APP_DIR/src
ExecStart=$APP_DIR/venv/bin/uvicorn app:app --host 0.0.0.0 --port $BACKEND_PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🔄 Starting backend service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

# Configure firewall (if ufw is active)
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    echo "🔒 Configuring firewall..."
    sudo ufw allow $BACKEND_PORT/tcp
fi

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Check service status
echo "✅ Checking service status..."
sudo systemctl status $SERVICE_NAME --no-pager

# Test the API
echo "🧪 Testing API endpoints..."
if curl -f http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
fi

if curl -f http://localhost:$BACKEND_PORT/api/risk/var-summary > /dev/null 2>&1; then
    echo "✅ VaR API endpoint accessible"
else
    echo "❌ VaR API endpoint failed"
fi

echo ""
echo "🎉 Deployment complete!"
echo "Backend is running on: http://157.230.58.248:$BACKEND_PORT"
echo ""
echo "API Endpoints:"
echo "  Health: http://157.230.58.248:$BACKEND_PORT/health"
echo "  VaR Summary: http://157.230.58.248:$BACKEND_PORT/api/risk/var-summary"
echo "  Correlation Matrix: http://157.230.58.248:$BACKEND_PORT/api/risk/correlation-matrix"
echo ""
echo "To check logs: sudo journalctl -u $SERVICE_NAME -f"
echo "To restart: sudo systemctl restart $SERVICE_NAME"
echo "To stop: sudo systemctl stop $SERVICE_NAME"
