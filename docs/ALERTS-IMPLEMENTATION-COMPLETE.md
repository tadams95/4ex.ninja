# Alert System Implementation - 4ex.ninja

## 🚨 Overview

The 4ex.ninja alert system provides comprehensive monitoring and alerting capabilities for critical system failures, including signal processing failures, database connectivity issues, and system resource exhaustion.

## ✅ Features Implemented

### 1. Alert Management System
- **AlertManager**: Centralized alert management with routing, escalation, and deduplication
- **Alert Types**: Signal processing, database connectivity, external API, system resources, authentication, data corruption, performance degradation
- **Severity Levels**: Critical, High, Medium, Low, Info
- **Alert Status**: Active, Acknowledged, Resolved, Suppressed

### 2. Alert Channels
- **Log Channel**: Always available for logging alerts
- **Email Channel**: SMTP-based email notifications (configurable via environment variables)
- **Webhook Channel**: Discord/Slack integration (configurable via environment variables)

### 3. API Endpoints
All endpoints are available under `/api/v1/alerts/`:

- `GET /api/v1/alerts/` - List alerts with filtering (status, severity, pagination)
- `GET /api/v1/alerts/active` - Get currently active alerts
- `GET /api/v1/alerts/statistics` - Alert statistics and trends
- `GET /api/v1/alerts/channels` - Channel status and availability
- `GET /api/v1/alerts/config` - Current alert configuration
- `POST /api/v1/alerts/{alert_id}/acknowledge` - Acknowledge an alert
- `POST /api/v1/alerts/{alert_id}/resolve` - Resolve an alert
- `POST /api/v1/alerts/test` - Send test alert

### 4. Monitoring Integration
- **System Metrics**: Automatic alerts for CPU, memory, and disk usage thresholds
- **Health Checks**: Alerts for database and external API failures
- **Error Tracking**: Integration with error handling systems

## 🔧 Configuration

### Environment Variables

#### Email Alerts
```bash
# Enable email alerts by setting these variables
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=alerts@yourdomain.com
ALERT_TO_EMAILS=admin@yourdomain.com,ops@yourdomain.com
```

#### Discord Webhook Alerts
```bash
# Enable Discord alerts
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

### Alert Thresholds (Default)
- **CPU Usage**: > 90%
- **Memory Usage**: > 85%
- **Disk Usage**: > 90%
- **Database**: Connection failures
- **External APIs**: Health check failures

## 📊 Alert Types

### 1. System Resource Alerts
- **CPU Exhaustion**: High CPU usage above threshold
- **Memory Exhaustion**: High memory usage above threshold
- **Disk Exhaustion**: High disk usage above threshold

### 2. Infrastructure Alerts
- **Database Connectivity**: Connection pool failures, query timeouts
- **External API Downtime**: OANDA API or other service failures
- **Circuit Breaker Triggered**: Service protection mechanisms activated

### 3. Application Alerts
- **Signal Processing Failure**: Trading signal generation errors
- **Authentication Failure**: Login/security issues
- **Data Corruption**: Data consistency problems
- **Performance Degradation**: Slow response times

## 🚀 Usage Examples

### Triggering Alerts Programmatically

```python
from infrastructure.monitoring.alerts import (
    trigger_system_resource_alert,
    alert_database_connectivity,
    alert_signal_processing_failure
)

# System resource alert
await trigger_system_resource_alert(
    resource_type="cpu",
    current_value=95.0,
    threshold=90.0,
    context={"process_count": 150}
)

# Database connectivity alert
await alert_database_connectivity(
    message="Connection pool exhausted",
    context={"pool_size": 10, "active_connections": 10}
)

# Signal processing alert
await alert_signal_processing_failure(
    message="Failed to generate EUR/USD signal",
    context={"pair": "EUR/USD", "error": "Insufficient data"}
)
```

### API Usage

```bash
# Get active alerts
curl http://localhost:8000/api/v1/alerts/active

# Get alert statistics
curl http://localhost:8000/api/v1/alerts/statistics

# Acknowledge an alert
curl -X POST "http://localhost:8000/api/v1/alerts/{alert_id}/acknowledge?acknowledged_by=admin"

# Test the alert system
curl -X POST http://localhost:8000/api/v1/alerts/test
```

## 📈 Monitoring Dashboard

The alert system provides statistics and metrics for:
- **Total alerts** generated
- **Active alerts** requiring attention
- **Alert frequency** by type and severity
- **Response times** and resolution statistics
- **Channel availability** and success rates

## 🔧 Customization

### Adding Custom Alert Rules

```python
# Add custom routing rule
alert_manager.add_alert_rule({
    "severity": [AlertSeverity.CRITICAL],
    "alert_type": [AlertType.SIGNAL_PROCESSING_FAILURE],
    "channels": ["logs", "email", "webhook"],
    "immediate": True
})

# Add suppression rule
alert_manager.add_suppression_rule({
    "alert_type": AlertType.SYSTEM_RESOURCE_EXHAUSTION,
    "deduplication_window": 600,  # 10 minutes
    "max_occurrences": 1
})
```

### Custom Alert Channels

```python
class SlackAlertChannel(AlertChannel):
    async def send_alert(self, alert: Alert) -> bool:
        # Implement Slack webhook integration
        pass
    
    def is_available(self) -> bool:
        return bool(self.webhook_url)

# Register custom channel
alert_manager.add_channel("slack", SlackAlertChannel(webhook_url))
```

## 🔍 Testing

The alert system includes comprehensive testing:

```bash
# Test alert functionality
python3 -c "
import sys; sys.path.append('./src')
from infrastructure.monitoring.alerts import alert_manager
import asyncio

async def test():
    # Trigger test alert
    from infrastructure.monitoring.alerts import trigger_system_resource_alert
    await trigger_system_resource_alert('cpu', 95.0, 90.0, {'test': True})
    
    # Check results
    alerts = alert_manager.get_active_alerts()
    print(f'Active alerts: {len(alerts)}')

asyncio.run(test())
"
```

## 🛠️ Troubleshooting

### Common Issues

1. **Email alerts not working**
   - Check SMTP environment variables
   - Verify email credentials and app passwords
   - Check firewall/network restrictions

2. **Webhook alerts not working**
   - Verify Discord webhook URL
   - Check webhook permissions
   - Review Discord rate limits

3. **High alert volume**
   - Review alert thresholds
   - Implement suppression rules
   - Check for system issues

### Logs and Debugging

```bash
# Check alert logs
grep "ALERT" logs/app.log

# Monitor alert system status
curl http://localhost:8000/api/v1/alerts/channels
```

## 📋 Production Checklist

- [ ] Configure email SMTP settings
- [ ] Set up Discord/Slack webhooks
- [ ] Review and adjust alert thresholds
- [ ] Test all alert channels
- [ ] Set up alert escalation procedures
- [ ] Configure monitoring dashboards
- [ ] Train team on alert acknowledgment process
- [ ] Document incident response procedures

## 🎯 Next Steps

The alert system is production-ready and includes:
- ✅ Comprehensive alert types and severities
- ✅ Multiple notification channels
- ✅ REST API for management
- ✅ Integration with monitoring systems
- ✅ Deduplication and escalation
- ✅ Configuration via environment variables

This completes the **"Alerts for Monitoring & Observability"** implementation as specified in the development priorities.
