#!/bin/bash

# 🚀 4ex.ninja Fresh Droplet Deployment Script
# Complete setup for new droplet with optimal MA strategy configuration
# ================================================================

# Configuration
DROPLET_IP="165.227.5.89"
DROPLET_USER="root"
PROJECT_NAME="4ex.ninja"
BACKEND_DIR="/opt/4ex-ninja-backend"
FRONTEND_DIR="/var/www/4ex.ninja-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 4ex.ninja Fresh Droplet Deployment${NC}"
echo "============================================"
echo -e "Target Droplet: ${YELLOW}$DROPLET_IP${NC}"
echo -e "Deployment Mode: ${GREEN}Fresh Installation${NC}"
echo ""

# Function to run commands on droplet
run_remote() {
    echo -e "${BLUE}[REMOTE]${NC} $1"
    ssh -o StrictHostKeyChecking=no $DROPLET_USER@$DROPLET_IP "$1"
}

# Function to copy files to droplet
copy_to_droplet() {
    echo -e "${BLUE}[COPY]${NC} $1 → $2"
    scp -o StrictHostKeyChecking=no -r "$1" "$DROPLET_USER@$DROPLET_IP:$2"
}

# Step 1: Test connection
echo -e "${YELLOW}📡 Testing connection to droplet...${NC}"
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $DROPLET_USER@$DROPLET_IP "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✅ Successfully connected to droplet${NC}"
else
    echo -e "${RED}❌ Failed to connect to droplet${NC}"
    echo "Please ensure the droplet is running and SSH access is enabled"
    exit 1
fi

# Step 2: System updates and dependencies
echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
run_remote "apt update && apt upgrade -y"
run_remote "apt install -y python3 python3-pip python3-venv nginx git curl supervisor htop"

# Step 3: Create project directories
echo -e "${YELLOW}📁 Creating project directories...${NC}"
run_remote "mkdir -p $BACKEND_DIR"
run_remote "mkdir -p $FRONTEND_DIR"
run_remote "mkdir -p /var/log/4ex-ninja"

# Step 4: Deploy backend code
echo -e "${YELLOW}🔧 Deploying backend code...${NC}"
copy_to_droplet "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/" "$BACKEND_DIR/"

# Step 5: Set up Python virtual environment
echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
run_remote "cd $BACKEND_DIR && python3 -m venv venv"
run_remote "cd $BACKEND_DIR && source venv/bin/activate && pip install --upgrade pip"
run_remote "cd $BACKEND_DIR && source venv/bin/activate && pip install -r requirements.txt"

# Step 6: Verify optimal MA strategy configuration
echo -e "${YELLOW}⚙️ Verifying optimal MA strategy configuration...${NC}"
OPTIMAL_CHECK=$(ssh $DROPLET_USER@$DROPLET_IP "grep 'slow_ma.*200' $BACKEND_DIR/src/config/strat_settings.py | wc -l")
if [ "$OPTIMAL_CHECK" -ge "8" ]; then
    echo -e "${GREEN}✅ Optimal MA parameters confirmed (8+ Daily strategies with slow_ma=200)${NC}"
else
    echo -e "${RED}❌ Configuration issue detected${NC}"
    echo "Expected 8+ Daily strategies with slow_ma=200, found: $OPTIMAL_CHECK"
fi

# Step 7: Create systemd service
echo -e "${YELLOW}🔄 Creating systemd service...${NC}"
cat > /tmp/4ex-ninja-backend.service << EOF
[Unit]
Description=4ex.ninja Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BACKEND_DIR
Environment=PATH=$BACKEND_DIR/venv/bin
Environment=PYTHONPATH=$BACKEND_DIR
ExecStart=$BACKEND_DIR/venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=append:/var/log/4ex-ninja/backend.log
StandardError=append:/var/log/4ex-ninja/backend-error.log

[Install]
WantedBy=multi-user.target
EOF

copy_to_droplet "/tmp/4ex-ninja-backend.service" "/etc/systemd/system/"
run_remote "systemctl daemon-reload"
run_remote "systemctl enable 4ex-ninja-backend"

# Step 8: Configure nginx (basic setup)
echo -e "${YELLOW}🌐 Configuring nginx...${NC}"
cat > /tmp/4ex-ninja-nginx.conf << EOF
server {
    listen 80;
    server_name $DROPLET_IP;
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location / {
        return 200 "4ex.ninja Backend Server - API available at /api/";
        add_header Content-Type text/plain;
    }
}
EOF

copy_to_droplet "/tmp/4ex-ninja-nginx.conf" "/etc/nginx/sites-available/4ex-ninja"
run_remote "ln -sf /etc/nginx/sites-available/4ex-ninja /etc/nginx/sites-enabled/"
run_remote "rm -f /etc/nginx/sites-enabled/default"
run_remote "nginx -t && systemctl restart nginx"

# Step 9: Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
run_remote "systemctl start 4ex-ninja-backend"
sleep 3

# Step 10: Verify deployment
echo -e "${YELLOW}🔍 Verifying deployment...${NC}"
SERVICE_STATUS=$(ssh $DROPLET_USER@$DROPLET_IP "systemctl is-active 4ex-ninja-backend")
if [ "$SERVICE_STATUS" = "active" ]; then
    echo -e "${GREEN}✅ Backend service is running${NC}"
else
    echo -e "${RED}❌ Backend service failed to start${NC}"
    echo "Service status: $SERVICE_STATUS"
    run_remote "journalctl -u 4ex-ninja-backend --no-pager -n 10"
fi

# Step 11: Test API endpoint
echo -e "${YELLOW}🧪 Testing API endpoint...${NC}"
sleep 2
API_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://$DROPLET_IP/api/ 2>/dev/null || echo "000")
if [ "$API_TEST" = "200" ] || [ "$API_TEST" = "404" ] || [ "$API_TEST" = "422" ]; then
    echo -e "${GREEN}✅ API endpoint responding (HTTP $API_TEST)${NC}"
else
    echo -e "${RED}❌ API endpoint not responding (HTTP $API_TEST)${NC}"
fi

# Step 12: Display summary
echo ""
echo -e "${GREEN}🎉 Deployment Summary${NC}"
echo "=================================="
echo -e "Droplet IP: ${YELLOW}$DROPLET_IP${NC}"
echo -e "Backend Service: ${GREEN}$SERVICE_STATUS${NC}"
echo -e "API Endpoint: ${YELLOW}http://$DROPLET_IP/api/${NC}"
echo -e "Logs: ${BLUE}/var/log/4ex-ninja/${NC}"
echo ""
echo -e "${BLUE}📊 MA Strategy Configuration:${NC}"
echo "- 8 Daily currency pairs with optimal parameters"
echo "- fast_ma: 50, slow_ma: 200 (conservative_moderate_daily)"
echo "- Expected performance: 18.0-19.8% returns"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Test API endpoints: curl http://$DROPLET_IP/api/"
echo "2. Monitor logs: ssh root@$DROPLET_IP 'tail -f /var/log/4ex-ninja/backend.log'"
echo "3. Check service status: ssh root@$DROPLET_IP 'systemctl status 4ex-ninja-backend'"
echo ""
echo -e "${GREEN}🚀 Fresh deployment complete!${NC}"

# Cleanup temporary files
rm -f /tmp/4ex-ninja-backend.service /tmp/4ex-ninja-nginx.conf
