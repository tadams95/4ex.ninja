#!/bin/bash

# Enhanced Daily Strategy V2 Parallel Deployment Script
# Deploys V2 alongside existing V1 on Digital Ocean droplet

echo "========================================"
echo "Enhanced Daily Strategy V2 Deployment"
echo "Parallel Deployment Mode"
echo "========================================"

# Set deployment variables
DROPLET_IP="YOUR_DROPLET_IP"
DROPLET_USER="root"
DEPLOYMENT_PATH="/opt/4ex-ninja"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "🚀 Starting V2 parallel deployment..."

# Create backup of current system
echo "📦 Creating system backup..."
ssh $DROPLET_USER@$DROPLET_IP "cd $DEPLOYMENT_PATH && tar -czf backups/pre_v2_backup_$TIMESTAMP.tar.gz ."

# Upload V2 files
echo "📤 Uploading Enhanced Daily Strategy V2 files..."
scp enhanced_daily_strategy_v2.py $DROPLET_USER@$DROPLET_IP:$DEPLOYMENT_PATH/
scp enhanced_daily_strategy_v2_config.json $DROPLET_USER@$DROPLET_IP:$DEPLOYMENT_PATH/
scp confidence_risk_manager_v2.py $DROPLET_USER@$DROPLET_IP:$DEPLOYMENT_PATH/

# Create V2 monitoring endpoints
echo "🔧 Setting up V2 monitoring endpoints..."
ssh $DROPLET_USER@$DROPLET_IP "cd $DEPLOYMENT_PATH && cat >> app.py << 'EOF'

# Enhanced Daily Strategy V2 Endpoints
@app.route('/api/v2/signals', methods=['GET'])
def get_v2_signals():
    try:
        from enhanced_daily_strategy_v2 import EnhancedDailyStrategyV2
        strategy = EnhancedDailyStrategyV2()
        
        # Get current market data and generate signals
        signals = strategy.get_current_signals()
        
        return jsonify({
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat(),
            'signals': signals,
            'status': 'active'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/status', methods=['GET'])
def get_v2_status():
    return jsonify({
        'strategy': 'Enhanced Daily Strategy V2',
        'version': '2.0.0',
        'status': 'running',
        'deployment_mode': 'parallel',
        'validation_source': 'comprehensive_10_pair_test'
    })

@app.route('/api/v2/performance', methods=['GET'])
def get_v2_performance():
    # TODO: Implement V2 performance tracking
    return jsonify({
        'message': 'V2 performance tracking - coming soon',
        'deployment_date': '2025-08-21'
    })
EOF"

# Install V2 dependencies
echo "📦 Installing V2 dependencies..."
ssh $DROPLET_USER@$DROPLET_IP "cd $DEPLOYMENT_PATH && pip3 install -r requirements.txt"

# Test V2 deployment
echo "🧪 Testing V2 deployment..."
ssh $DROPLET_USER@$DROPLET_IP "cd $DEPLOYMENT_PATH && python3 -c 'from enhanced_daily_strategy_v2 import EnhancedDailyStrategyV2; strategy = EnhancedDailyStrategyV2(); print(\"✅ V2 Strategy loaded successfully\")'"

# Restart application with V2 support
echo "🔄 Restarting application with V2 support..."
ssh $DROPLET_USER@$DROPLET_IP "cd $DEPLOYMENT_PATH && systemctl restart 4ex-ninja"

# Verify deployment
echo "✅ Verifying V2 deployment..."
sleep 10
curl -f http://$DROPLET_IP:5000/api/v2/status || echo "❌ V2 status check failed"

echo "========================================"
echo "✅ Enhanced Daily Strategy V2 Deployed"
echo "Mode: Parallel (V1 + V2 running)"
echo "V1 Endpoint: /api/v1/signals"
echo "V2 Endpoint: /api/v2/signals"
echo "Monitor: /api/v2/status"
echo "========================================"

echo "📊 Starting 30-day comparison period..."
echo "Next: Monitor V1 vs V2 performance for migration decision"
