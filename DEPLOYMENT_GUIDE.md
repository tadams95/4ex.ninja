# 🚀 Emergency Risk Management Deployment Guide

## Prerequisites Checklist

Before deploying the Emergency Risk Management system, ensure you have:

### 1. 🔑 **Required Credentials**
- **OANDA API Key** - From your OANDA account dashboard
- **OANDA Account ID** - Your practice or live account ID
- **MongoDB Connection String** - MongoDB Atlas or your MongoDB instance

### 2. 🌐 **Digital Ocean Access**
- SSH access to your droplet: `ssh root@157.230.58.248`
- Droplet should be running Ubuntu/Debian

### 3. 📁 **Environment Configuration**
Create a `.env` file with your credentials (see template below)

---

## 🔧 Step 1: Configure Environment Variables

Create a `.env` file in the root directory with your actual credentials:

```bash
# OANDA API Configuration
OANDA_API_KEY=your_actual_oanda_api_key
OANDA_ACCOUNT_ID=your_actual_account_id

# MongoDB Configuration
MONGO_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/database_name

# Discord Configuration (optional but recommended)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url

# Redis Configuration (optional, for 80-90% performance improvement)
REDIS_URL=redis://localhost:6379
```

---

## 🚀 Step 2: Deploy to Digital Ocean

### Option A: Automated Deployment (Recommended)

1. **Copy deployment script to server:**
```bash
scp deploy-emergency-risk.sh root@157.230.58.248:/tmp/
```

2. **Run deployment script:**
```bash
ssh root@157.230.58.248 'chmod +x /tmp/deploy-emergency-risk.sh && /tmp/deploy-emergency-risk.sh'
```

### Option B: Manual Deployment

1. **SSH into your droplet:**
```bash
ssh root@157.230.58.248
```

2. **Pull latest code:**
```bash
cd /tmp
git clone https://github.com/tadams95/4ex.ninja.git
cd 4ex.ninja
```

3. **Run the deployment script:**
```bash
chmod +x deploy-emergency-risk.sh
./deploy-emergency-risk.sh
```

---

## ⚙️ Step 3: Configure Environment on Server

After deployment, update the environment file on the server:

```bash
ssh root@157.230.58.248
nano /opt/4ex-ninja-backend/.env
```

Add your actual credentials to the `.env` file on the server.

---

## 🚀 Step 4: Start the Emergency Risk Management System

```bash
# Start the MA_Unified_Strat with Emergency Risk Management
ssh root@157.230.58.248 'sudo systemctl start ma-unified-strategy'

# Monitor logs
ssh root@157.230.58.248 'sudo journalctl -u ma-unified-strategy -f'
```

---

## 📊 Step 5: Verify Deployment

### Check System Status
```bash
ssh root@157.230.58.248 'sudo systemctl status 4ex-ninja-backend'
ssh root@157.230.58.248 'sudo systemctl status ma-unified-strategy'
```

### Test API Endpoints
```bash
curl http://157.230.58.248:8000/health
curl http://157.230.58.248:8000/api/risk/var-summary
```

### Monitor Emergency Risk Management
```bash
# View strategy logs (includes emergency risk events)
ssh root@157.230.58.248 'sudo journalctl -u ma-unified-strategy -f --lines=50'

# Check MongoDB collections
ssh root@157.230.58.248 'mongo your_connection_string --eval "db.emergency_events.find().limit(5)"'
```

---

## 🚨 Emergency Risk Management Features Active

Once deployed, your system will have:

- ✅ **4-Level Emergency Protocols**
  - Level 1: 10% drawdown → 80% position size
  - Level 2: 15% drawdown → 60% position size  
  - Level 3: 20% drawdown → 30% position size (Crisis Mode)
  - Level 4: 25% drawdown → Trading halted

- ✅ **Stress Event Detection**
  - 2x volatility threshold monitoring
  - Automatic position reduction during stress

- ✅ **Database Persistence**
  - Emergency events saved to `risk_management.emergency_events`
  - Stress events saved to `risk_management.stress_events`
  - Portfolio metrics saved to `risk_management.portfolio_metrics`

- ✅ **Real-time Monitoring**
  - Discord alerts for critical events
  - Comprehensive logging
  - API endpoints for risk dashboard

---

## 🛠️ Management Commands

```bash
# View live strategy logs
ssh root@157.230.58.248 'sudo journalctl -u ma-unified-strategy -f'

# Restart strategy
ssh root@157.230.58.248 'sudo systemctl restart ma-unified-strategy'

# Stop strategy (emergency stop)
ssh root@157.230.58.248 'sudo systemctl stop ma-unified-strategy'

# View backend API logs
ssh root@157.230.58.248 'sudo journalctl -u 4ex-ninja-backend -f'

# Check system status
ssh root@157.230.58.248 'sudo systemctl status ma-unified-strategy --no-pager'
```

---

## 🔍 Troubleshooting

### Common Issues:

1. **Strategy won't start:**
   - Check `.env` file has correct credentials
   - Verify MongoDB connection string
   - Check logs: `sudo journalctl -u ma-unified-strategy -f`

2. **No signals generated:**
   - Verify OANDA API credentials
   - Check market hours
   - Monitor logs for errors

3. **Database errors:**
   - Verify MongoDB connection string
   - Check network connectivity
   - Ensure database exists

### Emergency Contacts:
- View all logs: `sudo journalctl --no-pager`
- Check service status: `sudo systemctl status ma-unified-strategy`
- Emergency stop: `sudo systemctl stop ma-unified-strategy`

---

## 🎯 Success Indicators

You'll know the deployment is successful when you see:

1. **Strategy logs showing:**
   - "🚨 Emergency Risk Manager ACTIVATED"
   - "📊 Emergency event saved to database"
   - Signal generation with emergency context

2. **API responses from:**
   - `http://157.230.58.248:8000/health`
   - `http://157.230.58.248:8000/api/risk/var-summary`

3. **Database collections populated:**
   - `risk_management.emergency_events`
   - `risk_management.stress_events`
   - `risk_management.portfolio_metrics`

Your Emergency Risk Management system is now protecting your trading with enterprise-grade risk controls! 🛡️
