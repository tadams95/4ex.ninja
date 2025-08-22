#!/bin/bash

# =============================================================================
# Pre-Deployment Verification
# Verify all Discord integration components before production deployment
# =============================================================================

echo "🔍 PRE-DEPLOYMENT VERIFICATION"
echo "=============================="

# Check current directory
if [ ! -f "enhanced_daily_strategy.py" ]; then
    echo "❌ Error: Must run from 4ex.ninja-backend directory"
    exit 1
fi

echo "✅ Running from correct directory"

# Check Discord integration files
echo ""
echo "📋 Checking Discord Integration Files:"

DISCORD_FILES=(
    "services/enhanced_discord_service.py"
    "services/signal_discord_integration.py" 
    "services/notification_service.py"
    "services/enhanced_daily_production_service.py"
    "models/signal_models.py"
    ".env"
)

ALL_PRESENT=true
for file in "${DISCORD_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - MISSING"
        ALL_PRESENT=false
    fi
done

if [ "$ALL_PRESENT" = false ]; then
    echo ""
    echo "❌ Missing required files. Please ensure all Discord integration files are present."
    exit 1
fi

# Check environment variables
echo ""
echo "🔧 Checking Discord Webhook Configuration:"

if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    exit 1
fi

REQUIRED_WEBHOOKS=(
    "DISCORD_WEBHOOK_SIGNALS_FREE"
    "DISCORD_WEBHOOK_SIGNALS_PREMIUM"
    "DISCORD_WEBHOOK_ALERTS_CRITICAL"
)

WEBHOOKS_OK=true
for webhook in "${REQUIRED_WEBHOOKS[@]}"; do
    if grep -q "^$webhook=" .env; then
        echo "✅ $webhook configured"
    else
        echo "⚠️  $webhook not configured"
        WEBHOOKS_OK=false
    fi
done

# Test Python imports
echo ""
echo "🐍 Testing Python Imports:"

python3 -c "
import sys
import os
sys.path.append(os.getcwd())

try:
    # Test core imports
    from services.enhanced_discord_service import get_enhanced_discord_service
    print('✅ Enhanced Discord Service')
    
    from services.enhanced_daily_production_service import EnhancedDailyProductionService
    print('✅ Enhanced Daily Production Service')
    
    from services.notification_service import NotificationService
    print('✅ Notification Service')
    
    # Test service initialization
    service = EnhancedDailyProductionService()
    if hasattr(service, 'discord_service'):
        print('✅ Discord service initialized in production service')
    else:
        print('❌ Discord service not initialized')
        sys.exit(1)
        
    if 'signals_sent_to_discord' in service.performance_metrics:
        print('✅ Discord delivery metrics enabled')
    else:
        print('❌ Discord delivery metrics missing')
        sys.exit(1)
    
    print('✅ All imports and initializations successful')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Initialization error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Python verification failed"
    exit 1
fi

# Test SSH connection to production
echo ""
echo "🔗 Testing SSH Connection to Production:"
ssh -o ConnectTimeout=10 root@165.227.5.89 "echo 'SSH connection successful'" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ SSH connection to 165.227.5.89 successful"
else
    echo "❌ SSH connection to 165.227.5.89 failed"
    echo "   Please check your SSH keys and network connection"
    exit 1
fi

# Final verification summary
echo ""
echo "🎯 PRE-DEPLOYMENT SUMMARY:"
echo "========================="
echo "✅ All Discord integration files present"
echo "✅ Python imports working"
echo "✅ Service initialization successful"
echo "✅ SSH connection to production working"

if [ "$WEBHOOKS_OK" = true ]; then
    echo "✅ Discord webhooks configured"
else
    echo "⚠️  Some Discord webhooks not configured (will use available ones)"
fi

echo ""
echo "🚀 READY FOR PRODUCTION DEPLOYMENT!"
echo ""
echo "Next step: Run './deploy_to_production.sh' to deploy to 165.227.5.89"
