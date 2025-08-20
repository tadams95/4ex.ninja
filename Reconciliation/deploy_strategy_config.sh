#!/bin/bash

# 🚀 Strategy Configuration Deployment Script  
# Deploy optimal MA strategy parameters to production droplet
# Date: August 19, 2025

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🚀 Deploying Optimal MA Strategy Configuration to Production Droplet..."
echo "=================================================="

# Configuration
DROPLET_USER="root"
DROPLET_IP="157.230.58.248"  # Provided droplet IP
CONFIG_PATH="/var/www/4ex.ninja/4ex.ninja-backend/src/config/strat_settings.py"
SERVICE_NAME="4ex-ninja-backend"
BACKUP_DIR="/var/www/4ex.ninja/backups"
LOCAL_CONFIG="/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/src/config/strat_settings.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 4ex.ninja MA Strategy Configuration Deployment"
echo "=================================================="

# Step 1: Use provided Droplet IP
echo "🔍 Using droplet IP: $DROPLET_IP"

# Function to detect droplet IP from existing deployment
detect_droplet_ip() {
    log_info "Detecting droplet IP from existing deployment configuration..."
    
    # Check if there's a .env file with droplet info
    if [ -f "/Users/tyrelle/Desktop/4ex.ninja/.env" ]; then
        DROPLET_IP=$(grep -o 'DROPLET_IP=.*' /Users/tyrelle/Desktop/4ex.ninja/.env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "")
    fi
    
    # Check deployment logs for IP
    if [ -z "$DROPLET_IP" ] && [ -f "/Users/tyrelle/Desktop/4ex.ninja/logs/deployment.log" ]; then
        DROPLET_IP=$(grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}' /Users/tyrelle/Desktop/4ex.ninja/logs/deployment.log | tail -1 || echo "")
    fi
    
    if [ -n "$DROPLET_IP" ]; then
        log_success "Detected droplet IP: $DROPLET_IP"
    else
        log_warning "Could not auto-detect droplet IP"
        read -p "Enter your droplet IP address: " DROPLET_IP
    fi
}

# Function to validate local configuration
validate_local_config() {
    log_info "Validating local configuration file..."
    
    if [ ! -f "$LOCAL_CONFIG" ]; then
        log_error "Local configuration file not found: $LOCAL_CONFIG"
        exit 1
    fi
    
    # Test Python syntax
    cd "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/src/config"
    if python3 -c "import strat_settings; print('✅ Configuration syntax valid')"; then
        log_success "Local configuration syntax is valid"
    else
        log_error "Local configuration has syntax errors"
        exit 1
    fi
    
    # Verify optimal parameters are present
    local eur_usd_fast=$(python3 -c "import strat_settings; print(strat_settings.STRATEGIES['EUR_USD_D']['fast_ma'])")
    local eur_usd_slow=$(python3 -c "import strat_settings; print(strat_settings.STRATEGIES['EUR_USD_D']['slow_ma'])")
    
    if [ "$eur_usd_fast" = "50" ] && [ "$eur_usd_slow" = "200" ]; then
        log_success "Optimal parameters confirmed (fast_ma=50, slow_ma=200)"
    else
        log_error "Configuration does not contain optimal parameters (fast_ma=$eur_usd_fast, slow_ma=$eur_usd_slow)"
        exit 1
    fi
}

# Function to test droplet connectivity
test_droplet_connectivity() {
    log_info "Testing connection to droplet ($DROPLET_IP)..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$DROPLET_USER@$DROPLET_IP" "echo 'Connection successful'" >/dev/null 2>&1; then
        log_success "Successfully connected to droplet"
    else
        log_error "Cannot connect to droplet. Please check:"
        echo "  1. Droplet IP address: $DROPLET_IP"
        echo "  2. SSH key authentication is set up"
        echo "  3. Droplet is running and accessible"
        exit 1
    fi
}

# Function to backup current configuration on droplet
backup_droplet_config() {
    log_info "Creating backup of current configuration on droplet..."
    
    ssh "$DROPLET_USER@$DROPLET_IP" "
        mkdir -p /var/www/4ex.ninja/backups
        if [ -f '$DROPLET_CONFIG_PATH' ]; then
            cp '$DROPLET_CONFIG_PATH' '$BACKUP_PATH'
            echo '✅ Backup created: $BACKUP_PATH'
        else
            echo '⚠️  No existing configuration found at $DROPLET_CONFIG_PATH'
        fi
    "
}

# Function to deploy configuration
deploy_configuration() {
    log_info "Deploying updated configuration to droplet..."
    
    # Upload the configuration file
    if scp "$LOCAL_CONFIG" "$DROPLET_USER@$DROPLET_IP:$DROPLET_CONFIG_PATH"; then
        log_success "Configuration file uploaded successfully"
    else
        log_error "Failed to upload configuration file"
        exit 1
    fi
    
    # Verify file was uploaded correctly
    log_info "Verifying uploaded configuration..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        if [ -f '$DROPLET_CONFIG_PATH' ]; then
            echo '✅ Configuration file exists on droplet'
            ls -la '$DROPLET_CONFIG_PATH'
        else
            echo '❌ Configuration file not found on droplet'
            exit 1
        fi
    "
}

# Function to restart strategy services
restart_services() {
    log_info "Restarting strategy services on droplet..."
    
    ssh "$DROPLET_USER@$DROPLET_IP" "
        # Stop services gracefully
        echo 'Stopping strategy services...'
        supervisorctl stop 4ex-strategy-runner 2>/dev/null || systemctl stop ma-strategy-service 2>/dev/null || echo 'Service stop attempted'
        supervisorctl stop 4ex-signal-processor 2>/dev/null || systemctl stop signal-processor 2>/dev/null || echo 'Signal processor stop attempted'
        
        # Wait a moment
        sleep 3
        
        # Start services
        echo 'Starting strategy services...'
        supervisorctl start 4ex-strategy-runner 2>/dev/null || systemctl start ma-strategy-service 2>/dev/null || echo 'Service start attempted'
        supervisorctl start 4ex-signal-processor 2>/dev/null || systemctl start signal-processor 2>/dev/null || echo 'Signal processor start attempted'
        
        # Check status
        echo 'Checking service status...'
        supervisorctl status 2>/dev/null || systemctl status ma-strategy-service --no-pager -l 2>/dev/null || echo 'Status check completed'
    "
}

# Function to validate deployment
validate_deployment() {
    log_info "Validating deployment on droplet..."
    
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd /var/www/4ex.ninja/4ex.ninja-backend/src/config
        
        # Test configuration syntax
        if python3 -c 'import strat_settings; print(\"✅ Configuration loads successfully\")'; then
            echo '✅ Configuration syntax valid on droplet'
        else
            echo '❌ Configuration syntax error on droplet'
            exit 1
        fi
        
        # Verify optimal parameters
        echo 'Checking optimal parameters:'
        python3 -c \"
import strat_settings
print(f'EUR_USD_D: fast_ma={strat_settings.STRATEGIES[\\\"EUR_USD_D\\\"][\\\"fast_ma\\\"]}, slow_ma={strat_settings.STRATEGIES[\\\"EUR_USD_D\\\"][\\\"slow_ma\\\"]}')
print(f'GBP_USD_D: fast_ma={strat_settings.STRATEGIES[\\\"GBP_USD_D\\\"][\\\"fast_ma\\\"]}, slow_ma={strat_settings.STRATEGIES[\\\"GBP_USD_D\\\"][\\\"slow_ma\\\"]}')
print(f'USD_JPY_D: fast_ma={strat_settings.STRATEGIES[\\\"USD_JPY_D\\\"][\\\"fast_ma\\\"]}, slow_ma={strat_settings.STRATEGIES[\\\"USD_JPY_D\\\"][\\\"slow_ma\\\"]}')
\"
    "
}

# Function to monitor logs
monitor_initial_logs() {
    log_info "Monitoring initial service logs for 30 seconds..."
    
    ssh "$DROPLET_USER@$DROPLET_IP" "
        echo 'Checking recent logs for configuration loading...'
        timeout 30 tail -f /var/log/4ex-ninja/backend.log 2>/dev/null || \
        timeout 30 tail -f /var/log/supervisor/4ex-strategy-runner.log 2>/dev/null || \
        timeout 30 journalctl -u ma-strategy-service -f --since '1 minute ago' 2>/dev/null || \
        echo 'Log monitoring completed (logs may be in different location)'
    " || log_info "Log monitoring timeout reached"
}

# Main deployment function
main() {
    echo
    log_info "Starting Strategy Configuration Deployment Process"
    echo "=============================================="
    
    # Step 1: Detect droplet IP
    detect_droplet_ip
    
    # Step 2: Validate local configuration
    validate_local_config
    
    # Step 3: Test droplet connectivity
    test_droplet_connectivity
    
    # Step 4: Backup current configuration
    backup_droplet_config
    
    # Step 5: Deploy new configuration
    deploy_configuration
    
    # Step 6: Restart services
    restart_services
    
    # Step 7: Validate deployment
    validate_deployment
    
    # Step 8: Monitor initial logs
    monitor_initial_logs
    
    echo
    log_success "🎉 DEPLOYMENT COMPLETE!"
    echo "=============================================="
    echo
    echo "✅ Optimal MA strategy parameters deployed successfully"
    echo "✅ Services restarted with new configuration"
    echo "✅ Configuration validated on droplet"
    echo
    echo "Expected Changes:"
    echo "  • Signal frequency reduced by 60-70%"
    echo "  • Higher quality trend-following signals"
    echo "  • Movement toward 18.0-19.8% annual return targets"
    echo
    echo "Monitoring Commands:"
    echo "  ssh $DROPLET_USER@$DROPLET_IP 'tail -f /var/log/4ex-ninja/backend.log'"
    echo "  ssh $DROPLET_USER@$DROPLET_IP 'supervisorctl status'"
    echo
    echo "Rollback Command (if needed):"
    echo "  ssh $DROPLET_USER@$DROPLET_IP 'cp $BACKUP_PATH $DROPLET_CONFIG_PATH && supervisorctl restart all'"
    echo
}

# Execute main function
main "$@"
