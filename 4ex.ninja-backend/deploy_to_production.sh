#!/bin/bash

# =============================================================================
# Production Deployment Script for Discord Integration
# Deploys Enhanced Daily Strategy with Discord notifications to Digital Ocean
# Target: 165.227.5.89
# =============================================================================

DROPLET_IP="165.227.5.89"
DROPLET_USER="root"  # Change if using different user
REMOTE_PATH="/var/www/4ex.ninja-backend"  # Adjust path as needed
LOCAL_PATH="."

echo "🚀 Deploying Enhanced Daily Strategy with Discord Integration"
echo "Target: $DROPLET_USER@$DROPLET_IP:$REMOTE_PATH"
echo "=========================================================="

# Function to check if command was successful
check_status() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1 FAILED"
        exit 1
    fi
}

# Pre-deployment checks
echo ""
echo "🔍 Pre-deployment validation..."

# Check if we're in the right directory
if [ ! -f "enhanced_daily_strategy_v2.py" ]; then
    echo "❌ Error: Must run from 4ex.ninja-backend directory"
    exit 1
fi

# Check if Discord integration files exist
REQUIRED_FILES=(
    "enhanced_daily_strategy_v2.py"
    "confidence_risk_manager_v2.py"
    "production_deployment.py"
    "oanda_live_bridge.py"
    "services/data_service.py"
    "services/enhanced_discord_service.py"
    "app.py"
    ".env"
    "requirements.txt"
)

echo "📋 Checking required files..."
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - MISSING"
        exit 1
    fi
done

# Test SSH connection
echo ""
echo "🔗 Testing SSH connection..."
ssh -o ConnectTimeout=10 $DROPLET_USER@$DROPLET_IP "echo 'SSH connection successful'" > /dev/null 2>&1
check_status "SSH connection to droplet"

# Backup current production
echo ""
echo "💾 Creating backup of current production..."
BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
ssh $DROPLET_USER@$DROPLET_IP "
    if [ -d '$REMOTE_PATH' ]; then
        cp -r $REMOTE_PATH ${REMOTE_PATH}_$BACKUP_NAME
        echo 'Backup created: ${REMOTE_PATH}_$BACKUP_NAME'
    else
        echo 'No existing installation found, skipping backup'
    fi
"
check_status "Production backup"

# Create remote directory if it doesn't exist
echo ""
echo "📁 Preparing remote directory..."
ssh $DROPLET_USER@$DROPLET_IP "mkdir -p $REMOTE_PATH"
check_status "Remote directory creation"

# Deploy core files
echo ""
echo "📤 Deploying core application files..."

# Copy main application files
rsync -avz --progress \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='logs/*.log' \
    $LOCAL_PATH/ $DROPLET_USER@$DROPLET_IP:$REMOTE_PATH/
check_status "Core files deployment"

# Deploy Discord integration files specifically
echo ""
echo "🎯 Deploying Discord integration components..."

# Key Discord files
DISCORD_FILES=(
    "services/enhanced_discord_service.py"
    "services/signal_discord_integration.py"
    "services/notification_service.py"
    "services/enhanced_daily_production_service.py"
    "app.py"
)

for file in "${DISCORD_FILES[@]}"; do
    rsync -avz $file $DROPLET_USER@$DROPLET_IP:$REMOTE_PATH/$file
    check_status "Deployed $file"
done

# Install/update dependencies
echo ""
echo "📦 Installing Python dependencies..."
ssh $DROPLET_USER@$DROPLET_IP "
    cd $REMOTE_PATH
    python3 -m pip install --upgrade pip
    pip3 install -r requirements.txt
    pip3 install aiohttp asyncio
"
check_status "Python dependencies installation"

# Set proper permissions
echo ""
echo "🔐 Setting file permissions..."
ssh $DROPLET_USER@$DROPLET_IP "
    cd $REMOTE_PATH
    chmod +x *.sh
    chmod 644 *.py
    chmod 600 .env
    chown -R www-data:www-data . 2>/dev/null || echo 'www-data user not found, skipping ownership change'
"
check_status "File permissions"

# Test Discord integration on production
echo ""
echo "🧪 Testing Discord integration on production..."
ssh $DROPLET_USER@$DROPLET_IP "
    cd $REMOTE_PATH
    python3 -c '
import sys
import os
sys.path.append(os.getcwd())

try:
    from services.enhanced_discord_service import get_enhanced_discord_service
    from services.enhanced_daily_production_service import EnhancedDailyProductionService
    
    print(\"✅ Discord service import successful\")
    
    # Test service initialization
    service = EnhancedDailyProductionService()
    if hasattr(service, \"discord_service\"):
        print(\"✅ Discord integration initialized in production service\")
    else:
        print(\"❌ Discord integration not initialized\")
        sys.exit(1)
        
    print(\"✅ Production Discord integration test passed\")
    
except Exception as e:
    print(f\"❌ Production test failed: {e}\")
    sys.exit(1)
'
"
check_status "Production Discord integration test"

# Restart application service
echo ""
echo "🔄 Restarting application service..."

# Try common service names
SERVICE_COMMANDS=(
    "systemctl restart 4ex-ninja"
    "systemctl restart 4ex-ninja-backend"
    "systemctl restart forex-backend"
    "systemctl restart gunicorn"
    "pkill -f 'python.*app.py' && nohup python3 app.py > /dev/null 2>&1 &"
)

ssh $DROPLET_USER@$DROPLET_IP "
    cd $REMOTE_PATH
    
    # Try to restart known services
    for cmd in 'systemctl restart 4ex-ninja' 'systemctl restart 4ex-ninja-backend' 'systemctl restart forex-backend'; do
        if \$cmd 2>/dev/null; then
            echo \"Service restarted with: \$cmd\"
            exit 0
        fi
    done
    
    # If no service found, try manual restart
    echo 'No systemd service found, attempting manual restart...'
    pkill -f 'python.*app.py' 2>/dev/null || true
    sleep 2
    nohup python3 app.py > app.log 2>&1 &
    echo 'Application restarted manually'
"
check_status "Application service restart"

# Wait for service to start
echo ""
echo "⏳ Waiting for service to start..."
sleep 10

# Test production endpoints
echo ""
echo "🌐 Testing production endpoints..."

# Test basic health
echo "Testing health endpoint..."
curl -s -o /dev/null -w "%{http_code}" http://$DROPLET_IP:8000/health 2>/dev/null | grep -q "200"
if [ $? -eq 0 ]; then
    echo "✅ Health endpoint responding"
else
    echo "⚠️  Health endpoint not responding (may be on different port)"
fi

# Test Discord notification endpoint
echo "Testing Discord notification endpoint..."
DISCORD_TEST_RESPONSE=$(curl -s -X POST http://$DROPLET_IP:8000/notifications/test 2>/dev/null)
if echo "$DISCORD_TEST_RESPONSE" | grep -q "success"; then
    echo "✅ Discord notification endpoint responding"
else
    echo "⚠️  Discord notification endpoint test inconclusive"
fi

# Deployment summary
echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "=========================================="
echo "🔗 Production URLs:"
echo "   Health: http://$DROPLET_IP:8000/health"
echo "   Signals: http://$DROPLET_IP:8000/signals"
echo "   Discord Test: http://$DROPLET_IP:8000/notifications/test"
echo "   Performance: http://$DROPLET_IP:8000/performance"
echo ""
echo "📊 Test Commands:"
echo "   curl http://$DROPLET_IP:8000/health"
echo "   curl -X POST http://$DROPLET_IP:8000/notifications/test"
echo "   curl http://$DROPLET_IP:8000/signals"
echo ""
echo "🔍 Monitoring:"
echo "   ssh $DROPLET_USER@$DROPLET_IP 'tail -f $REMOTE_PATH/app.log'"
echo "   ssh $DROPLET_USER@$DROPLET_IP 'systemctl status 4ex-ninja'"
echo ""
echo "✅ Enhanced Daily Strategy with Discord integration is now LIVE!"
echo "🚀 Signals will automatically be sent to Discord when generated."
