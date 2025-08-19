#!/bin/bash

# 🔍 Pre-Deployment Checklist for Emergency Risk Management System

echo "🔍 4ex.ninja Emergency Risk Management - Pre-Deployment Checklist"
echo "=================================================================="

# Function to check if a value is set
check_env_var() {
    local var_name=$1
    local var_value=$2
    if [ -z "$var_value" ] || [ "$var_value" = "your_${var_name,,}_here" ]; then
        echo "❌ $var_name: Not configured"
        return 1
    else
        echo "✅ $var_name: Configured"
        return 0
    fi
}

# Check local environment
echo ""
echo "📋 Local Environment Check:"
echo "----------------------------"

missing_vars=0

# Load .env if it exists
if [ -f ".env" ]; then
    source .env
else
    echo "⚠️  No .env file found in current directory"
fi

# Check required environment variables
check_env_var "OANDA_API_KEY" "$OANDA_API_KEY" || ((missing_vars++))
check_env_var "OANDA_ACCOUNT_ID" "$OANDA_ACCOUNT_ID" || ((missing_vars++))
check_env_var "MONGO_CONNECTION_STRING" "$MONGO_CONNECTION_STRING" || ((missing_vars++))

# Check optional variables
echo ""
echo "🔧 Optional Configuration:"
echo "--------------------------"
check_env_var "DISCORD_WEBHOOK_URL" "$DISCORD_WEBHOOK_URL" || echo "⚠️  DISCORD_WEBHOOK_URL: Not set (Discord alerts disabled)"
check_env_var "REDIS_URL" "$REDIS_URL" || echo "⚠️  REDIS_URL: Not set (Redis optimization disabled)"

# Check Digital Ocean connectivity
echo ""
echo "🌐 Digital Ocean Connectivity:"
echo "------------------------------"
if ping -c 1 157.230.58.248 > /dev/null 2>&1; then
    echo "✅ Digital Ocean droplet: Reachable"
else
    echo "❌ Digital Ocean droplet: Unreachable"
    ((missing_vars++))
fi

# Check SSH access (if we can detect it)
echo ""
echo "🔑 SSH Access Check:"
echo "-------------------"
echo "💡 You'll need SSH access to: root@157.230.58.248"
echo "   Test with: ssh root@157.230.58.248 'echo SSH connection successful'"

# Check MongoDB connectivity (basic test)
echo ""
echo "🗄️  Database Connectivity:"
echo "-------------------------"
if [ ! -z "$MONGO_CONNECTION_STRING" ] && [ "$MONGO_CONNECTION_STRING" != "your_mongo_connection_string_here" ]; then
    echo "✅ MongoDB connection string: Configured"
    echo "💡 The deployment will test actual connectivity"
else
    echo "❌ MongoDB connection string: Not configured"
    ((missing_vars++))
fi

# Summary
echo ""
echo "📊 Pre-Deployment Summary:"
echo "=========================="

if [ $missing_vars -eq 0 ]; then
    echo "✅ All critical requirements met!"
    echo ""
    echo "🚀 Ready to deploy! Run the deployment with:"
    echo "   scp deploy-emergency-risk.sh root@157.230.58.248:/tmp/"
    echo "   ssh root@157.230.58.248 'chmod +x /tmp/deploy-emergency-risk.sh && /tmp/deploy-emergency-risk.sh'"
    echo ""
    echo "📋 What will be deployed:"
    echo "   ✅ Emergency Risk Management Framework (4-level protocols)"
    echo "   ✅ Database persistence for risk events"
    echo "   ✅ MA_Unified_Strat with enhanced risk management"
    echo "   ✅ Real-time monitoring and alerts"
    echo "   ✅ Automated position sizing and trading halts"
else
    echo "❌ $missing_vars critical requirement(s) missing"
    echo ""
    echo "🔧 Required actions before deployment:"
    echo "   1. Configure missing environment variables"
    echo "   2. Ensure Digital Ocean droplet is accessible"
    echo "   3. Test SSH connectivity"
    echo "   4. Verify MongoDB connection string"
    echo ""
    echo "💡 Once fixed, re-run this checklist and then deploy"
fi

echo ""
echo "📚 Additional Resources:"
echo "   - MongoDB Atlas: https://cloud.mongodb.com/"
echo "   - OANDA API: https://developer.oanda.com/"
echo "   - Discord Webhooks: https://discord.com/developers/docs/resources/webhook"
