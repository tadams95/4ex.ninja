#!/bin/bash

# Deploy Discord webhook configuration to production server

SERVER="root@138.197.105.133"
BACKEND_PATH="/root/4ex.ninja-backend"

echo "Deploying Discord webhook configuration..."

# Copy Discord configuration files
scp "4ex.ninja-backend/.env.discord" "${SERVER}:${BACKEND_PATH}/"
scp "4ex.ninja-backend/src/infrastructure/config/discord_webhook_config.py" "${SERVER}:${BACKEND_PATH}/src/infrastructure/config/"

# SSH into server and source the environment variables
ssh "${SERVER}" << 'EOF'
cd /root/4ex.ninja-backend

# Source Discord environment variables
echo "Sourcing Discord environment variables..."
source .env.discord

# Add to bashrc for persistence
echo "Adding Discord webhooks to .bashrc..."
cat .env.discord >> ~/.bashrc

# Restart the trading strategy to pick up new configuration
echo "Restarting MA_Unified_Strat..."
pkill -f "MA_Unified_Strat.py"
sleep 2

# Start with Discord environment
nohup bash -c 'source .env.discord && python3 MA_Unified_Strat.py' > strategy_logs.txt 2>&1 &

echo "Discord configuration deployed and strategy restarted!"
echo "Process ID: $!"
EOF

echo "Deployment complete!"
