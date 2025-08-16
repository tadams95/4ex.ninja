#!/bin/bash

# Quick status check for Phase 2 monitoring on droplet
# Usage: ./check_monitoring_status.sh

DROPLET_IP="157.230.58.248"
DROPLET_USER="root"

echo "🔍 Checking Phase 2 Monitoring Status on $DROPLET_IP"
echo "=================================================="
echo ""

echo "📊 Supervisor Services:"
ssh $DROPLET_USER@$DROPLET_IP 'supervisorctl status | grep -E "(4ex|monitoring)"'
echo ""

echo "🌐 Port Status:"
ssh $DROPLET_USER@$DROPLET_IP 'netstat -tulpn | grep -E ":808[01]"'
echo ""

echo "📁 Monitoring Files:"
ssh $DROPLET_USER@$DROPLET_IP 'ls -la /var/www/4ex.ninja/4ex.ninja-backend/src/monitoring/ 2>/dev/null || echo "Monitoring directory not found"'
echo ""

echo "📝 Recent Logs (last 10 lines):"
echo "--- System Monitoring ---"
ssh $DROPLET_USER@$DROPLET_IP 'tail -n 5 /var/log/4ex-ninja/monitoring.log 2>/dev/null || echo "No system monitoring logs"'
echo ""
echo "--- Phase 2 API ---"
ssh $DROPLET_USER@$DROPLET_IP 'tail -n 5 /var/log/4ex-ninja/monitoring_api.log 2>/dev/null || echo "No Phase 2 API logs yet"'
echo ""

echo "🔗 Access URLs:"
echo "   • System Monitoring: http://157.230.58.248:8080"
echo "   • Phase 2 API: http://157.230.58.248:8081"
echo ""

echo "⚡ Quick Commands:"
echo "   • Start Phase 2 API: ssh root@157.230.58.248 'supervisorctl start 4ex-monitoring-api'"
echo "   • View logs: ssh root@157.230.58.248 'tail -f /var/log/4ex-ninja/monitoring_api.log'"
echo "   • Restart services: ssh root@157.230.58.248 'supervisorctl restart all'"
