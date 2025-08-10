# Discord Integration Setup Guide - 4ex.ninja

## 🚀 Overview

This guide walks you through setting up Discord integration for 4ex.ninja, enabling real-time trading signal notifications, system alerts, and community engagement features.

## 📋 Prerequisites

- Discord server (admin access required)
- Python 3.8+ with required packages installed
- 4ex.ninja backend running
- Basic knowledge of Discord webhooks

## 🔧 Setup Process

### Step 1: Install Required Packages

```bash
cd /Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend
pip install aiohttp discord-webhook
```

### Step 2: Discord Server Setup

#### 2.1 Create Discord Server Channels

Create the following channels in your Discord server:

1. **#signals-free** - Free tier trading signals
2. **#signals-premium** - Premium trading signals (high confidence)
3. **#alerts-critical** - Critical system alerts (admin only)
4. **#alerts-general** - General system alerts (admin only)
5. **#market-analysis** - Market analysis and trends
6. **#system-status** - System status updates
7. **#general** - Community discussions

#### 2.2 Configure Channel Permissions

For each channel, set appropriate permissions:

- **Free Channels** (#signals-free, #system-status, #general):
  - @everyone: Read Messages ✅
  - @everyone: Send Messages ❌ (webhook only)

- **Premium Channels** (#signals-premium, #market-analysis):
  - @Premium role: Read Messages ✅
  - @everyone: Read Messages ❌

- **Admin Channels** (#alerts-critical, #alerts-general):
  - @Admin role: Read Messages ✅
  - @everyone: Read Messages ❌

#### 2.3 Create Discord Webhooks

For each channel, create a webhook:

1. Go to channel settings → Integrations → Webhooks
2. Click "Create Webhook"
3. Set name to "4ex.ninja"
4. Copy the webhook URL
5. Save the webhook

### Step 3: Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Discord Webhook URLs
DISCORD_WEBHOOK_SIGNALS_FREE=https://discord.com/api/webhooks/1403982488845549648/Nh3_T7WBOv4BuD0AFtDbbtN3r50JKYaHj0OIQmiDnN9NvSzXg5upj4UNoI3HdFryPuyY
DISCORD_WEBHOOK_SIGNALS_PREMIUM=https://discord.com/api/webhooks/1403982689379418143/1M5-WvGne7VzeI7aVZ5Q4sloRv9I0F-np8mUBHomroA30_TJQUTOXNvTgPb5ko3-muN5
DISCORD_WEBHOOK_ALERTS_CRITICAL=https://discord.com/api/webhooks/1403983698872897578/IisTRZ8uR-41eSiiTi5MhVrYKDI6akacBKNHtr1eOQEsUjOMJ_dY5COyGOjBMsEJil8O
DISCORD_WEBHOOK_ALERTS_GENERAL=https://discord.com/api/webhooks/1403983827801735198/qphjnivNPBpcRr3keFnJWfHN3wQ5mbjT3bkSJ99eHhQ_aUH7up1b0-poV4ZOgswbBQIV
DISCORD_WEBHOOK_MARKET_ANALYSIS=https://discord.com/api/webhooks/1403983962929369108/jxdu5M3rRqTq_m2OjQVJOe9f9MW5pam6gUb-USoJBp_G_Ko0JIDZzZjkORAZXCZBvlgf
DISCORD_WEBHOOK_SYSTEM_STATUS=https://discord.com/api/webhooks/1403984103530958890/HKPKtPDWAw095LHFZiHYJNwvfacnHgJnzKS0Vw0cm9FhMFCfQNylhSHp9rsQ_xW3Ate3
DISCORD_WEBHOOK_COMMUNITY=https://discord.com/api/webhooks/1403984239501901866/IbKJsLVxsmfSEidhqKPIsq-XLSuGc4uwyaYBExoGSYanH13PzHvZ82G2TBqV4ILSN61_

# Optional: Discord Branding
DISCORD_AVATAR_URL=https://your-domain.com/logo.png
DISCORD_FOOTER_ICON_URL=https://your-domain.com/favicon.ico
DISCORD_BRAND_COLOR=0x1DB954
```

### Step 4: Test Integration

Run the test script to verify everything is working:

```bash
cd /Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend
python test_discord_integration.py
```

Expected output:
```
🚀 Starting Discord Integration Tests for 4ex.ninja
============================================================

📋 Checking Configuration...
  ✅ DISCORD_WEBHOOK_SIGNALS_FREE: Configured
  ✅ DISCORD_WEBHOOK_SIGNALS_PREMIUM: Configured
  ...

🧪 Running Tests...
----------------------------------------

Signal Notification:
  📤 Sending to Free Tier Channel...
  📤 Sending to Premium Tier Channel...
  ✅ Free tier: Success
  ✅ Premium tier: Success

📊 Test Results Summary
============================================================
  ✅ PASS: Signal Notification
  ✅ PASS: System Alert
  ✅ PASS: Market Analysis
  ✅ PASS: System Status
  ✅ PASS: Enhanced Alert Channel

🎯 Overall: 5/5 tests passed
🎉 All tests passed! Discord integration is working correctly.
```

## 📱 Usage Examples

### Sending Trading Signals

```python
from core.entities.signal import Signal, SignalType, CrossoverType
from infrastructure.external_services.discord_service import get_discord_service, UserTier

# Create signal
signal = Signal(
    signal_id="EUR_USD_001",
    pair="EUR/USD",
    timeframe="1H",
    signal_type=SignalType.BUY,
    crossover_type=CrossoverType.BULLISH,
    entry_price=Decimal("1.1050"),
    current_price=Decimal("1.1055"),
    fast_ma=50,
    slow_ma=200,
    timestamp=datetime.now(timezone.utc),
    confidence_score=0.85
)

# Send to Discord
discord_service = get_discord_service()
await discord_service.send_signal_notification(
    signal=signal,
    user_tier=UserTier.PREMIUM,
    additional_context={
        "market_conditions": "Trending upward",
        "volatility": "Medium"
    }
)
```

### Sending System Alerts

```python
from infrastructure.monitoring.alerts import Alert, AlertSeverity, AlertType

# Create alert
alert = Alert(
    alert_type=AlertType.SYSTEM_RESOURCE_EXHAUSTION,
    severity=AlertSeverity.CRITICAL,
    title="High CPU Usage",
    message="CPU usage exceeded 95%",
    timestamp=datetime.now(timezone.utc),
    context={"cpu_usage": "96.5%"}
)

# Send through existing alert system (Discord channel will be used automatically)
await alert_manager.trigger_alert(alert)
```

### Sending Market Analysis

```python
from infrastructure.monitoring.discord_alerts import send_market_analysis_to_discord

await send_market_analysis_to_discord(
    title="EUR/USD Daily Analysis",
    analysis="Strong bullish momentum following ECB meeting...",
    trend_data={
        "short_term": "Bullish (95% confidence)",
        "trend_strength": "Strong"
    }
)
```

## 🎨 Discord Message Examples

### Trading Signal Format

```
🟢 BUY Signal - EUR/USD

**BULLISH** crossover detected

📊 Entry Price: $1.10500
⏰ Timeframe: 1H
💪 Confidence: 85.0%
🛑 Stop Loss: $1.10000
🎯 Take Profit: $1.11500
⚖️ Risk/Reward: 1:2.00

📈 Moving Averages: Fast: 50 | Slow: 200
📊 ATR: 0.00250

ℹ️ Additional Info
**market_conditions**: Trending upward
**volatility**: Medium
**session**: London Open

4ex.ninja | Signal ID: EUR_USD_001
```

### System Alert Format

```
🚨 High CPU Usage Detected

CPU usage has exceeded 95% for the last 5 minutes. Immediate attention required.

🔍 Alert Type: System Resource Exhaustion
⚡ Severity: CRITICAL
📍 Status: Active

📋 Context
**cpu_usage**: 96.5%
**memory_usage**: 78.2%
**process_count**: 145

4ex.ninja Alert System | ID: system_resource_exhaustion_1628784123
```

## 🔧 Advanced Configuration

### Role-Based Access Control

Set up Discord roles for different user tiers:

1. Create roles: `@Free`, `@Premium`, `@Admin`
2. Assign appropriate channel permissions
3. Set up role reaction bots for automatic role assignment

### Rate Limiting Configuration

Adjust rate limits in the Discord service configuration:

```python
# In discord_service.py factory function
channels = {
    DiscordChannelType.SIGNALS_FREE: DiscordChannelConfig(
        name="signals-free",
        rate_limit=20,  # messages per minute
        # ...
    ),
    # ...
}
```

### Custom Branding

Customize Discord message appearance:

```bash
# Set custom avatar and footer icons
DISCORD_AVATAR_URL=https://your-domain.com/bot-avatar.png
DISCORD_FOOTER_ICON_URL=https://your-domain.com/favicon.ico

# Set brand color (hex format)
DISCORD_BRAND_COLOR=0x1DB954  # Spotify green
```

## 🛠️ Troubleshooting

### Common Issues

1. **Webhook URL not working**
   - Verify the webhook URL is correct
   - Check if the webhook was deleted in Discord
   - Ensure the bot has permission to send messages

2. **Messages not appearing**
   - Check rate limiting (max 30 messages per minute per webhook)
   - Verify environment variables are set correctly
   - Check Discord server outages

3. **Permission errors**
   - Ensure webhook has proper channel permissions
   - Check if channel exists and is accessible

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger("infrastructure.external_services.discord_service").setLevel(logging.DEBUG)
logging.getLogger("infrastructure.monitoring.discord_alerts").setLevel(logging.DEBUG)
```

### Test Individual Components

```python
# Test Discord service directly
discord_service = get_discord_service()
print("Available channels:", list(discord_service.config.channels.keys()))

# Test webhook connectivity
async def test_webhook():
    success = await discord_service._send_with_aiohttp(
        webhook_url="YOUR_WEBHOOK_URL",
        embed_data={"content": "Test message"}
    )
    print(f"Webhook test: {'Success' if success else 'Failed'}")
```

## 📈 Monitoring and Analytics

### Discord Integration Metrics

The system automatically tracks:

- Message delivery success rates
- Rate limiting events
- Channel-specific activity
- User engagement metrics

### Performance Monitoring

Monitor Discord integration performance:

```python
from infrastructure.monitoring.system_metrics import system_metrics_monitor

# Check Discord notification performance
metrics = system_metrics_monitor.get_current_metrics()
if metrics:
    print(f"Discord notifications sent: {metrics.custom_counters.get('discord_notifications', 0)}")
```

## 🔮 Future Enhancements

### Planned Features

1. **Interactive Discord Bot**
   - Slash commands for signal queries
   - Real-time portfolio tracking
   - Alert configuration via Discord

2. **Advanced Analytics**
   - Signal performance tracking
   - User engagement analytics
   - A/B testing for message formats

3. **Community Features**
   - Signal voting and feedback
   - Community-driven analysis
   - Leaderboards and competitions

### Integration Roadmap

- **Week 1-2**: Basic webhook integration (✅ Complete)
- **Week 3-4**: Real-time signal streaming
- **Week 5-6**: Interactive bot features
- **Week 7-8**: Community engagement tools

## 🤝 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review Discord webhook documentation
3. Run the test script to diagnose issues
4. Check system logs for error messages

## 📚 Resources

- [Discord Webhook Guide](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)
- [Discord Rate Limiting](https://discord.com/developers/docs/topics/rate-limits)
- [4ex.ninja Alert System Documentation](./ALERTS-IMPLEMENTATION-COMPLETE.md)
