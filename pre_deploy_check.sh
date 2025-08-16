#!/bin/bash

# Pre-deployment health check for monitoring service
# Use this in your CI/CD pipeline before deploying the frontend

set -e

echo "🚀 Pre-deployment monitoring service check"
echo "==========================================="

# Import check_endpoint function
check_endpoint() {
    local base_url=$1
    local path=$2
    local timeout=${3:-10}
    
    local full_url="${base_url}${path}"
    
    echo -n "  Testing ${full_url}... "
    
    # Perform the request with timeout
    local response_code
    
    if response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$full_url" 2>/dev/null); then
        if [ "$response_code" -eq 200 ]; then
            echo "✅ OK"
            return 0
        else
            echo "❌ HTTP ${response_code}"
            return 1
        fi
    else
        echo "❌ FAILED"
        return 1
    fi
}

# Deployment-specific check
deployment_check() {
    echo "Checking monitoring service for production deployment..."
    
    # Check if we can reach at least one endpoint
    local working_endpoint=""
    
    # Test HTTP endpoint (known to work)
    if check_endpoint "http://157.230.58.248:8081" "/regime/current" 5; then
        working_endpoint="http://157.230.58.248:8081"
        echo "✅ HTTP endpoint is accessible"
    else
        echo "❌ HTTP endpoint failed"
        return 1
    fi
    
    # Test HTTPS endpoint (currently failing)
    if check_endpoint "https://157.230.58.248:8081" "/regime/current" 5; then
        echo "✅ HTTPS endpoint is accessible"
        working_endpoint="https://157.230.58.248:8081"
    else
        echo "⚠️  HTTPS endpoint failed (expected - SSL issue)"
    fi
    
    if [ -n "$working_endpoint" ]; then
        echo ""
        echo "✅ Deployment can proceed"
        echo "📝 Recommended environment configuration:"
        echo "   NEXT_PUBLIC_MONITORING_API_URL=${working_endpoint}"
        
        # Get script directory
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        
        # Create/update .env.production file
        if [ -f "${SCRIPT_DIR}/4ex.ninja-frontend/.env.production" ]; then
            echo "📁 Updating .env.production file..."
            sed -i.bak "s|NEXT_PUBLIC_MONITORING_API_URL=.*|NEXT_PUBLIC_MONITORING_API_URL=${working_endpoint}|" \
                "${SCRIPT_DIR}/4ex.ninja-frontend/.env.production"
        else
            echo "📁 Creating .env.production file..."
            echo "NEXT_PUBLIC_MONITORING_API_URL=${working_endpoint}" > \
                "${SCRIPT_DIR}/4ex.ninja-frontend/.env.production"
        fi
        
        return 0
    else
        echo ""
        echo "❌ Deployment should NOT proceed"
        echo "💡 Fix monitoring service accessibility before deploying"
        return 1
    fi
}

# Run deployment check
deployment_check

echo ""
echo "� Vercel Deployment Instructions:"
echo "1. Set environment variable in Vercel:"
echo "   NEXT_PUBLIC_MONITORING_API_URL=/api/monitoring"
echo ""
echo "2. After deployment, test these endpoints:"
echo "   - https://your-app.vercel.app/api/monitoring-health"
echo "   - https://your-app.vercel.app/api/monitoring/regime/current"
echo ""
echo "�🔍 For detailed health check, run: ./check_monitoring_service.sh"
