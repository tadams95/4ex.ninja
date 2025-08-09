#!/bin/bash

# API Response Optimization Test Script
echo "🧪 Testing API Response Optimizations"
echo "======================================"

# Start the server in background
cd /Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend
export PYTHONPATH=/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend
uvicorn src.app:app --host 127.0.0.1 --port 8004 &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Starting server..."
sleep 4

echo ""
echo "1️⃣ Testing basic signals response:"
curl -s "http://127.0.0.1:8004/api/v1/signals/?limit=2" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'   ✅ Response has data: {\"data\" in data}')
print(f'   📋 Has metadata: {\"meta\" in data}')
print(f'   🔢 Data count: {len(data.get(\"data\", []))}')
print(f'   📊 Pagination info: {\"pagination_type\" in data.get(\"meta\", {})}')
"

echo ""
echo "2️⃣ Testing field selection:"
curl -s "http://127.0.0.1:8004/api/v1/signals/?limit=2&fields=id,pair,signal_type" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('data'):
    first_item = data['data'][0]
    print(f'   🎯 Fields in response: {list(first_item.keys())}')
    field_selection = data.get('meta', {}).get('field_selection', {})
    print(f'   🔍 Field selection enabled: {field_selection.get(\"enabled\", False)}')
"

echo ""
echo "3️⃣ Testing compression headers:"
curl -s -I -H "Accept-Encoding: gzip" "http://127.0.0.1:8004/api/v1/signals/?limit=10" | grep -i "content-encoding\|content-length"

echo ""
echo "4️⃣ Testing market data optimization:"
curl -s "http://127.0.0.1:8004/api/v1/market-data/?limit=3&fields=instrument,timestamp,close" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'   ✅ Response has data: {\"data\" in data}')
print(f'   📋 Has metadata: {\"meta\" in data}')
print(f'   📄 Pagination type: {data.get(\"meta\", {}).get(\"pagination_type\", \"none\")}')
"

echo ""
echo "5️⃣ Testing response sizes:"
FULL_SIZE=$(curl -s "http://127.0.0.1:8004/api/v1/signals/?limit=10" | wc -c)
OPT_SIZE=$(curl -s "http://127.0.0.1:8004/api/v1/signals/?limit=10&fields=id,pair,signal_type" | wc -c)
echo "   📦 Full response: $FULL_SIZE bytes"
echo "   📦 Optimized response: $OPT_SIZE bytes"
SAVINGS=$(python3 -c "print(f'{((($FULL_SIZE - $OPT_SIZE) / $FULL_SIZE) * 100):.1f}%')")
echo "   💾 Size reduction: $SAVINGS"

echo ""
echo "🎉 API Response Optimization Testing Complete!"

# Cleanup
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null
echo "🧹 Server stopped"
