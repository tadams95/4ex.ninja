# Discord Live Signals Environment Configuration
# Copy this to your DigitalOcean droplet and modify as needed

# =============================================================================
# DISCORD CONFIGURATION
# =============================================================================

# Discord webhook URL (REQUIRED)
# Get this from Discord Server Settings → Integrations → Webhooks
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"

# Enable/disable Discord notifications globally
export DISCORD_NOTIFICATIONS_ENABLED="true"

# =============================================================================
# SIGNAL FILTERING
# =============================================================================

# Minimum risk/reward ratio to send to Discord
export DISCORD_MIN_RR_RATIO="1.5"

# Minimum confidence score (0.0 - 1.0)
export DISCORD_MIN_CONFIDENCE="0.7"

# Comma-separated list of pairs to monitor
export DISCORD_ENABLED_PAIRS="EUR/USD,GBP/USD,USD/JPY,AUD/USD,USD/CAD,USD/CHF,NZD/USD"

# Comma-separated list of timeframes to monitor
export DISCORD_ENABLED_TIMEFRAMES="H1,H4,D"

# =============================================================================
# RATE LIMITING
# =============================================================================

# Maximum signals per minute (prevents spam)
export DISCORD_MAX_SIGNALS_PER_MINUTE="5"

# Maximum signals per hour
export DISCORD_MAX_SIGNALS_PER_HOUR="30"

# Cooldown between signals for same pair (minutes)
export DISCORD_PAIR_COOLDOWN_MINUTES="15"

# =============================================================================
# EXISTING CONFIGURATION (Keep your existing settings)
# =============================================================================

# MongoDB connection
export MONGO_CONNECTION_STRING="your_existing_mongo_string"

# OANDA API credentials
export API_KEY="your_existing_oanda_api_key"
export ACCOUNT_ID="your_existing_oanda_account_id"

# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================

# 1. Save this file as 'discord_env.sh' on your DigitalOcean droplet
# 2. Update the DISCORD_WEBHOOK_URL with your actual webhook URL
# 3. Modify other settings as needed
# 4. Source the file before running your strategy:
#    
#    source discord_env.sh
#    python3 src/strategies/MA_Unified_Strat.py
#
# 5. Or add to your system startup script for permanent configuration

# =============================================================================
# VERIFICATION
# =============================================================================

# Test your Discord webhook URL:
# curl -H "Content-Type: application/json" \
#      -d '{"content":"Test message from 4ex.ninja"}' \
#      $DISCORD_WEBHOOK_URL
