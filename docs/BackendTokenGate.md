# Backend Token-Gated Features Deployment Guide

## 📊 Overview

Your $4EX token is deployed and your backend infrastructure is ready. This guide provides clear steps to activate real token-gated Discord notifications and API features.

**Token Contract**: `0x3Aa87C18d7080484e4839afA3540e520452ccA3E` (Base)  
**Current Status**: Backend configured but in simulation mode  
**Goal**: Activate real token balance checking for Discord notifications

---

## 🎯 Why Backend Token Verification is Required

### **Discord Notification System**
Your trading signals are generated and routed by the backend to different Discord channels based on user token tiers:

```python
# Current tier system in onchain_integration.py
notification_tiers = {
    "public": [],                    # Free users - no premium signals
    "holders": ["premium_signals"],  # 1,000,000+ $4EX tokens
    "premium": ["whale_signals"],    # 1,000,000+ $4EX tokens  
    "whale": ["alpha_signals"]       # 100,000,000+ $4EX tokens
}
```

### **Signal Routing Flow**
```
Trading Strategy (Backend) 
    → Signal Generated 
    → Check User Token Balance (Backend) 
    → Determine User Tier
    → Route to Appropriate Discord Channel
    → Send Notification to Correct Webhook
```

---

## 🚀 Deployment Steps

### **Step 1: Verify Current Configuration**

Your backend is already configured with the correct token address:

```bash
# Check token configuration
cd /Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend
python3 -c "
from src.onchain_integration import onchain_service
print(f'Token Address: {onchain_service.token_config.address}')
print(f'Is Deployed: {onchain_service.token_config.is_deployed}')
print(f'Web3 Connected: {onchain_service.web3.is_connected()}')
"
```

### **Step 2: Deploy Backend to Digital Ocean Droplet**

Your backend needs to be deployed to activate real token balance checking:

```bash
# SSH into your droplet
ssh root@157.230.58.248

# Navigate to your project directory and update
cd /path/to/4ex.ninja
git pull origin main

# Install/update Python dependencies if needed
cd 4ex.ninja-backend
pip install -r requirements.txt

# Restart your backend service (adjust based on your setup)
# If using systemd:
sudo systemctl restart 4ex-backend

# If using supervisor:
sudo supervisorctl restart 4ex-backend

# If running manually:
pkill -f "python.*app" && nohup python -m uvicorn src.app:app --host 0.0.0.0 --port 8000 &

# Verify deployment
tail -f /var/log/4ex-backend.log  # or wherever your logs are
```

### **Step 3: Configure Discord Token-Gated Webhooks**

Set up separate Discord webhooks for each tier:

```bash
# SSH into your droplet first
ssh root@157.230.58.248

# Add environment variables to your system
# Option 1: Add to ~/.bashrc or ~/.profile
echo 'export DISCORD_WEBHOOK_SIGNALS_FREE="https://discord.com/api/webhooks/FREE_WEBHOOK_URL"' >> ~/.bashrc
echo 'export DISCORD_WEBHOOK_SIGNALS_PREMIUM="https://discord.com/api/webhooks/PREMIUM_WEBHOOK_URL"' >> ~/.bashrc
echo 'export DISCORD_WEBHOOK_WHALE_SIGNALS="https://discord.com/api/webhooks/WHALE_WEBHOOK_URL"' >> ~/.bashrc
echo 'export DISCORD_WEBHOOK_ALPHA_SIGNALS="https://discord.com/api/webhooks/ALPHA_WEBHOOK_URL"' >> ~/.bashrc

# Option 2: Create environment file
cat > /etc/environment << EOF
DISCORD_WEBHOOK_SIGNALS_FREE=https://discord.com/api/webhooks/FREE_WEBHOOK_URL
DISCORD_WEBHOOK_SIGNALS_PREMIUM=https://discord.com/api/webhooks/PREMIUM_WEBHOOK_URL
DISCORD_WEBHOOK_WHALE_SIGNALS=https://discord.com/api/webhooks/WHALE_WEBHOOK_URL
DISCORD_WEBHOOK_ALPHA_SIGNALS=https://discord.com/api/webhooks/ALPHA_WEBHOOK_URL
EOF

# Reload environment
source ~/.bashrc
```

### **Step 4: Test Token Balance Integration**

```bash
# Test real token balance checking
curl -X POST https://api.4ex.ninja/wallet/verify \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "YOUR_WALLET_ADDRESS_WITH_TOKENS"
  }'

# Expected response:
{
  "address": "0x...",
  "balance": "1000000000000000000000",
  "balance_formatted": "1000",
  "access_tier": "holders",
  "available_channels": ["premium_signals"],
  "is_simulation": false
}
```

### **Step 5: Verify Discord Role Assignment**

Test the complete flow:

1. **Connect Wallet** on frontend
2. **Check Token Balance** via backend API
3. **Assign Discord Roles** based on token tier
4. **Receive Notifications** in appropriate channels

---

## 🔧 Environment Configuration

### **Required Environment Variables**

Add to your droplet's environment configuration:

```bash
# SSH into droplet
ssh root@157.230.58.248

# Add to system environment
cat >> /etc/environment << EOF
TOKEN_CONTRACT_ADDRESS=0x3Aa87C18d7080484e4839afA3540e520452ccA3E
BASE_RPC_URL=https://mainnet.base.org
TOKEN_CACHE_TTL=300
WEB3_PROVIDER_URL=https://mainnet.base.org
ETHEREUM_NETWORK=base
DISCORD_WEBHOOK_SIGNALS_FREE=your_free_webhook_url
DISCORD_WEBHOOK_SIGNALS_PREMIUM=your_premium_webhook_url
DISCORD_WEBHOOK_WHALE_SIGNALS=your_whale_webhook_url
DISCORD_WEBHOOK_ALPHA_SIGNALS=your_alpha_webhook_url
EOF

# Or add to your application's .env file
cd /path/to/4ex.ninja/4ex.ninja-backend
cat >> .env << EOF
TOKEN_CONTRACT_ADDRESS=0x3Aa87C18d7080484e4839afA3540e520452ccA3E
BASE_RPC_URL=https://mainnet.base.org
TOKEN_CACHE_TTL=300
WEB3_PROVIDER_URL=https://mainnet.base.org
ETHEREUM_NETWORK=base
EOF
```

### **Service Configuration**

Since you're not using Docker, configure your backend service with virtual environment:

```bash
# Create virtual environment first
ssh root@157.230.58.248
apt update && apt install python3-full python3-venv python3-pip -y
python3 -m venv /root/venv
source /root/venv/bin/activate
pip install -r requirements.txt
pip install web3 eth-account fastapi uvicorn

# If using systemd service file
sudo nano /etc/systemd/system/4ex-backend.service

# Example service file:
[Unit]
Description=4EX Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
Environment=TOKEN_CONTRACT_ADDRESS=0x3Aa87C18d7080484e4839afA3540e520452ccA3E
Environment=BASE_RPC_URL=https://mainnet.base.org
Environment=PATH=/root/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/root/venv/bin/python -m uvicorn src.app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable 4ex-backend
sudo systemctl start 4ex-backend
```

---

## 🧪 Testing & Validation

### **Test 1: Token Balance Checking**
```bash
# SSH into droplet and test
ssh root@157.230.58.248
cd /path/to/4ex.ninja/4ex.ninja-backend

# Verify real token balance (not simulation)
python3 -c "
import asyncio
from src.onchain_integration import get_wallet_info

async def test():
    result = await get_wallet_info('YOUR_WALLET_ADDRESS')
    print(f'Balance: {result[\"balance_formatted\"]} $4EX')
    print(f'Tier: {result[\"access_tier\"]}')
    print(f'Simulation: {result[\"is_simulation\"]}')

asyncio.run(test())
"
```

### **Test 2: Discord Channel Routing**
```bash
# Test signal routing to correct Discord channel
# This should route to different webhooks based on user tier
python3 -c "
from src.infrastructure.external_services.discord_service import get_discord_service
from src.domain.signal import Signal, SignalType
from src.infrastructure.external_services.discord_service import UserTier

# Create test signal
signal = Signal(
    signal_id='test-001',
    pair='EUR/USD',
    signal_type=SignalType.BUY,
    entry_price=1.0950,
    confidence_score=0.85
)

# Test different user tiers
discord_service = get_discord_service()
discord_service.send_signal_notification(signal, UserTier.PREMIUM)
"
```

### **Test 3: Complete User Flow**
1. User connects wallet with 1,000+ $4EX tokens
2. Backend checks real token balance 
3. User assigned "holders" tier
4. Signal generated and sent to premium Discord channel
5. User receives notification in correct channel

---

## 🎯 Success Criteria

After deployment, verify:

- [ ] **Real Token Balance**: `is_simulation: false` in API responses
- [ ] **Tier Assignment**: Correct tiers based on actual token holdings
- [ ] **Discord Routing**: Signals sent to tier-appropriate channels
- [ ] **Performance**: Token balance checks <100ms
- [ ] **Error Handling**: Graceful fallback if RPC fails

---

## 🚨 Rollback Plan

If issues occur:

```bash
# SSH into droplet
ssh root@157.230.58.248

# Quick rollback to simulation mode
export TOKEN_SIMULATION_MODE=true

# Or restart service
sudo systemctl restart 4ex-backend

# Or if running manually
pkill -f "python.*app"
cd /path/to/4ex.ninja/4ex.ninja-backend
nohup python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 &

# Monitor logs
tail -f /var/log/4ex-backend.log
# or
journalctl -u 4ex-backend -f
```

---

## 📋 Next Actions

1. **Deploy backend changes** to activate real token integration
2. **Set up Discord webhook URLs** for each tier
3. **Test with real wallet addresses** that hold $4EX tokens
4. **Monitor performance** and error rates
5. **Document user onboarding flow** for wallet connection

Your infrastructure is ready - just need to deploy and configure the Discord webhooks!