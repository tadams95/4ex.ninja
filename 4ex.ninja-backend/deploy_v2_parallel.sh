#!/bin/bash

# Enhanced Daily Strategy V2 Parallel Deployment Script
# Deploys V2 alongside existing V1 on Digital Ocean droplet

echo "========================================"
echo "Enhanced Daily Strategy V2 Deployment"
echo "Parallel Deployment Mode"
echo "========================================"

# Set deployment variables
DROPLET_IP="165.227.5.89"
DROPLET_USER="root"
DEPLOYMENT_PATH="/opt/4ex-ninja-backend"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "🚀 Starting V2 parallel deployment..."

# Create backup of current system
echo "📦 Creating system backup..."
ssh $DROPLET_USER@$DROPLET_IP "cd $DEPLOYMENT_PATH && tar -czf backups/pre_v2_backup_$TIMESTAMP.tar.gz ."

# Upload V2 files
echo "📤 Uploading Enhanced Daily Strategy V2 files..."
scp enhanced_daily_strategy_v2.py $DROPLET_USER@$DROPLET_IP:$DEPLOYMENT_PATH/
scp enhanced_daily_strategy_v2_config.json $DROPLET_USER@$DROPLET_IP:$DEPLOYMENT_PATH/
scp confidence_risk_manager_v2.py $DROPLET_USER@$DROPLET_IP:$DEPLOYMENT_PATH/

# Upload updated app.py with V2 endpoints
echo "� Uploading updated app.py with V2 endpoints..."
scp app.py $DROPLET_USER@$DROPLET_IP:$DEPLOYMENT_PATH/

# Upload updated service file (fixed V1 import path)
echo "📤 Uploading updated enhanced_daily_production_service.py..."
scp services/enhanced_daily_production_service.py $DROPLET_USER@$DROPLET_IP:$DEPLOYMENT_PATH/services/

echo "✅ V2 monitoring endpoints integrated into app.py"

# Install V2 dependencies
echo "📦 Installing V2 dependencies..."
ssh $DROPLET_USER@$DROPLET_IP "cd $DEPLOYMENT_PATH && pip3 install -r requirements.txt"

# Test V2 deployment
echo "🧪 Testing V2 deployment..."
ssh $DROPLET_USER@$DROPLET_IP "cd $DEPLOYMENT_PATH && python3 -c 'from enhanced_daily_strategy_v2 import EnhancedDailyStrategyV2; strategy = EnhancedDailyStrategyV2(); print(\"✅ V2 Strategy loaded successfully\")'"

# Restart application with V2 support
echo "🔄 Restarting application with V2 support..."
ssh $DROPLET_USER@$DROPLET_IP "cd $DEPLOYMENT_PATH && systemctl restart 4ex-ninja"

# Verify deployment
echo "✅ Verifying V2 deployment..."
sleep 10
curl -f http://$DROPLET_IP:5000/api/v2/status || echo "❌ V2 status check failed"

echo "========================================"
echo "✅ Enhanced Daily Strategy V2 Deployed"
echo "Mode: Parallel (V1 + V2 running)"
echo "V1 Endpoint: /api/v1/signals"
echo "V2 Endpoint: /api/v2/signals"
echo "Monitor: /api/v2/status"
echo "========================================"

echo "📊 Starting 30-day comparison period..."
echo "Next: Monitor V1 vs V2 performance for migration decision"
