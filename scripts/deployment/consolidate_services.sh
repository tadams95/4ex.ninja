#!/bin/bash

# 4ex.ninja Service Consolidation Guide
# Merge Backtesting API into Monitoring Dashboard to free up port 8082

echo "🔧 Service Consolidation: Merge Backtesting into Monitoring"
echo "=========================================================="
echo ""
echo "🎯 Goal: Free up port 8082 by merging backtesting API into monitoring dashboard (port 8081)"
echo ""

DROPLET_IP="157.230.58.248"
DROPLET_USER="root"

echo "📋 Current Status:"
echo "   Port 8081: Monitoring Dashboard (ACTIVE)"
echo "   Port 8082: Backtesting API (ACTIVE)"
echo "   Port 8083: LAST AVAILABLE PORT"
echo ""

echo "🚨 WARNING: This will temporarily interrupt backtesting API service"
read -p "Continue with consolidation? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Consolidation cancelled"
    exit 1
fi

echo ""
echo "🔄 Step 1: Stop backtesting service..."
ssh $DROPLET_USER@$DROPLET_IP "systemctl stop 4ex-backend"

echo "🔄 Step 2: Backup current monitoring dashboard..."
ssh $DROPLET_USER@$DROPLET_IP "cp /var/www/4ex.ninja/4ex.ninja-backend/src/monitoring/dashboard_api.py /var/www/4ex.ninja/4ex.ninja-backend/src/monitoring/dashboard_api.py.backup"

echo "🔄 Step 3: Update monitoring dashboard to include backtesting routes..."
ssh $DROPLET_USER@$DROPLET_IP "
cd /var/www/4ex.ninja/4ex.ninja-backend/src/monitoring

# Add backtesting import to dashboard_api.py
echo '
# Import backtesting router
from ..backtesting.backtest_api import backtest_router

# Include backtesting routes
app.include_router(backtest_router, prefix=\"/api/v1\")
' >> dashboard_api.py
"

echo "🔄 Step 4: Restart monitoring service..."
ssh $DROPLET_USER@$DROPLET_IP "systemctl restart monitoring-dashboard"

echo "🔄 Step 5: Test consolidated API..."
sleep 5

echo "🧪 Testing monitoring endpoints:"
curl -s http://$DROPLET_IP:8081/health > /dev/null && echo "✅ Monitoring health: OK" || echo "❌ Monitoring health: FAIL"

echo "🧪 Testing backtesting endpoints:"
curl -s http://$DROPLET_IP:8081/api/v1/backtest/health > /dev/null && echo "✅ Backtesting health: OK" || echo "❌ Backtesting health: FAIL"

echo ""
echo "✅ Consolidation Results:"
echo "   📡 Single API endpoint: http://$DROPLET_IP:8081/"
echo "   📊 Monitoring: http://$DROPLET_IP:8081/api/v1/monitoring/*"
echo "   🔬 Backtesting: http://$DROPLET_IP:8081/api/v1/backtest/*"
echo "   🟢 Port 8082: NOW AVAILABLE for future services"
echo "   🟢 Port 8083: Still available for critical services"
echo ""
echo "🎯 Next Steps:"
echo "   1. Update documentation to reflect new endpoint"
echo "   2. Update deployment scripts"
echo "   3. Inform team of new API structure"
