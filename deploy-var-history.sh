#!/bin/bash

# Quick deployment script for VaR History endpoint
# Only uploads the modified risk.py file to Digital Ocean

set -e

echo "🚀 Deploying VaR History Endpoint to Digital Ocean..."

# Configuration
DROPLET_IP="157.230.58.248"
DROPLET_USER="root"
BACKEND_DIR="/var/www/4ex.ninja/4ex.ninja-backend"
LOCAL_FILE="4ex.ninja-backend/src/api/routes/risk.py"
REMOTE_FILE="$BACKEND_DIR/src/api/routes/risk.py"

echo "📁 Uploading updated risk.py file..."

# Copy the single file to the droplet
scp "$LOCAL_FILE" "$DROPLET_USER@$DROPLET_IP:$REMOTE_FILE"

echo "🔄 Restarting backend service..."

# Restart the backend service to load the new endpoint
ssh "$DROPLET_USER@$DROPLET_IP" << 'EOF'
# Kill the existing uvicorn process
pkill -f "uvicorn app:app"
sleep 2

# Start the backend again
cd /var/www/4ex.ninja
source venv/bin/activate
cd 4ex.ninja-backend
nohup uvicorn app:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
sleep 3

# Check if it's running
ps aux | grep uvicorn | grep -v grep
EOF

echo "✅ VaR History endpoint deployed successfully!"
echo "🔗 Test the endpoint: http://$DROPLET_IP:8000/api/risk/var-history?period=1D"
