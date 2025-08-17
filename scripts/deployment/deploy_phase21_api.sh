#!/bin/bash

# Phase 2.1 Universal Backtesting API - Quick Deploy
# Deploy to Digital Ocean: 157.230.58.248

set -e

DROPLET_IP="157.230.58.248"
DROPLET_USER="root"
PROJECT_PATH="/var/www/4ex.ninja/4ex.ninja-backend"

echo "🚀 Deploying Phase 2.1 Universal Backtesting API..."
echo "Target: $DROPLET_USER@$DROPLET_IP"
echo ""

# 1. Deploy backtesting module
echo "📦 Deploying backtesting module..."
scp -r 4ex.ninja-backend/src/backtesting/ $DROPLET_USER@$DROPLET_IP:$PROJECT_PATH/src/

# 2. Deploy updated app.py with backtest router
echo "📦 Deploying updated FastAPI app..."
scp 4ex.ninja-backend/src/app.py $DROPLET_USER@$DROPLET_IP:$PROJECT_PATH/src/

# 3. Restart backend service
echo "🔄 Restarting backend service..."
ssh $DROPLET_USER@$DROPLET_IP 'systemctl restart 4ex-backend'

# 4. Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# 5. Test deployment
echo "🧪 Testing deployment..."
if curl -s http://$DROPLET_IP:8082/api/v1/backtest/health > /dev/null; then
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 Phase 2.1 Universal Backtesting API is now live at:"
    echo "   http://$DROPLET_IP:8082/api/v1/backtest/"
    echo ""
    echo "📋 Available endpoints:"
    echo "   GET  /api/v1/backtest/health         - Health check"
    echo "   GET  /api/v1/backtest/strategies     - List strategies"
    echo "   POST /api/v1/backtest/run            - Run backtest"
    echo "   GET  /api/v1/backtest/results        - List results"
    echo "   GET  /api/v1/backtest/results/{id}   - Get specific result"
    echo "   DEL  /api/v1/backtest/results/{id}   - Delete result"
    echo ""
    echo "🎯 Ready for team collaboration and remote backtesting!"
else
    echo "❌ Deployment failed - service not responding"
    echo "Check logs: ssh $DROPLET_USER@$DROPLET_IP 'journalctl -u 4ex-backend -f'"
    exit 1
fi
