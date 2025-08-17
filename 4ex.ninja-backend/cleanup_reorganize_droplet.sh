#!/bin/bash

# =============================================================================
# 4ex.ninja Digital Ocean Droplet Cleanup & Reorganization Script
# =============================================================================

echo "🧹 Starting 4ex.ninja Droplet Cleanup & Reorganization..."
echo "============================================================"

# Set script to exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Current working directory
CURRENT_DIR="/root"
PROJECT_DIR="/root/4ex.ninja-backend"

echo -e "${BLUE}📁 Creating clean project structure...${NC}"

# Create the main project directory if it doesn't exist
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create organized directory structure
echo -e "${YELLOW}Creating directory structure...${NC}"
mkdir -p {config,src,scripts,logs,backups,tests,docs}
mkdir -p config/risk_profiles
mkdir -p src/{strategies,risk_management,infrastructure,core,api,services,utils}
mkdir -p src/risk_management/{emergency,var,regime,portfolio,utils}
mkdir -p logs/{strategy,risk_management,system,archived}
mkdir -p scripts/{deployment,maintenance,monitoring}

echo -e "${GREEN}✅ Directory structure created${NC}"

# Backup existing files before moving
echo -e "${BLUE}💾 Creating backup of current files...${NC}"
BACKUP_DIR="$PROJECT_DIR/backups/migration_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Copy current files to backup
cp "$CURRENT_DIR"/*.py "$BACKUP_DIR/" 2>/dev/null || echo "No Python files to backup"
cp "$CURRENT_DIR"/*.txt "$BACKUP_DIR/" 2>/dev/null || echo "No text files to backup"
cp "$CURRENT_DIR"/*.json "$BACKUP_DIR/" 2>/dev/null || echo "No JSON files to backup"
cp "$CURRENT_DIR"/.env "$BACKUP_DIR/" 2>/dev/null || echo "No .env file to backup"

echo -e "${GREEN}✅ Backup created at $BACKUP_DIR${NC}"

# Move and organize existing files
echo -e "${BLUE}📦 Organizing existing files...${NC}"

# Move strategy files
if [ -f "$CURRENT_DIR/MA_Unified_Strat.py" ]; then
    mv "$CURRENT_DIR/MA_Unified_Strat.py" src/strategies/
    echo -e "${GREEN}✅ Moved main strategy file${NC}"
fi

# Move configuration files
if [ -d "$CURRENT_DIR/config" ]; then
    cp -r "$CURRENT_DIR/config/"* config/ 2>/dev/null || true
    echo -e "${GREEN}✅ Moved configuration files${NC}"
fi

# Move source code
if [ -d "$CURRENT_DIR/src" ]; then
    cp -r "$CURRENT_DIR/src/"* src/ 2>/dev/null || true
    echo -e "${GREEN}✅ Moved source code files${NC}"
fi

# Move requirements.txt
if [ -f "$CURRENT_DIR/requirements.txt" ]; then
    mv "$CURRENT_DIR/requirements.txt" .
    echo -e "${GREEN}✅ Moved requirements.txt${NC}"
fi

# Clean up old files from root
echo -e "${BLUE}🗑️ Cleaning up root directory...${NC}"
rm -f "$CURRENT_DIR"/MA_Unified_Strat*.py 2>/dev/null || true
rm -f "$CURRENT_DIR"/*.json 2>/dev/null || true
rm -f "$CURRENT_DIR"/debug_*.py 2>/dev/null || true
rm -f "$CURRENT_DIR"/test_*.py 2>/dev/null || true
rm -f "$CURRENT_DIR"/quick_*.py 2>/dev/null || true
rm -f "$CURRENT_DIR"/strategy_logs.txt 2>/dev/null || true
rm -f "$CURRENT_DIR"/stream_prices.py 2>/dev/null || true
rm -f "$CURRENT_DIR"/check_candles.py 2>/dev/null || true
rm -f "$CURRENT_DIR"/crossover_tracker.py 2>/dev/null || true
rm -f "$CURRENT_DIR"/real_time_monitor.py 2>/dev/null || true

echo -e "${GREEN}✅ Root directory cleaned${NC}"

# Create essential configuration files
echo -e "${BLUE}⚙️ Creating configuration files...${NC}"

# Create risk profiles configuration
cat > config/risk_profiles/emergency_config.json << 'EOF'
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
  "monitoring_frequency": 60,
  "alert_channels": {
    "level_1": "alerts_general",
    "level_2": "alerts_critical", 
    "level_3": "alerts_critical",
    "level_4": "alerts_critical"
  }
}
EOF

cat > config/risk_profiles/portfolio_allocation.json << 'EOF'
{
  "allocation_tiers": {
    "core": {
      "percentage": 0.60,
      "strategy_types": ["conservative"],
      "max_individual_allocation": 0.15,
      "target_pairs": ["USD_CAD", "AUD_USD", "USD_CHF", "USD_JPY", "EUR_USD"]
    },
    "growth": {
      "percentage": 0.30,
      "strategy_types": ["moderate"],
      "max_individual_allocation": 0.10,
      "target_pairs": ["GBP_USD", "EUR_GBP", "AUD_JPY"]
    },
    "tactical": {
      "percentage": 0.10,
      "strategy_types": ["aggressive"],
      "max_individual_allocation": 0.05,
      "target_pairs": ["GBP_JPY", "EUR_JPY"]
    }
  },
  "rebalancing": {
    "frequency": "weekly",
    "threshold": 0.05,
    "max_deviation": 0.10
  }
}
EOF

echo -e "${GREEN}✅ Risk configuration files created${NC}"

# Create essential scripts
echo -e "${BLUE}📜 Creating management scripts...${NC}"

# Health check script
cat > scripts/health_check.sh << 'EOF'
#!/bin/bash

# Enhanced health check for 4ex.ninja strategy
LOG_FILE="/root/4ex.ninja-backend/logs/system/health_check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting enhanced health check..." >> $LOG_FILE

# Check strategy process
if pgrep -f "MA_Unified_Strat.py" > /dev/null; then
    echo "[$TIMESTAMP] ✅ Strategy process running" >> $LOG_FILE
else
    echo "[$TIMESTAMP] ❌ Strategy process NOT running" >> $LOG_FILE
    # Auto-restart if systemd service exists
    if systemctl is-enabled 4ex-strategy >/dev/null 2>&1; then
        systemctl restart 4ex-strategy
        echo "[$TIMESTAMP] 🔄 Strategy service restarted" >> $LOG_FILE
    fi
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
    echo "[$TIMESTAMP] ⚠️ Redis connection failed (optional)" >> $LOG_FILE
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo "[$TIMESTAMP] ✅ Disk space OK ($DISK_USAGE%)" >> $LOG_FILE
else
    echo "[$TIMESTAMP] ⚠️ Disk space warning ($DISK_USAGE%)" >> $LOG_FILE
fi

# Check memory usage
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEMORY_USAGE -lt 85 ]; then
    echo "[$TIMESTAMP] ✅ Memory usage OK ($MEMORY_USAGE%)" >> $LOG_FILE
else
    echo "[$TIMESTAMP] ⚠️ Memory usage high ($MEMORY_USAGE%)" >> $LOG_FILE
fi

echo "[$TIMESTAMP] Health check completed" >> $LOG_FILE
EOF

chmod +x scripts/health_check.sh

# Deployment monitor script
cat > scripts/deployment_monitor.sh << 'EOF'
#!/bin/bash

echo "🚀 4ex.ninja Enhanced Strategy Deployment Monitor"
echo "=============================================="

# Strategy process status
echo "📊 Process Status:"
ps aux | grep MA_Unified_Strat.py | grep -v grep

# Memory and CPU usage
if pgrep -f MA_Unified_Strat.py > /dev/null; then
    echo "💻 Resource Usage:"
    ps -p $(pgrep -f MA_Unified_Strat.py) -o pid,ppid,%cpu,%mem,cmd
fi

# Recent log entries
echo "📝 Recent Activity (Last 10 entries):"
if [ -f logs/strategy/strategy.log ]; then
    tail -10 logs/strategy/strategy.log
else
    echo "No strategy logs found yet"
fi

# Risk management status
echo "🛡️ Risk Management Status:"
if [ -f logs/risk_management/emergency.log ]; then
    echo "Emergency framework: Active"
    tail -3 logs/risk_management/emergency.log
else
    echo "Emergency framework: Not active yet"
fi

echo "=============================================="
echo "✅ Deployment monitoring completed"
EOF

chmod +x scripts/deployment_monitor.sh

# Emergency rollback script
cat > scripts/emergency_rollback.sh << 'EOF'
#!/bin/bash

echo "🚨 EMERGENCY ROLLBACK INITIATED"

# Stop current service
if systemctl is-active --quiet 4ex-strategy; then
    systemctl stop 4ex-strategy
    echo "✅ Service stopped"
fi

# Find latest backup
BACKUP_DIR="/root/4ex.ninja-backend/backups"
LATEST_BACKUP=$(ls -t $BACKUP_DIR/migration_*/MA_Unified_Strat.py 2>/dev/null | head -1)

if [ -n "$LATEST_BACKUP" ]; then
    cp "$LATEST_BACKUP" src/strategies/MA_Unified_Strat.py
    echo "✅ Rollback completed to: $LATEST_BACKUP"
else
    echo "❌ No backup found for rollback"
    exit 1
fi

# Restart service
if systemctl is-enabled --quiet 4ex-strategy; then
    systemctl start 4ex-strategy
    echo "✅ Service restarted"
fi

systemctl status 4ex-strategy
EOF

chmod +x scripts/emergency_rollback.sh

echo -e "${GREEN}✅ Management scripts created${NC}"

# Create README
cat > README.md << 'EOF'
# 4ex.ninja Backend - Enhanced Trading Strategy

## Project Structure

```
4ex.ninja-backend/
├── config/                 # Configuration files
├── src/                    # Source code
│   ├── strategies/         # Trading strategies
│   ├── risk_management/    # Risk management modules
│   └── infrastructure/     # Supporting infrastructure
├── scripts/               # Management scripts
├── logs/                  # Application logs
├── backups/               # Backups and migrations
└── docs/                  # Documentation
```

## Quick Start

1. Ensure environment variables are set in `.env`
2. Install dependencies: `pip install -r requirements.txt`
3. Run strategy: `python src/strategies/MA_Unified_Strat.py`

## Management Scripts

- `scripts/health_check.sh` - System health monitoring
- `scripts/deployment_monitor.sh` - Deployment status
- `scripts/emergency_rollback.sh` - Emergency rollback

## Monitoring

- Strategy logs: `logs/strategy/`
- Risk management logs: `logs/risk_management/`
- System logs: `logs/system/`
EOF

echo -e "${GREEN}✅ Documentation created${NC}"

# Set proper permissions
echo -e "${BLUE}🔒 Setting permissions...${NC}"
chmod -R 755 scripts/
chmod 644 config/*.py config/*.json
chmod 600 .env* 2>/dev/null || true

echo -e "${GREEN}✅ Permissions set${NC}"

# Create symlink for easy access
ln -sf "$PROJECT_DIR" /root/project 2>/dev/null || true

echo ""
echo -e "${GREEN}🎉 CLEANUP AND REORGANIZATION COMPLETE!${NC}"
echo ""
echo -e "${BLUE}📁 New project location: $PROJECT_DIR${NC}"
echo -e "${BLUE}🔗 Quick access symlink: /root/project${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Copy your complete .env file to the project directory"
echo "2. Update your environment variables"
echo "3. Test the health check: ./scripts/health_check.sh"
echo "4. Deploy the enhanced strategy"
echo ""
echo -e "${GREEN}✅ Ready for enhanced strategy deployment!${NC}"
EOF
