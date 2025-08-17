#!/bin/bash

# 4ex.ninja Port Quick Reference
# Digital Ocean Droplet: 157.230.58.248

echo "🌐 4ex.ninja Port Allocation Status"
echo "=================================="
echo ""

# Check each known port
check_port() {
    local port=$1
    local description=$2
    
    echo -n "Port $port ($description): "
    if ssh root@157.230.58.248 "netstat -tlnp | grep :$port" >/dev/null 2>&1; then
        echo "🔴 OCCUPIED"
        ssh root@157.230.58.248 "netstat -tlnp | grep :$port | head -1"
    else
        echo "🟢 AVAILABLE"
    fi
}

# Check known ports
check_port 8000 "Legacy Backend"
check_port 8081 "Monitoring Dashboard"  
check_port 8082 "Backtesting API"
check_port 8083 "LAST AVAILABLE - RESERVE FOR CRITICAL ONLY"

echo ""
echo "🚨 PORT CONSTRAINT WARNING:"
echo "Only 1 port remaining (8083) - Consider service consolidation!"
echo ""
echo "🔍 Quick Tests:"
echo "curl http://157.230.58.248:8081/health"
echo "curl http://157.230.58.248:8082/api/v1/backtest/health"
echo ""

# Show running Python services
echo "🐍 Running Python Services:"
ssh root@157.230.58.248 "ps aux | grep python | grep -v grep | grep -E '(uvicorn|port)'" 2>/dev/null || echo "No Python services found with port info"
