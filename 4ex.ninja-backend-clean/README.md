# 4ex.ninja Clean Backend

A production-focused, streamlined backend for the 4ex.ninja trading system, implementing optimal Moving Average strategy parameters.

## Overview

This clean backend was created to eliminate technical debt and deployment issues from the original complex structure. It focuses specifically on the validated optimal MA strategy configuration that achieves **18.0-19.8% returns**.

### Key Features

- **Optimal MA Strategy**: Conservative moderate daily parameters (fast_ma=50, slow_ma=200)
- **8 Currency Pairs**: EUR_USD, GBP_USD, USD_JPY, AUD_USD, EUR_GBP, GBP_JPY, NZD_USD, USD_CAD
- **Production Ready**: Single entry point, clean architecture, minimal dependencies
- **Real-time Signals**: MA crossover detection with confidence scoring
- **Discord Integration**: Automated signal notifications
- **Performance Tracking**: Metrics for all supported strategies

## Validated Performance

Based on batch_1_results.json validation:

| Pair | Expected Return | Strategy Type |
|------|----------------|---------------|
| EUR_USD_D | 18.0% | conservative_moderate_daily |
| GBP_USD_D | 19.8% | conservative_moderate_daily |
| USD_JPY_D | 18.5% | conservative_moderate_daily |
| AUD_USD_D | 18.2% | conservative_moderate_daily |
| EUR_GBP_D | 18.7% | conservative_moderate_daily |
| GBP_JPY_D | 19.1% | conservative_moderate_daily |
| NZD_USD_D | 18.3% | conservative_moderate_daily |
| USD_CAD_D | 18.9% | conservative_moderate_daily |

## Architecture

```
4ex.ninja-backend-clean/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── deploy.sh             # Deployment script
├── test_backend.py       # Test suite
├── config/
│   └── settings.py       # Configuration and optimal parameters
├── models/
│   └── signal_models.py  # Data models
└── services/
    ├── ma_strategy_service.py    # MA strategy calculations
    ├── signal_service.py         # Signal management
    ├── notification_service.py   # Discord notifications
    └── data_service.py          # Price data provider
```

## API Endpoints

### Health Check
- `GET /health` - System health and status

### Strategy Configuration
- `GET /strategy/config` - Get all strategy configurations
- `GET /strategy/config/{pair}` - Get specific pair configuration

### Signal Generation
- `POST /signals/generate` - Generate signal for specific pair
- `POST /signals/generate-all` - Generate signals for all pairs
- `GET /signals/recent` - Get recent signals
- `GET /signals/active` - Get active BUY/SELL signals

### Performance Metrics
- `GET /performance/{pair}` - Get performance metrics for pair
- `GET /performance/all` - Get all performance metrics

### Notifications
- `POST /notifications/test` - Send test Discord notification

## Quick Start

### Local Development

1. **Install Dependencies**
   ```bash
   cd 4ex.ninja-backend-clean
   pip install -r requirements.txt
   ```

2. **Run Backend**
   ```bash
   python -m uvicorn app:app --reload --port 8000
   ```

3. **Test Backend**
   ```bash
   python test_backend.py
   ```

4. **Visit API Docs**
   - http://localhost:8000/docs (Swagger UI)
   - http://localhost:8000/health (Health Check)

### Production Deployment

1. **Deploy to Digital Ocean Droplet**
   ```bash
   ./deploy.sh
   ```

2. **Verify Deployment**
   ```bash
   curl http://165.227.5.89:8000/health
   ```

## Configuration

### Environment Variables

Create `.env` file:

```env
ENVIRONMENT=production
MONGODB_URL=mongodb://localhost:27017/4ex_ninja
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
OANDA_API_KEY=your_oanda_api_key
OANDA_ACCOUNT_ID=your_oanda_account_id
REDIS_URL=redis://localhost:6379
```

### Optimal Strategy Parameters

The backend is pre-configured with validated optimal parameters:

```python
# Fast MA Period: 50
# Slow MA Period: 200
# Source: Close price
# Strategy Type: conservative_moderate_daily
```

## Testing

### Automated Tests

```bash
# Run all tests
python test_backend.py

# Test specific endpoint
curl http://localhost:8000/strategy/config
```

### Test Results Expected

- ✅ Health Check: Status "healthy" with strategy count 8
- ✅ Strategy Config: 8 configurations with optimal parameters
- ✅ Signal Generation: BUY/SELL/HOLD signals with confidence
- ✅ Performance Metrics: Returns matching validation results

## Deployment

### Prerequisites

- Python 3.8+
- Digital Ocean droplet with SSH access
- Discord webhook URL (optional)

### Deployment Process

1. **Automated Deployment**
   ```bash
   ./deploy.sh
   ```

2. **Manual Verification**
   ```bash
   ssh root@165.227.5.89
   systemctl status 4ex-ninja-backend
   journalctl -u 4ex-ninja-backend -f
   ```

### Service Management

```bash
# Start service
systemctl start 4ex-ninja-backend

# Stop service
systemctl stop 4ex-ninja-backend

# Restart service
systemctl restart 4ex-ninja-backend

# View logs
journalctl -u 4ex-ninja-backend -f
```

## Monitoring

### Health Checks

- **Backend**: http://165.227.5.89:8000/health
- **Strategy Count**: Should show 8 active strategies
- **Signal Generation**: Test with EUR_USD_D pair

### Performance Verification

1. **Check Strategy Returns**
   ```bash
   curl http://165.227.5.89:8000/performance/EUR_USD
   ```

2. **Verify Optimal Parameters**
   ```bash
   curl http://165.227.5.89:8000/strategy/config
   ```

3. **Monitor Signal Generation**
   ```bash
   curl -X POST http://165.227.5.89:8000/signals/generate-all
   ```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs
   journalctl -u 4ex-ninja-backend -n 50
   
   # Check dependencies
   cd /opt/4ex-ninja-backend
   python -m pip list
   ```

2. **Import Errors**
   ```bash
   # Ensure proper Python path
   export PYTHONPATH=/opt/4ex-ninja-backend:$PYTHONPATH
   ```

3. **Port Conflicts**
   ```bash
   # Check what's using port 8000
   netstat -tulpn | grep 8000
   ```

### Logs Location

- **System Logs**: `journalctl -u 4ex-ninja-backend`
- **Application Logs**: Check systemd journal
- **Error Logs**: Captured in systemd service

## Performance Expectations

Based on validation results, the clean backend should deliver:

- **Average Return**: 18.0-19.8% annually
- **Strategy Type**: Conservative moderate daily
- **Signal Accuracy**: High confidence with MA crossover validation
- **Latency**: < 100ms for signal generation
- **Uptime**: 99.9% with systemd auto-restart

## Support

For issues or questions:

1. Check logs: `journalctl -u 4ex-ninja-backend -f`
2. Verify optimal parameters: `curl http://localhost:8000/strategy/config`
3. Test signal generation: `python test_backend.py`
4. Review deployment: `./deploy.sh` (dry run)

---

**Built for optimal 18.0-19.8% returns with conservative_moderate_daily MA strategy**
