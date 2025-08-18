# 🔧 Backend Connection Setup Guide

## Current Status
✅ Backend is running on Digital Ocean droplet (157.230.58.248:8000)
✅ API endpoints working internally: `/api/risk/var-summary`, `/api/risk/correlation-matrix`
❌ External access blocked (likely firewall/security group issue)

## 🔍 Troubleshooting Steps

### 1. Check External Access
From your local machine, test if the backend is accessible:
```bash
curl -v http://157.230.58.248:8000/api/risk/var-summary
```

If this fails with "Connection refused" or timeout, the issue is network configuration.

### 2. Fix Firewall (on your droplet)
SSH into your droplet and run:
```bash
# Check current firewall status
sudo ufw status

# Allow port 8000 if UFW is active
sudo ufw allow 8000/tcp

# Or if using iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

### 3. Check Service Binding
Ensure the service is bound to all interfaces (0.0.0.0) not just localhost:
```bash
# Check what the service is bound to
sudo netstat -tlnp | grep :8000

# Should show: 0.0.0.0:8000, not 127.0.0.1:8000
```

### 4. Digital Ocean Networking
- Check if there are any Cloud Firewalls applied to your droplet
- Verify the droplet's security groups allow inbound traffic on port 8000

## 🚀 Quick Fix Options

### Option A: Enable External Access (Recommended)
1. Open port 8000 in firewall
2. Ensure service binds to 0.0.0.0:8000
3. Test external connectivity

### Option B: Use SSH Tunnel (Temporary)
```bash
# Create SSH tunnel (run this from your local machine)
ssh -L 8000:localhost:8000 root@157.230.58.248

# Then your frontend can connect to localhost:8000
```

### Option C: Add Nginx Reverse Proxy
Set up nginx to proxy API requests and handle SSL/security.

## 🔧 Deployment Commands

Once network access is working, deploy with:

```bash
# Commit changes
git add .
git commit -m "Connect dashboard to production backend"
git push

# Set Vercel environment variable
vercel env add BACKEND_URL production
# Enter: http://157.230.58.248:8000

# Deploy to Vercel
vercel --prod
```

## 🧪 Testing the Connection

After deployment, test the live dashboard:
1. Visit: https://4ex-ninja.vercel.app/risk-dashboard
2. Open browser dev tools → Network tab
3. Verify API calls to `/api/risk/var-summary` return 200 status
4. Check that real VaR data is displayed

## 📋 Current Implementation Status

✅ **Task 1.1**: Backend API Endpoints - COMPLETED
✅ **Task 1.2**: Frontend Dashboard Shell - COMPLETED  
✅ **Task 1.3**: Real-Time VaR Display - COMPLETED
🔄 **Network Configuration**: IN PROGRESS

**Next**: Task 2.1 - Correlation Heat Map (once backend connection is established)
