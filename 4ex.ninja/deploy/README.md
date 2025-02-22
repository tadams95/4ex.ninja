# Deployment Guide

## Digital Ocean Setup

1. Create a new droplet:
   - Choose Ubuntu 20.04 LTS
   - Basic plan ($5/month should be sufficient)
   - Choose a datacenter near major forex centers (London/New York)

2. Initial server setup:
```bash
# SSH into your droplet
ssh root@your_droplet_ip
 
# Run the setup script
cd /tmp
wget https://raw.githubusercontent.com/tadams95/4ex.ninja/main/deploy/setup_droplet.sh
chmod +x setup_droplet.sh
./setup_droplet.sh
```

3. Monitor the service:
```bash
# Check service status
systemctl status forex-strategy

# View logs
journalctl -u forex-strategy -f
```

4. Maintenance:
- Service auto-restarts on failure
- Logs rotate automatically
- System updates can be automated with unattended-upgrades

## Security Considerations

1. Setup SSH key authentication
2. Configure firewall (ufw)
3. Keep system updated
4. Monitor system resources
