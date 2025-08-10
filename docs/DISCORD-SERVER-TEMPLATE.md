# 4ex.ninja Discord Server Template

## 📋 Server Structure

### Categories and Channels:

```
🤖 4EX.NINJA TRADING BOT
├── 📊 TRADING SIGNALS
│   ├── #signals-free          🆓 Free trading signals
│   ├── #signals-premium       💎 Premium high-confidence signals
│   └── #market-analysis       📈 Market trends and analysis
│
├── 🚨 SYSTEM ALERTS
│   ├── #alerts-critical       🔴 Critical system alerts (Admin only)
│   ├── #alerts-general        🟡 General system alerts (Admin only)
│   └── #system-status         🟢 System status updates
│
└── 💬 COMMUNITY
    └── #general               💭 Community discussions

📊 STATISTICS & PERFORMANCE (Optional)
├── #performance-metrics       📊 Bot performance data
├── #signal-results           📈 Signal success rates
└── #analytics                🔍 Trading analytics
```

## 🎯 Channel Purposes

### Trading Channels:
- **#signals-free**: Basic crossover signals, available to all users
- **#signals-premium**: High-confidence signals (≥80%), premium users only
- **#market-analysis**: Daily/weekly market analysis and trends

### Alert Channels:
- **#alerts-critical**: System failures, high CPU/memory, API issues
- **#alerts-general**: Performance warnings, low-priority alerts
- **#system-status**: Regular system health updates, maintenance notices

### Community:
- **#general**: User discussions, feedback, trading chat

## 🔐 Role Setup

### Required Roles:

```
👑 Admin           - Full access to all channels
💎 Premium User     - Access to premium signals + free channels  
🆓 Free User       - Access to free signals and community
🤖 Bot             - For the 4ex.ninja bot (if using bot instead of webhooks)
```

### Role Permissions:

**Admin Role:**
- View all channels
- Manage channels (for webhook setup)
- Send messages in all channels

**Premium User Role:**
- View: #signals-free, #signals-premium, #market-analysis, #system-status, #general
- Send messages in: #general

**Free User Role:**
- View: #signals-free, #system-status, #general
- Send messages in: #general

**Bot Role (if using Discord bot):**
- Send messages in all channels
- Embed links
- Use external emojis
- Add reactions

## 🎨 Channel Setup Details

### #signals-free
```
📋 Topic: Free trading signals from 4ex.ninja bot
🔧 Permissions: @Free User, @Premium User, @Admin can view
📱 Notifications: @here for important signals
⏰ Rate Limit: 20 messages/minute
```

### #signals-premium  
```
📋 Topic: Premium high-confidence trading signals (≥80% confidence)
🔧 Permissions: @Premium User, @Admin can view
📱 Notifications: @everyone for high-confidence signals
⏰ Rate Limit: 30 messages/minute
```

### #alerts-critical
```
📋 Topic: Critical system alerts requiring immediate attention
🔧 Permissions: @Admin only
📱 Notifications: @everyone for all alerts
⏰ Rate Limit: 10 messages/minute
```

### #system-status
```
📋 Topic: System health updates and maintenance notices
🔧 Permissions: @Free User, @Premium User, @Admin can view
📱 Notifications: Mentions only
⏰ Rate Limit: 5 messages/minute
```

## 🔗 Webhook Configuration

For each channel, create a webhook:

1. **Channel Settings** → **Integrations** → **Webhooks**
2. **Create Webhook**
3. **Name**: "4ex.ninja"
4. **Avatar**: Upload your logo
5. **Copy Webhook URL**

### Required Webhooks:
- #signals-free → `DISCORD_WEBHOOK_SIGNALS_FREE`
- #signals-premium → `DISCORD_WEBHOOK_SIGNALS_PREMIUM`
- #alerts-critical → `DISCORD_WEBHOOK_ALERTS_CRITICAL`
- #alerts-general → `DISCORD_WEBHOOK_ALERTS_GENERAL`
- #market-analysis → `DISCORD_WEBHOOK_MARKET_ANALYSIS`
- #system-status → `DISCORD_WEBHOOK_SYSTEM_STATUS`
- #general → `DISCORD_WEBHOOK_COMMUNITY`

## 📱 Mobile App Configuration

### Notification Settings:
```
🔴 Critical: #alerts-critical - All messages
🟡 Important: #signals-premium - All messages  
🟢 Normal: #signals-free - Mentions only
🔵 Low: #system-status, #general - Mentions only
```

### Push Notification Setup:
1. Install Discord mobile app
2. Join your server
3. Go to server settings → Notifications
4. Set per-channel notification preferences
5. Enable "Mobile Push Notifications"

## 🎯 Usage Examples

### Signal Notification:
```
🟢 BUY Signal - EUR/USD
**BULLISH** crossover detected

📊 Entry Price: $1.10500
⏰ Timeframe: 1H  
💪 Confidence: 88.0%
🛑 Stop Loss: $1.10000
🎯 Take Profit: $1.11500
⚖️ Risk/Reward: 1:3.00

📈 Moving Averages: Fast: 50 | Slow: 200
📊 ATR: 0.00250

ℹ️ Market Context
**market_conditions**: Trending upward
**volatility**: Medium
**session**: London Open

4ex.ninja | Signal ID: EUR_USD_1628784123
```

### System Alert:
```
🚨 High CPU Usage Detected
CPU usage has exceeded 95% for the last 5 minutes

🔍 Alert Type: System Resource Exhaustion
⚡ Severity: HIGH
📍 Status: Active

📋 Context
**cpu_usage**: 96.5%
**memory_usage**: 78.2%
**affected_services**: signal_generation, api_server

4ex.ninja Alert System | ID: alert_1628784456
```

## 🚀 Quick Start

1. **Create Discord server** using this template
2. **Set up channels** and roles as described
3. **Create webhooks** for each channel
4. **Run setup script**: `./setup_discord.sh`
5. **Test integration**: `python3 test_discord_integration.py`
6. **Start receiving signals**! 🎉

## 🔧 Maintenance

### Regular Tasks:
- Monitor webhook delivery rates
- Check notification preferences
- Update role permissions as needed
- Review channel usage and adjust rate limits
- Clean up old messages if needed

### Troubleshooting:
- Test webhooks with Discord webhook tester
- Check server audit logs for permission issues
- Monitor bot logs for rate limiting
- Verify environment variables are correct

Your Discord server is now ready for professional trading signal delivery! 📊🚀
