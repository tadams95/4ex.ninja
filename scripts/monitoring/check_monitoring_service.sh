#!/bin/bash

# Monitoring Service Health Check Script
# Use this script to verify the monitoring API is accessible during deployment

set -e

echo "🏥 Monitoring Service Health Check"
echo "=================================="

# Configuration
MONITORING_ENDPOINTS=(
    "https://157.230.58.248:8081"
    "http://157.230.58.248:8081"
)

API_PATHS=(
    "/regime/current"
    "/alerts/recent"
    "/strategy/health"
    "/performance/summary"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Health check function
check_endpoint() {
    local base_url=$1
    local path=$2
    local timeout=${3:-10}
    
    local full_url="${base_url}${path}"
    
    echo -n "  Testing ${full_url}... "
    
    # Perform the request with timeout
    local response_code
    local response_time
    
    if response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$full_url" 2>/dev/null); then
        response_time=$(curl -s -o /dev/null -w "%{time_total}" --max-time "$timeout" "$full_url" 2>/dev/null)
        
        if [ "$response_code" -eq 200 ]; then
            printf "${GREEN}✅ OK${NC} (${response_code}, ${response_time}s)\n"
            return 0
        else
            printf "${YELLOW}⚠️  HTTP ${response_code}${NC}\n"
            return 1
        fi
    else
        printf "${RED}❌ FAILED${NC} (connection error)\n"
        return 1
    fi
}

# Test SSL/TLS specifically
check_ssl() {
    local url=$1
    
    echo -n "  SSL/TLS Check for ${url}... "
    
    if curl -s --max-time 10 "${url}/regime/current" > /dev/null 2>&1; then
        printf "${GREEN}✅ SSL OK${NC}\n"
        return 0
    else
        printf "${RED}❌ SSL FAILED${NC}\n"
        return 1
    fi
}

# CORS check
check_cors() {
    local url=$1
    
    echo -n "  CORS Check for ${url}... "
    
    local cors_header
    cors_header=$(curl -s -H "Origin: https://4ex.ninja" -I "${url}/regime/current" | grep -i "access-control-allow-origin" || true)
    
    if [ -n "$cors_header" ]; then
        printf "${GREEN}✅ CORS OK${NC}\n"
        return 0
    else
        printf "${YELLOW}⚠️  No CORS headers${NC}\n"
        return 1
    fi
}

# Performance check
check_performance() {
    local url=$1
    local threshold=${2:-2.0}
    
    echo -n "  Performance Check for ${url}... "
    
    local response_time
    response_time=$(curl -s -o /dev/null -w "%{time_total}" --max-time 10 "${url}/regime/current" 2>/dev/null || echo "timeout")
    
    if [ "$response_time" = "timeout" ]; then
        printf "${RED}❌ TIMEOUT${NC}\n"
        return 1
    elif [ "$(echo "$response_time < $threshold" | bc)" -eq 1 ]; then
        printf "${GREEN}✅ FAST${NC} (${response_time}s)\n"
        return 0
    else
        printf "${YELLOW}⚠️  SLOW${NC} (${response_time}s)\n"
        return 1
    fi
}

# Data validation check
check_data_format() {
    local url=$1
    
    echo -n "  Data Format Check for ${url}... "
    
    local json_response
    json_response=$(curl -s --max-time 10 "${url}/regime/current" 2>/dev/null || echo "")
    
    if [ -z "$json_response" ]; then
        printf "${RED}❌ NO DATA${NC}\n"
        return 1
    fi
    
    # Check if it's valid JSON with expected fields
    if echo "$json_response" | jq -e '.current_regime' > /dev/null 2>&1; then
        printf "${GREEN}✅ VALID JSON${NC}\n"
        return 0
    else
        printf "${RED}❌ INVALID JSON${NC}\n"
        return 1
    fi
}

# Main health check process
main() {
    local overall_status=0
    local working_endpoints=()
    local failed_endpoints=()
    
    echo -e "${BLUE}Checking monitoring service endpoints...${NC}\n"
    
    for base_url in "${MONITORING_ENDPOINTS[@]}"; do
        echo "🔍 Testing: $base_url"
        
        local endpoint_healthy=true
        local endpoint_tests=0
        local endpoint_passed=0
        
        # Test each API path
        for path in "${API_PATHS[@]}"; do
            ((endpoint_tests++))
            if check_endpoint "$base_url" "$path"; then
                ((endpoint_passed++))
            else
                endpoint_healthy=false
            fi
        done
        
        # Additional checks for working endpoints
        if [ $endpoint_passed -gt 0 ]; then
            # SSL check (only for HTTPS)
            if [[ $base_url == https* ]]; then
                check_ssl "$base_url" || endpoint_healthy=false
            fi
            
            # CORS check
            check_cors "$base_url" || true  # Don't fail on CORS issues
            
            # Performance check
            check_performance "$base_url" || true  # Don't fail on performance issues
            
            # Data format check
            check_data_format "$base_url" || endpoint_healthy=false
        fi
        
        # Record results
        if [ $endpoint_passed -gt 0 ]; then
            working_endpoints+=("$base_url ($endpoint_passed/$endpoint_tests endpoints)")
        else
            failed_endpoints+=("$base_url")
            overall_status=1
        fi
        
        echo ""
    done
    
    # Summary
    echo "📊 Health Check Summary"
    echo "======================="
    
    if [ ${#working_endpoints[@]} -gt 0 ]; then
        echo -e "${GREEN}✅ Working Endpoints:${NC}"
        for endpoint in "${working_endpoints[@]}"; do
            echo "   • $endpoint"
        done
    fi
    
    if [ ${#failed_endpoints[@]} -gt 0 ]; then
        echo -e "${RED}❌ Failed Endpoints:${NC}"
        for endpoint in "${failed_endpoints[@]}"; do
            echo "   • $endpoint"
        done
    fi
    
    echo ""
    
    # Recommendations
    if [ $overall_status -eq 0 ]; then
        echo -e "${GREEN}🎉 All monitoring services are healthy!${NC}"
        
        # Determine best endpoint
        if [[ " ${working_endpoints[*]} " =~ "https:" ]]; then
            echo -e "${BLUE}💡 Recommendation: Use HTTPS endpoint for production${NC}"
        else
            echo -e "${YELLOW}💡 Recommendation: Consider enabling HTTPS for production${NC}"
        fi
    else
        echo -e "${RED}⚠️  Some monitoring services are not accessible${NC}"
        echo -e "${YELLOW}💡 Recommendations:${NC}"
        echo "   • Check if monitoring service is running: systemctl status monitoring-api"
        echo "   • Verify firewall rules allow port 8081"
        echo "   • Check SSL certificate configuration for HTTPS"
        echo "   • Review monitoring service logs for errors"
    fi
    
    echo ""
    echo "📋 Next Steps for Production:"
    echo "  1. Update environment variables with working endpoint"
    echo "  2. Ensure CORS headers are properly configured"
    echo "  3. Set up monitoring alerts for service health"
    echo "  4. Configure load balancer if using multiple instances"
    
    exit $overall_status
}

# Check dependencies
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl is required but not installed${NC}"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq is recommended for JSON validation but not installed${NC}"
fi

if ! command -v bc &> /dev/null; then
    echo -e "${YELLOW}⚠️  bc is recommended for performance checks but not installed${NC}"
fi

# Run main function
main "$@"
