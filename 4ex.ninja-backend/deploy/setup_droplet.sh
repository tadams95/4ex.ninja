#!/bin/bash

# 4ex.ninja Production Server Setup Script
# This script sets up a complete production environment with HTTPS and security

set -e

# Configuration
FOREX_USER="forex"
DOMAIN_MAIN="4ex.ninja"
DOMAIN_API="api.4ex.ninja"
EMAIL="admin@4ex.ninja"  # Change this to your email
GITHUB_REPO="https://github.com/tadams95/4ex.ninja.git"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

log_info "Starting 4ex.ninja production server setup..."

# Update system
log_info "Updating system packages..."
apt-get update && apt-get upgrade -y

# Install required packages
log_info "Installing required packages..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    supervisor \
    ufw \
    certbot \
    python3-certbot-nginx \
    htop \
    curl \
    wget \
    unzip \
    fail2ban

# Install Node.js for frontend
log_info "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt-get install -y nodejs

# Configure firewall
log_info "Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Create forex user
log_info "Creating forex user..."
if ! id "$FOREX_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$FOREX_USER"
    usermod -aG sudo "$FOREX_USER"
fi

# Clone repository
log_info "Cloning repository..."
su - "$FOREX_USER" -c "
    if [ -d '4ex.ninja' ]; then
        cd 4ex.ninja && git pull
    else
        git clone $GITHUB_REPO
    fi
"

# Setup Python backend environment
log_info "Setting up Python backend environment..."
su - "$FOREX_USER" -c "
    cd 4ex.ninja/4ex.ninja-backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
"

# Setup Node.js frontend environment
log_info "Setting up Node.js frontend environment..."
su - "$FOREX_USER" -c "
    cd 4ex.ninja/4ex.ninja-frontend
    npm install
    npm run build
"

# Configure supervisor for backend service
log_info "Configuring backend service..."
cat > /etc/supervisor/conf.d/4ex-backend.conf << EOF
[program:4ex-backend]
command=/home/$FOREX_USER/4ex.ninja/4ex.ninja-backend/venv/bin/python -m uvicorn src.app:app --host 127.0.0.1 --port 8000
directory=/home/$FOREX_USER/4ex.ninja/4ex.ninja-backend
user=$FOREX_USER
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/4ex-backend.err.log
stdout_logfile=/var/log/supervisor/4ex-backend.out.log
environment=ENVIRONMENT="production",JWT_SECRET_KEY="$(openssl rand -base64 32)"

[program:4ex-frontend]
command=/usr/bin/npm start
directory=/home/$FOREX_USER/4ex.ninja/4ex.ninja-frontend
user=$FOREX_USER
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/4ex-frontend.err.log
stdout_logfile=/var/log/supervisor/4ex-frontend.out.log
environment=NODE_ENV="production",NEXT_PUBLIC_API_URL="https://$DOMAIN_API"
EOF

# Setup logging directories
log_info "Setting up logging..."
mkdir -p /var/log/4ex-ninja
chown "$FOREX_USER:$FOREX_USER" /var/log/4ex-ninja

# Configure fail2ban for additional security
log_info "Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=ReqLimit, port="http,https", protocol=tcp]
logpath = /var/log/nginx/error.log
maxretry = 10
findtime = 600
bantime = 7200
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Copy SSL setup script and make it executable
log_info "Preparing SSL setup..."
cp "/home/$FOREX_USER/4ex.ninja/4ex.ninja-backend/deploy/setup-ssl.sh" /usr/local/bin/
chmod +x /usr/local/bin/setup-ssl.sh

# Start services
log_info "Starting services..."
supervisorctl reread
supervisorctl update
supervisorctl start all

# Wait for services to start
log_info "Waiting for services to start..."
sleep 10

# Check if services are running
if supervisorctl status 4ex-backend | grep -q RUNNING; then
    log_info "✓ Backend service is running"
else
    log_error "✗ Backend service failed to start"
    supervisorctl status 4ex-backend
fi

if supervisorctl status 4ex-frontend | grep -q RUNNING; then
    log_info "✓ Frontend service is running"
else
    log_error "✗ Frontend service failed to start"
    supervisorctl status 4ex-frontend
fi

# Setup SSL certificates
log_info "Setting up SSL certificates..."
/usr/local/bin/setup-ssl.sh

# Create maintenance scripts
log_info "Creating maintenance scripts..."

# System update script
cat > /usr/local/bin/update-4ex.sh << 'EOF'
#!/bin/bash
# Update 4ex.ninja application

log_info() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

log_info "Updating 4ex.ninja application..."

# Stop services
supervisorctl stop all

# Update code
su - forex -c "cd 4ex.ninja && git pull"

# Update backend dependencies
su - forex -c "cd 4ex.ninja/4ex.ninja-backend && source venv/bin/activate && pip install -r requirements.txt"

# Update frontend dependencies and rebuild
su - forex -c "cd 4ex.ninja/4ex.ninja-frontend && npm install && npm run build"

# Restart services
supervisorctl start all

log_info "Update completed successfully!"
EOF

chmod +x /usr/local/bin/update-4ex.sh

# System status script
cat > /usr/local/bin/status-4ex.sh << 'EOF'
#!/bin/bash
# Check 4ex.ninja system status

echo "=== 4ex.ninja System Status ==="
echo "Date: $(date)"
echo ""

echo "Services:"
supervisorctl status

echo ""
echo "SSL Certificates:"
certbot certificates

echo ""
echo "Nginx Status:"
systemctl status nginx --no-pager -l

echo ""
echo "System Resources:"
free -h
df -h /

echo ""
echo "Active Connections:"
netstat -tuln | grep :80
netstat -tuln | grep :443
netstat -tuln | grep :8000
netstat -tuln | grep :3000

echo ""
echo "Recent Logs:"
tail -n 5 /var/log/supervisor/4ex-backend.out.log
EOF

chmod +x /usr/local/bin/status-4ex.sh

# Setup log rotation
log_info "Setting up log rotation..."
cat > /etc/logrotate.d/4ex-nginx << 'EOF'
/var/log/nginx/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 `cat /var/run/nginx.pid`
        fi
    endscript
}
EOF

cat > /etc/logrotate.d/4ex-supervisor << 'EOF'
/var/log/supervisor/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

# Final system check
log_info "Performing final system check..."

# Check if all services are running
sleep 5
backend_status=$(supervisorctl status 4ex-backend | grep RUNNING || echo "FAILED")
frontend_status=$(supervisorctl status 4ex-frontend | grep RUNNING || echo "FAILED")
nginx_status=$(systemctl is-active nginx || echo "FAILED")

echo "================================"
echo "Setup Complete! Summary:"
echo "================================"
echo "Backend Service: $backend_status"
echo "Frontend Service: $frontend_status"  
echo "Nginx Status: $nginx_status"
echo ""
echo "Domains configured:"
echo "  - https://$DOMAIN_MAIN (Frontend)"
echo "  - https://$DOMAIN_API (Backend API)"
echo ""
echo "Useful commands:"
echo "  - Update application: /usr/local/bin/update-4ex.sh"
echo "  - Check status: /usr/local/bin/status-4ex.sh"
echo "  - SSL test: /usr/local/bin/ssl-test.sh"
echo "  - View backend logs: supervisorctl tail -f 4ex-backend"
echo "  - View frontend logs: supervisorctl tail -f 4ex-frontend"
echo "  - Restart services: supervisorctl restart all"
echo ""
echo "Next steps:"
echo "  1. Point your DNS records to this server IP"
echo "  2. Test the application at https://$DOMAIN_MAIN"
echo "  3. Monitor logs and system performance"
echo "  4. Configure monitoring and alerting"
echo ""

if [[ "$backend_status" == *"RUNNING"* ]] && [[ "$frontend_status" == *"RUNNING"* ]] && [[ "$nginx_status" == "active" ]]; then
    log_info "✅ All services are running successfully!"
else
    log_warn "⚠️  Some services may need attention. Run /usr/local/bin/status-4ex.sh for details."
fi

log_info "4ex.ninja production setup completed!"
