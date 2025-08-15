#!/bin/bash

# 4ex.ninja - Quick Deployment Commands for Digital Ocean
# Copy and paste these commands directly into your SSH session

echo "🚀 4ex.ninja Quick Deployment Commands"
echo "======================================"
echo ""

echo "1️⃣ First, make sure you're running as root:"
echo "   sudo su -"
echo ""

echo "2️⃣ Clone the repository:"
echo "   cd /tmp"
echo "   git clone https://github.com/tadams95/4ex.ninja.git"
echo "   cd 4ex.ninja/4ex.ninja-backend/scripts"
echo ""

echo "3️⃣ Run the deployment script:"
echo "   chmod +x deploy_production.sh"
echo "   ./deploy_production.sh"
echo ""

echo "4️⃣ After deployment, configure your credentials:"
echo "   nano /etc/4ex-ninja/production.env"
echo "   # Add your OANDA_API_KEY, OANDA_ACCOUNT_ID, and DISCORD_WEBHOOK_URL"
echo ""

echo "5️⃣ Update the domain in nginx config:"
echo "   nano /etc/nginx/sites-available/4ex.ninja"
echo "   # Replace 'your-domain.com' with your actual domain or IP"
echo "   systemctl reload nginx"
echo ""

echo "6️⃣ Run the validation tests:"
echo "   cd /var/www/4ex.ninja/4ex.ninja-backend"
echo "   source /var/www/4ex.ninja/venv/bin/activate"
echo "   python src/validation/emergency_validation_runner.py"
echo ""

echo "7️⃣ Check everything is working:"
echo "   supervisorctl status"
echo "   curl http://localhost/health"
echo ""

echo "🎉 That's it! Your 4ex.ninja system should be live!"
echo "Access it at: http://your-droplet-ip/"
