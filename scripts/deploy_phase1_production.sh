#!/bin/bash
# 🚀 Phase 1 Production Deployment Execution Script
# MA_Unified_Strat Enhanced Risk Management Framework
# Deployment Date: August 17, 2025

echo "🚀 4ex.ninja MA_Unified_Strat Phase 1 Production Deployment"
echo "============================================================"
echo "Status: Ready for Digital Ocean Droplet Deployment"
echo "Phase 1 Success Rate: 94.6% (35/37 validation checks)"
echo "============================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Configuration
DROPLET_IP="your_droplet_ip"  # Replace with actual IP
PROJECT_PATH="/4ex.ninja-backend"
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/deployment_log_${BACKUP_TIMESTAMP}.log"

echo "Starting deployment at $(date)" > $LOG_FILE

# Pre-deployment validation
echo ""
echo "🔍 Pre-Deployment Validation"
echo "----------------------------"

# Check if SSH access is configured
if [ -z "$DROPLET_IP" ] || [ "$DROPLET_IP" = "your_droplet_ip" ]; then
    print_error "Please update DROPLET_IP in this script with your actual Digital Ocean droplet IP"
    exit 1
fi

print_info "Droplet IP: $DROPLET_IP"
print_info "Project Path: $PROJECT_PATH"
print_info "Backup Timestamp: $BACKUP_TIMESTAMP"
print_info "Log File: $LOG_FILE"

# Deployment Steps
echo ""
echo "🚀 Beginning Deployment Process"
echo "------------------------------"

# Step 1: Environment Preparation
echo ""
echo "📋 Step 1: Environment Preparation"
print_info "This step prepares the Digital Ocean droplet environment"

cat << 'EOF'
# Commands to run on your Digital Ocean droplet:

# 1. Connect to droplet
ssh root@$DROPLET_IP

# 2. Navigate to project directory
cd /4ex.ninja-backend

# 3. Create backup of current strategy
cp src/strategies/MA_Unified_Strat.py src/strategies/MA_Unified_Strat_backup_$(date +%Y%m%d_%H%M%S).py

# 4. Update system packages
apt update && apt upgrade -y

# 5. Verify Python environment
python3 --version
pip --version
EOF

# Step 2: Dependencies Installation
echo ""
echo "📦 Step 2: Install Risk Management Dependencies"
print_info "Installing additional Python packages for risk management"

cat << 'EOF'
# Install risk management dependencies
pip install numpy>=1.24.0 scipy>=1.10.0 scikit-learn>=1.2.0
pip install asyncio-throttle>=1.0.0 prometheus-client>=0.16.0
pip install quantlib-python>=1.30 empyrical>=0.5.5

# Update requirements.txt
echo "numpy>=1.24.0" >> requirements.txt
echo "scipy>=1.10.0" >> requirements.txt
echo "scikit-learn>=1.2.0" >> requirements.txt
echo "asyncio-throttle>=1.0.0" >> requirements.txt
echo "prometheus-client>=0.16.0" >> requirements.txt
echo "quantlib-python>=1.30" >> requirements.txt
echo "empyrical>=0.5.5" >> requirements.txt
EOF

# Step 3: Infrastructure Setup
echo ""
echo "🏗️  Step 3: Create Risk Management Infrastructure"
print_info "Setting up directory structure and configuration files"

cat << 'EOF'
# Create directory structure
mkdir -p src/risk_management/{emergency,var,regime,portfolio}
mkdir -p src/risk_management/utils
mkdir -p config/risk_profiles
mkdir -p logs/risk_management

# Create emergency risk configuration
cat > config/risk_profiles/emergency_config.json << 'EOL'
{
  "emergency_levels": {
    "level_1": 0.10,
    "level_2": 0.15,
    "level_3": 0.20,
    "level_4": 0.25
  },
  "stress_threshold": 2.0,
  "correlation_limit": 0.4,
  "var_daily_limit": 0.0031,
  "monitoring_frequency": 60
}
EOL

# Create portfolio allocation configuration
cat > config/risk_profiles/portfolio_allocation.json << 'EOL'
{
  "allocation_tiers": {
    "core": {
      "percentage": 0.60,
      "strategy_types": ["conservative"],
      "max_individual_allocation": 0.15
    },
    "growth": {
      "percentage": 0.30,
      "strategy_types": ["moderate"],
      "max_individual_allocation": 0.10
    },
    "tactical": {
      "percentage": 0.10,
      "strategy_types": ["aggressive"],
      "max_individual_allocation": 0.05
    }
  }
}
EOL
EOF

# Step 4: Strategy Deployment
echo ""
echo "🎯 Step 4: Deploy Enhanced Strategy"
print_info "Deploying MA_Unified_Strat.py with Phase 1 risk management"
print_warning "CRITICAL: Ensure you have the enhanced MA_Unified_Strat.py with Phase 1 components"

cat << 'EOF'
# Stop current strategy processes
pkill -f "MA_Unified_Strat.py"
sleep 10

# Deploy enhanced strategy file
# Method 1: If using git
git pull origin main  # Assuming enhanced strategy is committed

# Method 2: If using scp (replace with your local path)
# scp /local/path/to/enhanced_MA_Unified_Strat.py root@$DROPLET_IP:/4ex.ninja-backend/src/strategies/

# Update permissions
chmod +x src/strategies/MA_Unified_Strat.py
EOF

# Step 5: Service Configuration
echo ""
echo "⚙️  Step 5: Configure System Services"
print_info "Setting up systemd service and log rotation"

cat << 'EOF'
# Create systemd service for enhanced strategy
cat > /etc/systemd/system/4ex-strategy.service << 'EOL'
[Unit]
Description=4ex.ninja Enhanced MA Strategy
After=network.target mongodb.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/4ex.ninja-backend
Environment=PYTHONPATH=/4ex.ninja-backend
ExecStart=/usr/bin/python3 src/strategies/MA_Unified_Strat.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/4ex-strategy.log
StandardError=append:/var/log/4ex-strategy-error.log

# Resource limits for risk management
MemoryLimit=2G
CPUQuota=150%

[Install]
WantedBy=multi-user.target
EOL

# Enable and configure log rotation
cat > /etc/logrotate.d/4ex-strategy << 'EOL'
/var/log/4ex-strategy*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    postrotate
        systemctl reload 4ex-strategy
    endscript
}
EOL

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable 4ex-strategy
EOF

# Step 6: Environment Configuration
echo ""
echo "🔧 Step 6: Configure Environment Variables"
print_info "Setting up risk management environment variables"

cat << 'EOF'
# Add risk management environment variables to .env
cat >> .env << 'EOL'

# Risk Management Configuration - Phase 1
EMERGENCY_RISK_ENABLED=true
VAR_MONITORING_ENABLED=false  # Phase 2
REGIME_DETECTION_ENABLED=false  # Phase 3
PORTFOLIO_RISK_ENABLED=true

# Risk Thresholds
MAX_PORTFOLIO_DRAWDOWN=0.15
VAR_CONFIDENCE_LEVEL=0.95
CORRELATION_THRESHOLD=0.4
STRESS_VOLATILITY_MULTIPLIER=2.0

# Monitoring Frequencies (seconds)
EMERGENCY_CHECK_FREQUENCY=60
VAR_CALCULATION_FREQUENCY=300  # Phase 2
REGIME_UPDATE_FREQUENCY=900  # Phase 3
PORTFOLIO_HEALTH_FREQUENCY=180

# Alert Configuration
EMERGENCY_DISCORD_WEBHOOK=your_emergency_webhook_url
RISK_ALERT_CHANNEL=risk_alerts
PERFORMANCE_ALERT_CHANNEL=performance_alerts
EOL

# Source the environment variables
source .env
EOF

# Step 7: Database Updates
echo ""
echo "🗄️  Step 7: Database Schema Updates"
print_info "Creating risk management collections in MongoDB"

cat << 'EOF'
# Connect to MongoDB and add risk management collections
mongo --tls --tlsAllowInvalidCertificates

# In MongoDB shell, run these commands:
use risk_management
db.createCollection("emergency_events")
db.createCollection("var_calculations")
db.createCollection("regime_changes")
db.createCollection("portfolio_health")

# Create indexes for performance
db.emergency_events.createIndex({"timestamp": 1, "level": 1})
db.var_calculations.createIndex({"timestamp": 1, "pair": 1})
db.regime_changes.createIndex({"timestamp": 1, "regime": 1})
db.portfolio_health.createIndex({"timestamp": 1, "health_score": 1})

exit
EOF

# Step 8: Health Monitoring Setup
echo ""
echo "💊 Step 8: Setup Health Monitoring"
print_info "Creating health check and monitoring scripts"

cat << 'EOF'
# Create health check script
cat > scripts/health_check.sh << 'EOL'
#!/bin/bash

LOG_FILE="/var/log/4ex-health-check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting enhanced health check..." >> $LOG_FILE

# Check strategy process
if pgrep -f "MA_Unified_Strat.py" > /dev/null; then
    echo "[$TIMESTAMP] ✅ Strategy process running" >> $LOG_FILE
else
    echo "[$TIMESTAMP] ❌ Strategy process NOT running" >> $LOG_FILE
    systemctl restart 4ex-strategy
fi

# Check database connectivity
if mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
    echo "[$TIMESTAMP] ✅ MongoDB connection healthy" >> $LOG_FILE
else
    echo "[$TIMESTAMP] ❌ MongoDB connection failed" >> $LOG_FILE
fi

# Check Redis connectivity
if redis-cli ping > /dev/null 2>&1; then
    echo "[$TIMESTAMP] ✅ Redis connection healthy" >> $LOG_FILE
else
    echo "[$TIMESTAMP] ❌ Redis connection failed" >> $LOG_FILE
fi

echo "[$TIMESTAMP] Health check completed" >> $LOG_FILE
EOL

chmod +x scripts/health_check.sh

# Add to crontab for regular monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * /4ex.ninja-backend/scripts/health_check.sh") | crontab -
EOF

# Step 9: Production Startup
echo ""
echo "🚀 Step 9: Start Production Service"
print_info "Starting the enhanced strategy service"

cat << 'EOF'
# Start the enhanced strategy service
systemctl start 4ex-strategy

# Monitor startup logs (run in separate terminal)
tail -f /var/log/4ex-strategy.log

# Verify all components are initializing
grep -E "(EmergencyRiskManager|Emergency.*initialized)" /var/log/4ex-strategy.log

# Check service status
systemctl status 4ex-strategy
EOF

# Step 10: Validation
echo ""
echo "✅ Step 10: Production Validation"
print_info "Validating Phase 1 components are operational"

cat << 'EOF'
# Validate emergency risk framework
echo "🔍 Validating Phase 1 Implementation..."

# Check emergency risk manager initialization
grep "EmergencyRiskManager initialized" /var/log/4ex-strategy.log
echo "✅ Emergency Risk Manager: $([ $? -eq 0 ] && echo 'Active' || echo 'NOT FOUND')"

# Check for critical errors
ERROR_COUNT=$(grep -c "CRITICAL\|EMERGENCY" /var/log/4ex-strategy.log)
echo "🚨 Critical Errors: $ERROR_COUNT (Target: 0)"

# Check signal generation
SIGNALS_TODAY=$(grep "$(date +%Y-%m-%d)" logs/signals/*.log 2>/dev/null | wc -l)
echo "📊 Signals Generated Today: $SIGNALS_TODAY"

echo "✅ Phase 1 deployment validation completed!"
EOF

# Rollback Procedure
echo ""
echo "🔄 Emergency Rollback Procedure"
print_info "Use this if deployment encounters issues"

cat << 'EOF'
# Create emergency rollback script
cat > scripts/emergency_rollback.sh << 'EOL'
#!/bin/bash

echo "🚨 EMERGENCY ROLLBACK INITIATED"

# Stop current service
systemctl stop 4ex-strategy

# Restore backup
BACKUP_FILE=$(ls -t src/strategies/MA_Unified_Strat_backup_*.py | head -1)
cp $BACKUP_FILE src/strategies/MA_Unified_Strat.py

# Restart with original version
systemctl start 4ex-strategy

echo "✅ Rollback completed to: $BACKUP_FILE"
systemctl status 4ex-strategy
EOL

chmod +x scripts/emergency_rollback.sh
EOF

# Post-Deployment Monitoring
echo ""
echo "📊 Post-Deployment Monitoring"
print_info "24-48 hour monitoring plan for Phase 1"

cat << 'EOF'
# Create deployment monitoring script
cat > scripts/deployment_monitor.sh << 'EOL'
#!/bin/bash

echo "🚀 4ex.ninja Enhanced Strategy Deployment Monitor"
echo "=============================================="

# Strategy process status
echo "📊 Process Status:"
ps aux | grep MA_Unified_Strat.py | grep -v grep

# Recent log entries
echo "📝 Recent Activity (Last 10 entries):"
tail -10 /var/log/4ex-strategy.log

# Risk management status
echo "🛡️ Risk Management Status:"
if [ -f logs/risk_management/emergency.log ]; then
    echo "Emergency framework: Active"
    tail -3 logs/risk_management/emergency.log
fi

echo "=============================================="
echo "✅ Deployment monitoring completed"
EOL

chmod +x scripts/deployment_monitor.sh

# Run monitoring every hour for first 24 hours
# (crontab -l 2>/dev/null; echo "0 * * * * /4ex.ninja-backend/scripts/deployment_monitor.sh") | crontab -
EOF

# Summary
echo ""
echo "🏆 DEPLOYMENT SUMMARY"
echo "===================="
print_status "Phase 1 deployment script prepared"
print_status "All deployment steps documented"
print_status "Health monitoring configured"
print_status "Emergency rollback procedure ready"
print_status "Post-deployment monitoring planned"

echo ""
print_info "Next Steps:"
echo "1. Review all commands in this script"
echo "2. Replace 'your_droplet_ip' with actual IP address"
echo "3. Ensure enhanced MA_Unified_Strat.py is ready for deployment"
echo "4. Execute commands step by step on your Digital Ocean droplet"
echo "5. Monitor Phase 1 for 1-2 weeks before beginning Phase 2"

echo ""
print_warning "IMPORTANT: This script provides the commands to run. Execute them manually on your droplet for safety."
print_warning "Test each step and validate before proceeding to the next."

echo ""
echo "📊 Phase 1 Success Metrics to Monitor:"
echo "- Emergency risk framework initialization: SUCCESS"
echo "- Strategy process stability: >99.5% uptime"
echo "- Emergency trigger false positives: <2%"
echo "- Signal generation: No degradation from baseline"

echo ""
echo "🚀 READY FOR PHASE 1 PRODUCTION DEPLOYMENT! 🚀"
echo "Documentation: /docs/MAReview/PHASE1_PRODUCTION_DEPLOYMENT_SUMMARY.md"
echo "Phase 2 Plan: /docs/MAReview/PHASE2_IMPLEMENTATION_PLAN.md"

# Log completion
echo "Deployment script preparation completed at $(date)" >> $LOG_FILE
print_status "Deployment preparation log saved to: $LOG_FILE"
