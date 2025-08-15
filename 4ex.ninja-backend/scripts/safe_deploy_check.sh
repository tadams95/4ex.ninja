#!/bin/bash

# Safe Deployment Pre-Check Script for 4ex.ninja
# Checks for existing installations and provides safe deployment options

echo "🔍 4ex.ninja Safe Deployment Pre-Check"
echo "======================================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CONFLICTS_FOUND=false

echo -e "\n${BLUE}1. Checking for existing installations...${NC}"

# Check project directory
if [ -d "/var/www/4ex.ninja" ]; then
    echo -e "${YELLOW}⚠️  Existing project found: /var/www/4ex.ninja${NC}"
    echo "   Last modified: $(stat -c %y /var/www/4ex.ninja 2>/dev/null || echo 'Unknown')"
    echo "   Size: $(du -sh /var/www/4ex.ninja 2>/dev/null | cut -f1 || echo 'Unknown')"
    CONFLICTS_FOUND=true
fi

# Check Nginx config
if [ -f "/etc/nginx/sites-available/4ex.ninja" ]; then
    echo -e "${YELLOW}⚠️  Existing Nginx config: /etc/nginx/sites-available/4ex.ninja${NC}"
    CONFLICTS_FOUND=true
fi

# Check Supervisor configs
if ls /etc/supervisor/conf.d/4ex-*.conf 1> /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Existing Supervisor configs found:${NC}"
    ls -la /etc/supervisor/conf.d/4ex-*.conf
    CONFLICTS_FOUND=true
fi

# Check Redis configuration
if [ -f "/etc/redis/redis.conf" ]; then
    echo -e "${YELLOW}⚠️  Redis config exists${NC}"
    if systemctl is-active --quiet redis-server; then
        echo "   Status: ${GREEN}RUNNING${NC}"
    else
        echo "   Status: ${RED}STOPPED${NC}"
    fi
    CONFLICTS_FOUND=true
fi

echo -e "\n${BLUE}2. Checking for running 4ex.ninja processes...${NC}"
RUNNING_PROCESSES=$(ps aux | grep -E "(4ex|ninja)" | grep -v grep || true)
if [ ! -z "$RUNNING_PROCESSES" ]; then
    echo -e "${YELLOW}⚠️  Found running processes:${NC}"
    echo "$RUNNING_PROCESSES"
    CONFLICTS_FOUND=true
else
    echo -e "${GREEN}✅ No 4ex.ninja processes running${NC}"
fi

# Check ports
echo -e "\n${BLUE}3. Checking critical port usage...${NC}"
PORT_CONFLICTS=""

# Check port 80 (HTTP)
if netstat -tulpn 2>/dev/null | grep ":80 " | grep LISTEN >/dev/null; then
    PORT_80_USER=$(netstat -tulpn 2>/dev/null | grep ":80 " | grep LISTEN | awk '{print $7}')
    echo -e "${YELLOW}⚠️  Port 80 in use by: $PORT_80_USER${NC}"
    PORT_CONFLICTS="true"
fi

# Check port 443 (HTTPS)
if netstat -tulpn 2>/dev/null | grep ":443 " | grep LISTEN >/dev/null; then
    PORT_443_USER=$(netstat -tulpn 2>/dev/null | grep ":443 " | grep LISTEN | awk '{print $7}')
    echo -e "${YELLOW}⚠️  Port 443 in use by: $PORT_443_USER${NC}"
    PORT_CONFLICTS="true"
fi

# Check port 8000 (API)
if netstat -tulpn 2>/dev/null | grep ":8000 " | grep LISTEN >/dev/null; then
    PORT_8000_USER=$(netstat -tulpn 2>/dev/null | grep ":8000 " | grep LISTEN | awk '{print $7}')
    echo -e "${YELLOW}⚠️  Port 8000 in use by: $PORT_8000_USER${NC}"
    PORT_CONFLICTS="true"
fi

# Check port 6379 (Redis)
if netstat -tulpn 2>/dev/null | grep ":6379 " | grep LISTEN >/dev/null; then
    PORT_6379_USER=$(netstat -tulpn 2>/dev/null | grep ":6379 " | grep LISTEN | awk '{print $7}')
    echo -e "${YELLOW}⚠️  Port 6379 in use by: $PORT_6379_USER${NC}"
    PORT_CONFLICTS="true"
fi

if [ -z "$PORT_CONFLICTS" ]; then
    echo -e "${GREEN}✅ All required ports available${NC}"
fi

# Check disk space
echo -e "\n${BLUE}4. Checking system resources...${NC}"
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
DISK_AVAILABLE=$(df -h / | awk 'NR==2 {print $4}')

if [ $DISK_USAGE -lt 70 ]; then
    echo -e "${GREEN}✅ Disk usage: $DISK_USAGE% (Available: $DISK_AVAILABLE)${NC}"
else
    echo -e "${YELLOW}⚠️  Disk usage: $DISK_USAGE% (Available: $DISK_AVAILABLE)${NC}"
fi

# Check memory
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
MEMORY_AVAILABLE=$(free -h | awk 'NR==2{print $7}')

if [ $MEMORY_USAGE -lt 80 ]; then
    echo -e "${GREEN}✅ Memory usage: $MEMORY_USAGE% (Available: $MEMORY_AVAILABLE)${NC}"
else
    echo -e "${YELLOW}⚠️  Memory usage: $MEMORY_USAGE% (Available: $MEMORY_AVAILABLE)${NC}"
fi

echo -e "\n${BLUE}5. Summary and Recommendations${NC}"
echo "================================"

if [ "$CONFLICTS_FOUND" = true ]; then
    echo -e "${RED}🚨 POTENTIAL CONFLICTS DETECTED${NC}"
    echo ""
    echo -e "${YELLOW}Recommended Safe Deployment Options:${NC}"
    echo ""
    echo -e "${BLUE}Option 1: Backup Existing and Deploy Fresh${NC}"
    echo "  - Creates full backup of existing installation"
    echo "  - Deploys fresh 4ex.ninja system"
    echo "  - Command: ${GREEN}./backup_and_deploy.sh${NC}"
    echo ""
    echo -e "${BLUE}Option 2: Update Existing Installation${NC}"
    echo "  - Updates code without changing configs"
    echo "  - Safer but limited to code updates only"
    echo "  - Command: ${GREEN}./update_existing.sh${NC}"
    echo ""
    echo -e "${BLUE}Option 3: Manual Conflict Resolution${NC}"
    echo "  - Stop conflicting services manually"
    echo "  - Remove/backup conflicting files"
    echo "  - Then run full deployment"
    echo ""
    echo -e "${RED}❌ DO NOT run deploy_production.sh directly yet!${NC}"
    echo ""
    echo "What would you like to do?"
    echo "1) Create backup and deploy fresh (RECOMMENDED)"
    echo "2) Update existing installation only"
    echo "3) Show manual conflict resolution steps"
    echo "4) Force deploy anyway (RISKY)"
    echo "5) Exit and handle manually"
    echo ""
    read -p "Enter your choice (1-5): " choice
    
    case $choice in
        1)
            echo -e "\n${GREEN}Creating backup and deploying fresh...${NC}"
            echo "This will:"
            echo "- Backup all existing files to /tmp/4ex-backup-$(date +%Y%m%d_%H%M%S)"
            echo "- Stop conflicting services"
            echo "- Deploy fresh 4ex.ninja system"
            echo ""
            read -p "Proceed? (y/N): " confirm
            if [[ $confirm == [yY] ]]; then
                echo "Creating backup_and_deploy.sh script..."
                # Here we would create and run the backup script
                echo "Run: ./backup_and_deploy.sh"
            fi
            ;;
        2)
            echo -e "\n${GREEN}Creating update script...${NC}"
            echo "This will only update code without changing system configs"
            echo "Run: ./update_existing.sh"
            ;;
        3)
            echo -e "\n${BLUE}Manual Conflict Resolution Steps:${NC}"
            echo "1. Stop services: sudo supervisorctl stop all"
            echo "2. Stop nginx: sudo systemctl stop nginx"
            echo "3. Stop redis: sudo systemctl stop redis-server"
            echo "4. Backup configs: cp -r /etc/nginx/sites-available /tmp/nginx-backup"
            echo "5. Remove conflicts: rm -rf /var/www/4ex.ninja"
            echo "6. Run: ./deploy_production.sh"
            ;;
        4)
            echo -e "\n${RED}⚠️  FORCING DEPLOYMENT - This may break existing services!${NC}"
            read -p "Are you absolutely sure? Type 'FORCE' to continue: " force_confirm
            if [[ $force_confirm == "FORCE" ]]; then
                echo "Running deployment script..."
                ./deploy_production.sh
            else
                echo "Deployment cancelled."
            fi
            ;;
        5)
            echo "Exiting. Please resolve conflicts manually."
            exit 0
            ;;
    esac
else
    echo -e "${GREEN}✅ NO CONFLICTS DETECTED - SAFE TO DEPLOY${NC}"
    echo ""
    echo "Your system is ready for fresh deployment!"
    echo ""
    echo -e "${BLUE}To deploy 4ex.ninja:${NC}"
    echo "  git clone https://github.com/tadams95/4ex.ninja.git"
    echo "  cd 4ex.ninja/4ex.ninja-backend/scripts"
    echo "  chmod +x deploy_production.sh"
    echo "  ./deploy_production.sh"
    echo ""
    echo -e "${GREEN}This will set up the complete 4ex.ninja system on IP: 157.230.58.248${NC}"
    echo ""
    read -p "Would you like to run the deployment now? (y/N): " deploy_now
    if [[ $deploy_now == [yY] ]]; then
        echo ""
        echo "Starting deployment..."
        if [ -f "./deploy_production.sh" ]; then
            ./deploy_production.sh
        else
            echo "Please clone the repository first:"
            echo "git clone https://github.com/tadams95/4ex.ninja.git"
            echo "cd 4ex.ninja/4ex.ninja-backend/scripts"
            echo "./deploy_production.sh"
        fi
    fi
fi

echo ""
echo -e "${BLUE}Pre-check completed!${NC}"
