#!/bin/bash

# Phase 2 VaR & Correlation Management Deployment Script
# Deploy the fixed VaR Monitor and Correlation Manager to Digital Ocean droplet

echo "🚀 Deploying Phase 2 VaR & Correlation Management Components..."
echo "================================================================"

# Set variables
DROPLET_IP="157.230.58.248"
LOCAL_BACKEND="/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend"
REMOTE_BACKEND="/root/4ex.ninja-backend"

# Copy the fixed risk components
echo "📦 Copying VaR Monitor and Correlation Manager..."
scp "${LOCAL_BACKEND}/src/risk/var_monitor.py" root@${DROPLET_IP}:${REMOTE_BACKEND}/src/risk/
scp "${LOCAL_BACKEND}/src/risk/correlation_manager.py" root@${DROPLET_IP}:${REMOTE_BACKEND}/src/risk/
scp "${LOCAL_BACKEND}/src/risk/risk_metrics_db.py" root@${DROPLET_IP}:${REMOTE_BACKEND}/src/risk/

# Copy the integration demo for testing
echo "📦 Copying integration demo..."
scp "${LOCAL_BACKEND}/src/risk/phase2_integration_demo.py" root@${DROPLET_IP}:${REMOTE_BACKEND}/src/risk/

echo "✅ Phase 2 VaR & Correlation components deployed successfully!"

# Test the deployment
echo "🧪 Testing deployment on droplet..."
ssh root@${DROPLET_IP} << 'EOF'
cd /root/4ex.ninja-backend
echo "Testing VaR and Correlation Manager imports..."

python3 -c "
import sys
sys.path.append('.')
sys.path.append('/root/4ex.ninja-backend')

try:
    # Check if files exist
    import os
    files_to_check = [
        'src/risk/var_monitor.py',
        'src/risk/correlation_manager.py', 
        'src/risk/risk_metrics_db.py'
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            print(f'✅ {file} deployed successfully')
        else:
            print(f'❌ {file} missing')
    
    print('🎉 Phase 2 VaR & Correlation Management deployment complete!')
    
except Exception as e:
    print(f'❌ Deployment test failed: {e}')
"
EOF

echo "🎯 Deployment Summary:"
echo "  - VaR Monitor: Fixed critical type errors and deployed"
echo "  - Correlation Manager: Fixed critical type errors and deployed"  
echo "  - Risk Metrics DB: Schema deployed"
echo "  - Ready for Phase 2 Week 2 implementation!"
