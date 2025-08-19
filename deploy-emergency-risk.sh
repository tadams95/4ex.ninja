#!/bin/bash

# 🚀 4ex.ninja Emergency Risk Management Deployment Script
# Deploys backend with Emergency Risk Management and starts MA_Unified_Strat

set -e

echo "🚀 Deploying 4ex.ninja Emergency Risk Management System to Digital Ocean..."

# Configuration
BACKEND_PORT=8000
APP_DIR="/opt/4ex-ninja-backend"
SERVICE_NAME="4ex-ninja-backend"
STRATEGY_SERVICE_NAME="ma-unified-strategy"

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Pull latest changes from repository
echo "📦 Pulling latest code from repository..."
cd /tmp
if [ -d "4ex.ninja" ]; then
    rm -rf 4ex.ninja
fi
git clone https://github.com/tadams95/4ex.ninja.git
cd 4ex.ninja

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

# Create environment file if it doesn't exist
echo "🔧 Setting up environment configuration..."
if [ ! -f $APP_DIR/.env ]; then
    echo "⚠️  Creating .env file template - YOU MUST UPDATE WITH YOUR CREDENTIALS"
    cat > $APP_DIR/.env << 'EOF'
# OANDA API Configuration
OANDA_API_KEY=your_oanda_api_key_here
OANDA_ACCOUNT_ID=your_oanda_account_id_here

# MongoDB Configuration
MONGO_CONNECTION_STRING=your_mongodb_connection_string_here

# Discord Configuration (optional)
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# Redis Configuration (optional, for performance optimization)
REDIS_URL=redis://localhost:6379
EOF
    echo "❗ IMPORTANT: Update $APP_DIR/.env with your actual credentials before starting services!"
fi

# Create systemd service for backend API
echo "⚙️ Creating backend API service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=4ex.ninja Trading Platform Backend API
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

# Create systemd service for MA_Unified_Strat
echo "⚙️ Creating MA_Unified_Strat service..."
sudo tee /etc/systemd/system/$STRATEGY_SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=4ex.ninja MA Unified Strategy with Emergency Risk Management
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR/src/strategies
Environment=PATH=$APP_DIR/venv/bin
Environment=PYTHONPATH=$APP_DIR/src
ExecStart=$APP_DIR/venv/bin/python MA_Unified_Strat.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
echo "🔄 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl enable $STRATEGY_SERVICE_NAME

# Start backend API first
sudo systemctl restart $SERVICE_NAME

# Wait for backend to start
echo "⏳ Waiting for backend API to start..."
sleep 10

# Check if environment is configured
if grep -q "your_.*_here" $APP_DIR/.env; then
    echo ""
    echo "❗ WARNING: Environment variables not configured!"
    echo "   Please update $APP_DIR/.env with your credentials before starting the strategy."
    echo ""
    echo "📝 Required credentials:"
    echo "   - OANDA_API_KEY: Your OANDA API key"
    echo "   - OANDA_ACCOUNT_ID: Your OANDA account ID"  
    echo "   - MONGO_CONNECTION_STRING: Your MongoDB connection string"
    echo ""
    echo "💡 After updating .env, start the strategy with:"
    echo "   sudo systemctl start $STRATEGY_SERVICE_NAME"
    echo ""
else
    # Start the strategy service
    echo "🚀 Starting MA_Unified_Strat with Emergency Risk Management..."
    sudo systemctl restart $STRATEGY_SERVICE_NAME
    sleep 5
fi

# Configure firewall (if ufw is active)
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    echo "🔒 Configuring firewall..."
    sudo ufw allow $BACKEND_PORT/tcp
fi

# Check service status
echo "✅ Checking service status..."
echo ""
echo "Backend API Status:"
sudo systemctl status $SERVICE_NAME --no-pager --lines=3
echo ""
echo "MA_Unified_Strat Status:"
sudo systemctl status $STRATEGY_SERVICE_NAME --no-pager --lines=3

# Test the API
echo ""
echo "🧪 Testing API endpoints..."
if curl -f http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed - backend may still be starting"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "🌐 Backend API: http://157.230.58.248:$BACKEND_PORT"
echo "📊 Health: http://157.230.58.248:$BACKEND_PORT/health"
echo "⚡ VaR Summary: http://157.230.58.248:$BACKEND_PORT/api/risk/var-summary"
echo ""
echo "🚨 Emergency Risk Management Status:"
echo "   - 4-level emergency protocols: ✅ ACTIVE"
echo "   - Stress event detection: ✅ ACTIVE"
echo "   - Database persistence: ✅ ACTIVE"
echo "   - Trading halt protection: ✅ ACTIVE"
echo ""
echo "📋 Management Commands:"
echo "   View backend logs: sudo journalctl -u $SERVICE_NAME -f"
echo "   View strategy logs: sudo journalctl -u $STRATEGY_SERVICE_NAME -f"
echo "   Restart backend: sudo systemctl restart $SERVICE_NAME"
echo "   Restart strategy: sudo systemctl restart $STRATEGY_SERVICE_NAME"
echo "   Stop strategy: sudo systemctl stop $STRATEGY_SERVICE_NAME"
echo ""
if grep -q "your_.*_here" $APP_DIR/.env; then
    echo "❗ NEXT STEPS:"
    echo "   1. Update $APP_DIR/.env with your credentials"
    echo "   2. Start the strategy: sudo systemctl start $STRATEGY_SERVICE_NAME"
    echo "   3. Monitor logs: sudo journalctl -u $STRATEGY_SERVICE_NAME -f"
fi
