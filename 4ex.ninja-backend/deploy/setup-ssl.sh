#!/bin/bash
# SSL Certificate Setup Script for 4ex.ninja
# This script sets up Let's Encrypt SSL certificates for all domains

set -e

# Configuration
DOMAINS=(
    "4ex.ninja"
    "www.4ex.ninja" 
    "api.4ex.ninja"
)
EMAIL="admin@4ex.ninja"  # Change this to your email
NGINX_CONFIG_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
CERTBOT_WEBROOT="/var/www/certbot"

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

log_info "Starting SSL setup for 4ex.ninja..."

# Update system
log_info "Updating system packages..."
apt-get update -q

# Install required packages
log_info "Installing required packages..."
apt-get install -y nginx certbot python3-certbot-nginx

# Create webroot directory for certbot
log_info "Setting up certbot webroot..."
mkdir -p "$CERTBOT_WEBROOT"
chown -R www-data:www-data "$CERTBOT_WEBROOT"

# Create temporary nginx config for initial certificate generation
log_info "Creating temporary nginx configuration..."
cat > /etc/nginx/sites-available/temp-ssl-setup << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name 4ex.ninja www.4ex.ninja api.4ex.ninja;

    # Allow Let's Encrypt challenges
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        allow all;
    }

    # Temporary response for other requests
    location / {
        return 200 "SSL setup in progress...";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable temporary config
ln -sf /etc/nginx/sites-available/temp-ssl-setup /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
log_info "Testing nginx configuration..."
nginx -t
if [[ $? -ne 0 ]]; then
    log_error "Nginx configuration test failed"
    exit 1
fi

# Start/restart nginx
log_info "Starting nginx..."
systemctl enable nginx
systemctl restart nginx

# Wait for nginx to start
sleep 2

# Check if nginx is running
if ! systemctl is-active --quiet nginx; then
    log_error "Nginx failed to start"
    exit 1
fi

# Generate SSL certificates
log_info "Generating SSL certificates..."

# Main domain certificate
log_info "Getting certificate for main domain..."
certbot certonly \
    --webroot \
    --webroot-path="$CERTBOT_WEBROOT" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --domains 4ex.ninja,www.4ex.ninja

if [[ $? -ne 0 ]]; then
    log_error "Failed to generate certificate for main domain"
    exit 1
fi

# API domain certificate  
log_info "Getting certificate for API domain..."
certbot certonly \
    --webroot \
    --webroot-path="$CERTBOT_WEBROOT" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --domains api.4ex.ninja

if [[ $? -ne 0 ]]; then
    log_error "Failed to generate certificate for API domain"
    exit 1
fi

# Set up certificate renewal
log_info "Setting up automatic certificate renewal..."

# Create renewal script
cat > /usr/local/bin/certbot-renew.sh << 'EOF'
#!/bin/bash
# Certificate renewal script

/usr/bin/certbot renew --quiet --webroot --webroot-path=/var/www/certbot

# Reload nginx if certificates were renewed
if [[ $? -eq 0 ]]; then
    /usr/bin/systemctl reload nginx
fi
EOF

chmod +x /usr/local/bin/certbot-renew.sh

# Create cron job for renewal (twice daily as recommended)
cat > /etc/cron.d/certbot-renew << 'EOF'
# Automatically renew Let's Encrypt certificates
0 */12 * * * root /usr/local/bin/certbot-renew.sh >/dev/null 2>&1
EOF

# Test renewal process
log_info "Testing certificate renewal..."
certbot renew --dry-run
if [[ $? -ne 0 ]]; then
    log_warn "Certificate renewal test failed - manual intervention may be needed"
fi

# Install the production nginx configuration
log_info "Installing production nginx configuration..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy nginx configuration
cp "$SCRIPT_DIR/nginx/4ex-ninja.conf" "$NGINX_CONFIG_DIR/"

# Enable the site
ln -sf "$NGINX_CONFIG_DIR/4ex-ninja.conf" "$NGINX_ENABLED_DIR/"

# Remove temporary config
rm -f "$NGINX_ENABLED_DIR/temp-ssl-setup"

# Test nginx configuration with SSL
log_info "Testing nginx configuration with SSL..."
nginx -t
if [[ $? -ne 0 ]]; then
    log_error "Nginx SSL configuration test failed"
    exit 1
fi

# Reload nginx with new configuration
log_info "Reloading nginx with SSL configuration..."
systemctl reload nginx

# Verify SSL is working
log_info "Verifying SSL setup..."
sleep 3

# Test each domain
for domain in "${DOMAINS[@]}"; do
    log_info "Testing SSL for $domain..."
    if curl -sSf "https://$domain/health" >/dev/null 2>&1 || curl -sSf "https://$domain/" >/dev/null 2>&1; then
        log_info "✓ SSL working for $domain"
    else
        log_warn "⚠ SSL test failed for $domain (service may not be running yet)"
    fi
done

# Create SSL monitoring script
log_info "Creating SSL monitoring script..."
cat > /usr/local/bin/ssl-monitor.sh << 'EOF'
#!/bin/bash
# SSL Certificate Monitoring Script

DOMAINS=("4ex.ninja" "www.4ex.ninja" "api.4ex.ninja")
NOTIFY_DAYS=30
EMAIL="admin@4ex.ninja"

for domain in "${DOMAINS[@]}"; do
    expiry_date=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
    expiry_epoch=$(date -d "$expiry_date" +%s)
    current_epoch=$(date +%s)
    days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    if [[ $days_until_expiry -le $NOTIFY_DAYS ]]; then
        echo "WARNING: SSL certificate for $domain expires in $days_until_expiry days"
        # Add notification logic here (email, Slack, etc.)
    fi
done
EOF

chmod +x /usr/local/bin/ssl-monitor.sh

# Add SSL monitoring to cron (weekly check)
cat > /etc/cron.d/ssl-monitor << 'EOF'
# Monitor SSL certificate expiration
0 0 * * 0 root /usr/local/bin/ssl-monitor.sh >/dev/null 2>&1
EOF

# Create SSL security test script
log_info "Creating SSL security test script..."
cat > /usr/local/bin/ssl-test.sh << 'EOF'
#!/bin/bash
# SSL Security Test Script

DOMAINS=("4ex.ninja" "www.4ex.ninja" "api.4ex.ninja")

echo "SSL Security Test Results:"
echo "=========================="

for domain in "${DOMAINS[@]}"; do
    echo "Testing $domain..."
    
    # Test SSL grade using SSL Labs API (requires internet)
    if command -v curl >/dev/null 2>&1; then
        echo "  Checking SSL configuration..."
        curl -s "https://api.ssllabs.com/api/v3/analyze?host=$domain&fromCache=on" | grep -o '"grade":"[^"]*"' | head -1
    fi
    
    # Test security headers
    echo "  Security headers test:"
    headers=$(curl -sI "https://$domain/" 2>/dev/null)
    
    if echo "$headers" | grep -q "Strict-Transport-Security"; then
        echo "    ✓ HSTS enabled"
    else
        echo "    ✗ HSTS missing"
    fi
    
    if echo "$headers" | grep -q "X-Content-Type-Options"; then
        echo "    ✓ Content-Type-Options header present"
    else
        echo "    ✗ Content-Type-Options header missing"
    fi
    
    if echo "$headers" | grep -q "X-Frame-Options"; then
        echo "    ✓ X-Frame-Options header present"
    else
        echo "    ✗ X-Frame-Options header missing"
    fi
    
    echo ""
done
EOF

chmod +x /usr/local/bin/ssl-test.sh

# Final status check
log_info "SSL setup complete! Summary:"
echo "================================"
echo "Certificates installed for:"
for domain in "${DOMAINS[@]}"; do
    echo "  - $domain"
done
echo ""
echo "Services configured:"
echo "  - Nginx with SSL termination"
echo "  - Automatic certificate renewal"
echo "  - SSL monitoring"
echo ""
echo "Useful commands:"
echo "  - Test SSL: /usr/local/bin/ssl-test.sh"
echo "  - Check renewal: certbot certificates"
echo "  - Manual renewal: certbot renew"
echo "  - Nginx reload: systemctl reload nginx"
echo ""
echo "Next steps:"
echo "  1. Start your application services"
echo "  2. Test the complete application"
echo "  3. Configure DNS to point to this server"
echo "  4. Run security tests"

log_info "SSL setup completed successfully!"
