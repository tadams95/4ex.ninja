# Monitoring Service Deployment Guide

## Overview

This guide helps you check if the monitoring service is deployed and accessible from your production build.

## Current Status

✅ **HTTP Endpoint**: `http://157.230.58.248:8081` - Working perfectly
❌ **HTTPS Endpoint**: `https://157.230.58.248:8081` - SSL/TLS configuration issues

## Health Check Tools

### 1. Comprehensive Health Check Script
```bash
./check_monitoring_service.sh
```

**Features:**
- Tests all endpoints (HTTP/HTTPS)
- Checks CORS configuration
- Validates JSON response format
- Measures response times
- Provides detailed recommendations

### 2. Pre-Deployment Check
```bash
./pre_deploy_check.sh
```

**Features:**
- Quick check for CI/CD pipelines
- Automatically updates environment configuration
- Returns exit code for automated deployments

### 3. React Components

#### Health Status Component
```tsx
import { MonitoringHealthStatus } from '../components/MonitoringHealthStatus';

// Basic usage
<MonitoringHealthStatus />

// With details
<MonitoringHealthStatus showDetails={true} />
```

#### Production Health Check Component
```tsx
import { ProductionHealthCheck } from '../components/MonitoringHealthStatus';

<ProductionHealthCheck />
```

### 4. Programmatic Health Checks
```tsx
import { quickHealthCheck, getRecommendedApiBaseUrl } from '../utils/monitoringHealthCheck';

// Quick boolean check
const isHealthy = await quickHealthCheck();

// Get best endpoint
const bestEndpoint = await getRecommendedApiBaseUrl();
```

## Environment Configuration

### Production (.env.production)
```env
NEXT_PUBLIC_MONITORING_API_URL=http://157.230.58.248:8081
```

### Development (.env.local)
```env
NEXT_PUBLIC_MONITORING_API_URL=http://localhost:8081
```

## Integration in CI/CD

### GitHub Actions Example
```yaml
- name: Check Monitoring Service
  run: |
    ./pre_deploy_check.sh
    if [ $? -eq 0 ]; then
      echo "✅ Monitoring service is accessible"
    else
      echo "❌ Monitoring service check failed"
      exit 1
    fi
```

### Vercel Deployment
Add to your `vercel.json`:
```json
{
  "build": {
    "env": {
      "NEXT_PUBLIC_MONITORING_API_URL": "http://157.230.58.248:8081"
    }
  }
}
```

## Current Issues & Recommendations

### 1. HTTPS SSL Issue
**Problem**: HTTPS endpoint fails with SSL/TLS protocol version error
**Solution**: 
- Use HTTP endpoint for now
- Fix SSL certificate configuration on server
- Consider using a reverse proxy (nginx) with proper SSL

### 2. Production Recommendations
1. **Use HTTP endpoint**: Currently the only working option
2. **Enable proper CORS**: Already configured correctly
3. **Monitor service health**: Use the provided health check components
4. **Set up alerts**: Monitor API availability

## Troubleshooting

### Common Issues

1. **"Failed to fetch" errors**
   - Check if monitoring service is running
   - Verify firewall rules allow port 8081
   - Test with curl: `curl http://157.230.58.248:8081/regime/current`

2. **CORS errors**
   - Verify Origin headers in server configuration
   - Check if server allows your domain

3. **Timeout errors**
   - Check server performance
   - Verify network connectivity
   - Consider increasing timeout values

### Debug Commands

```bash
# Test HTTP endpoint
curl -v http://157.230.58.248:8081/regime/current

# Test HTTPS endpoint (will fail)
curl -v https://157.230.58.248:8081/regime/current

# Check CORS
curl -H "Origin: https://4ex.ninja" -I http://157.230.58.248:8081/regime/current

# Performance test
curl -w "Time: %{time_total}s\n" -o /dev/null -s http://157.230.58.248:8081/regime/current
```

## Next Steps

1. **Fix HTTPS SSL Configuration**
   - Update SSL certificate
   - Configure proper TLS settings
   - Test with health check script

2. **Production Deployment**
   - Run pre-deployment check
   - Use recommended environment variables
   - Monitor service health in production

3. **Monitoring & Alerts**
   - Set up automated health checks
   - Configure alerts for service downtime
   - Monitor API response times

## Files Created

- `utils/monitoringHealthCheck.ts` - Health check utilities
- `components/MonitoringHealthStatus.tsx` - React health status components
- `check_monitoring_service.sh` - Comprehensive health check script
- `pre_deploy_check.sh` - Quick deployment check
- `.env.production.example` - Environment configuration example

All tools work together to ensure your monitoring service is accessible and properly configured for production deployment.
