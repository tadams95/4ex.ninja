#!/bin/bash

# Update system
apt-get update && apt-get upgrade -y

# Install required packages
apt-get install -y python3-pip python3-venv git supervisor

# Create forex user
useradd -m -s /bin/bash forex

# Clone repository
su - forex -c "git clone https://github.com/tadams95/4ex.ninja.git"

# Setup Python environment
su - forex -c "cd 4ex.ninja && python3 -m venv venv"
su - forex -c "cd 4ex.ninja && source venv/bin/activate && pip install -r requirements.txt"

# Copy and enable service
cp /home/forex/4ex.ninja/deploy/forex-strategy.service /etc/systemd/system/
systemctl enable forex-strategy
systemctl start forex-strategy

# Setup logging
mkdir -p /var/log/forex
chown forex:forex /var/log/forex
