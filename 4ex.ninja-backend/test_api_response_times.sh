#!/bin/bash

# API Response Time Analysis Script
# Tests multiple endpoints and measures response times

BASE_URL="http://127.0.0.1:9000"
ITERATIONS=5

echo "🚀 4ex.ninja API Response Time Analysis"
echo "======================================"
echo "Base URL: $BASE_URL"
echo "Iterations per endpoint: $ITERATIONS"
echo

# Function to test an endpoint
test_endpoint() {
    local endpoint="$1"
    local method="$2"
    echo "🧪 Testing $method $endpoint"
    
    local total_time=0
    local success_count=0
    local min_time=999999
    local max_time=0
    local status_codes=""
    
    for i in $(seq 1 $ITERATIONS); do
        if [ "$method" = "GET" ]; then
            result=$(curl -s -w "%{time_total}:%{http_code}:%{size_download}" -o /dev/null "$BASE_URL$endpoint" 2>/dev/null)
        else
            result=$(curl -s -w "%{time_total}:%{http_code}:%{size_download}" -o /dev/null -X POST -H "Content-Type: application/json" -d '{}' "$BASE_URL$endpoint" 2>/dev/null)
        fi
        
        if [ $? -eq 0 ]; then
            time_total=$(echo $result | cut -d: -f1)
            status_code=$(echo $result | cut -d: -f2)
            size=$(echo $result | cut -d: -f3)
            
            # Convert to milliseconds
            time_ms=$(echo "$time_total * 1000" | bc -l)
            
            echo "   Request $i: ${time_ms}ms | Status: $status_code | Size: ${size}B"
            
            total_time=$(echo "$total_time + $time_ms" | bc -l)
            success_count=$((success_count + 1))
            status_codes="$status_codes $status_code"
            
            # Update min/max
            if (( $(echo "$time_ms < $min_time" | bc -l) )); then
                min_time=$time_ms
            fi
            if (( $(echo "$time_ms > $max_time" | bc -l) )); then
                max_time=$time_ms
            fi
        else
            echo "   Request $i: ERROR - Connection failed"
        fi
    done
    
    if [ $success_count -gt 0 ]; then
        avg_time=$(echo "scale=2; $total_time / $success_count" | bc -l)
        echo "   📊 Average: ${avg_time}ms | Min: ${min_time}ms | Max: ${max_time}ms"
        echo "   ✅ Success Rate: $success_count/$ITERATIONS | Status Codes:$status_codes"
        
        # Performance rating
        if (( $(echo "$avg_time < 100" | bc -l) )); then
            echo "   🟢 EXCELLENT (<100ms)"
        elif (( $(echo "$avg_time < 500" | bc -l) )); then
            echo "   🟡 GOOD (<500ms)"
        elif (( $(echo "$avg_time < 1000" | bc -l) )); then
            echo "   🟠 NEEDS IMPROVEMENT (<1000ms)"
        else
            echo "   🔴 POOR (>1000ms)"
        fi
    else
        echo "   ❌ ALL REQUESTS FAILED"
    fi
    echo
}

# Check if server is running
echo "🔍 Checking server status..."
if curl -s "$BASE_URL/" > /dev/null 2>&1; then
    echo "✅ Server is running at $BASE_URL"
else
    echo "❌ Server is not running at $BASE_URL"
    echo "Please start the server first:"
    echo "cd /path/to/backend && PYTHONPATH=./src JWT_SECRET_KEY='test-key' python3 -m uvicorn app:app --host 127.0.0.1 --port 9000"
    exit 1
fi

echo

# Test common endpoints
echo "📈 Testing Common API Endpoints"
echo "================================"

test_endpoint "/" "GET"
test_endpoint "/health" "GET"
test_endpoint "/docs" "GET"

echo "📊 Testing Performance Monitoring Endpoints"
echo "==========================================="

test_endpoint "/api/v1/performance/" "GET"
test_endpoint "/api/v1/performance/metrics" "GET"
test_endpoint "/api/v1/performance/system" "GET"

echo "🔄 Testing Trading API Endpoints"
echo "================================"

test_endpoint "/api/v1/signals/" "GET"
test_endpoint "/api/v1/market-data/" "GET"

echo "🔐 Testing Auth Endpoints"
echo "========================="

test_endpoint "/api/v1/auth/health" "GET"

echo "📋 Summary & Recommendations"
echo "============================"
echo "✅ Test completed successfully"
echo "💡 Key Performance Tips:"
echo "   • Response times <100ms are excellent"
echo "   • Response times <500ms are good for API endpoints"
echo "   • Times >1000ms indicate potential optimization needs"
echo "   • Consider adding response caching for frequently accessed endpoints"
echo "   • Monitor database query performance for slow endpoints"
echo
echo "📄 For detailed analysis, check server logs or use the Python analysis script"
