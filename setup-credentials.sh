#!/bin/bash

# 🔧 Quick Environment Setup for Emergency Risk Management

echo "🔧 Setting up environment for Emergency Risk Management deployment"
echo "================================================================="

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    
    echo "Please provide your credentials:"
    echo ""
    
    # Get OANDA credentials
    read -p "🔑 Enter your OANDA API Key: " OANDA_API_KEY
    read -p "🔑 Enter your OANDA Account ID: " OANDA_ACCOUNT_ID
    
    # Get MongoDB connection string
    echo ""
    echo "💡 MongoDB connection string format:"
    echo "   mongodb+srv://username:password@cluster.mongodb.net/database_name"
    echo ""
    read -p "🗄️  Enter your MongoDB connection string: " MONGO_CONNECTION_STRING
    
    # Optional Discord webhook
    echo ""
    read -p "📱 Enter Discord webhook URL (optional, press Enter to skip): " DISCORD_WEBHOOK_URL
    
    # Create .env file
    cat > .env << EOF
# OANDA API Configuration
OANDA_API_KEY=$OANDA_API_KEY
OANDA_ACCOUNT_ID=$OANDA_ACCOUNT_ID

# MongoDB Configuration
MONGO_CONNECTION_STRING=$MONGO_CONNECTION_STRING

EOF

    # Add Discord if provided
    if [ ! -z "$DISCORD_WEBHOOK_URL" ]; then
        echo "# Discord Configuration" >> .env
        echo "DISCORD_WEBHOOK_URL=$DISCORD_WEBHOOK_URL" >> .env
        echo "" >> .env
    fi
    
    # Add Redis configuration
    echo "# Redis Configuration (for performance optimization)" >> .env
    echo "REDIS_URL=redis://localhost:6379" >> .env
    
    echo ""
    echo "✅ .env file created successfully!"
    
else
    echo "✅ .env file already exists"
fi

# Test the configuration
echo ""
echo "🧪 Testing configuration..."
source .env

# Validate required variables
missing=0

if [ -z "$OANDA_API_KEY" ]; then
    echo "❌ OANDA_API_KEY is missing"
    ((missing++))
else
    echo "✅ OANDA_API_KEY configured"
fi

if [ -z "$OANDA_ACCOUNT_ID" ]; then
    echo "❌ OANDA_ACCOUNT_ID is missing"
    ((missing++))
else
    echo "✅ OANDA_ACCOUNT_ID configured"
fi

if [ -z "$MONGO_CONNECTION_STRING" ]; then
    echo "❌ MONGO_CONNECTION_STRING is missing"
    ((missing++))
else
    echo "✅ MONGO_CONNECTION_STRING configured"
fi

if [ ! -z "$DISCORD_WEBHOOK_URL" ]; then
    echo "✅ DISCORD_WEBHOOK_URL configured (optional)"
else
    echo "⚠️  DISCORD_WEBHOOK_URL not set (Discord alerts will be disabled)"
fi

echo ""
if [ $missing -eq 0 ]; then
    echo "🎉 All required credentials configured!"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Test SSH access: ssh root@157.230.58.248 'echo SSH works'"
    echo "   2. Run pre-deployment check: ./pre-deployment-check.sh"
    echo "   3. Deploy to server: ./deploy-emergency-risk.sh"
    echo ""
    echo "📋 Or use the automated deployment:"
    echo "   scp deploy-emergency-risk.sh root@157.230.58.248:/tmp/"
    echo "   ssh root@157.230.58.248 'chmod +x /tmp/deploy-emergency-risk.sh && /tmp/deploy-emergency-risk.sh'"
else
    echo "❌ $missing required credential(s) missing. Please update .env file."
fi

echo ""
echo "💡 To modify credentials later, edit: .env"
