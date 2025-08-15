# 4ex.ninja Digital Ocean Deployment Guide

## Quick SSH Deployment Instructions

### 1. SSH into Your Digital Ocean Droplet

```bash
ssh root@your-droplet-ip
```

**Or if you have a non-root user:**
```bash
ssh your-username@your-droplet-ip
```

### 2. Upload the Deployment Script

**Option A: Direct upload via SCP**
```bash
# From your local machine (run this in a new terminal)
scp /Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/scripts/deploy_production.sh root@your-droplet-ip:/tmp/
```

**Option B: Clone the repo directly on the droplet**
```bash
# On the droplet
cd /tmp
git clone https://github.com/tadams95/4ex.ninja.git
cd 4ex.ninja/4ex.ninja-backend/scripts
chmod +x deploy_production.sh
```

### 3. Run the Deployment

```bash
# On the droplet (as root)
sudo /tmp/deploy_production.sh
```

### 4. Configure API Credentials (After Deployment)

```bash
# Edit the production environment file
sudo nano /etc/4ex-ninja/production.env

# Add your actual credentials:
OANDA_API_KEY=your_oanda_api_key_here
OANDA_ACCOUNT_ID=your_oanda_account_id_here
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
```

### 5. Update Domain Configuration

```bash
# Edit nginx configuration
sudo nano /etc/nginx/sites-available/4ex.ninja

# Replace 'your-domain.com' with your actual domain or droplet IP
server_name your-actual-domain.com www.your-actual-domain.com;
# OR for IP-only access:
server_name your-droplet-ip;

# Reload nginx
sudo systemctl reload nginx
```

### 6. Run Phase 1 Validation

```bash
cd /var/www/4ex.ninja/4ex.ninja-backend
source /var/www/4ex.ninja/venv/bin/activate
python src/validation/emergency_validation_runner.py
```

---

## Droplet Requirements

### Minimum Specs:
- **RAM:** 2GB (4GB recommended)
- **CPU:** 1 vCPU (2 vCPUs recommended)
- **Storage:** 25GB SSD
- **OS:** Ubuntu 20.04+ or 22.04 LTS

### Network:
- Public IPv4 address
- Firewall rules: Allow SSH (22), HTTP (80), HTTPS (443)

---

## Post-Deployment Monitoring

### Check Services Status:
```bash
# Supervisor services
sudo supervisorctl status

# System services
sudo systemctl status redis-server
sudo systemctl status nginx

# View logs
sudo tail -f /var/log/4ex-ninja/backend.log
sudo tail -f /var/log/4ex-ninja/monitoring.log
```

### Access Points:
- **Main App:** `http://your-droplet-ip/`
- **API Health:** `http://your-droplet-ip/health`
- **Monitoring:** `http://your-droplet-ip/monitor`

---

## Troubleshooting

### If deployment fails:
```bash
# Check deployment logs
sudo tail -f /var/log/syslog

# Check individual service status
sudo supervisorctl status
sudo systemctl status redis-server
sudo systemctl status nginx

# Restart services if needed
sudo supervisorctl restart all
sudo systemctl restart nginx
```

### If validation fails:
```bash
# Check error logs
sudo tail -f /var/log/4ex-ninja/backend_error.log
sudo tail -f /var/log/4ex-ninja/strategies_error.log

# Verify environment variables
sudo cat /etc/4ex-ninja/production.env

# Test Redis connection
redis-cli -a 4ex_redis_secure_2024 ping
```

---

## Security Notes

- The deployment script automatically configures UFW firewall
- Fail2ban is configured for basic intrusion prevention
- Redis is password-protected
- All services run under dedicated user accounts

---

## Next Steps After Successful Deployment

1. ✅ **API Credentials Configuration**
2. ✅ **Domain/IP Configuration** 
3. ✅ **Phase 1 Validation Tests**
4. 🔄 **Performance Comparison Validation** (with real metrics)
5. 🎯 **Phase 1 Completion** (95% confidence target)

Ready to deploy? Just SSH into your droplet and run the script! 🚀
