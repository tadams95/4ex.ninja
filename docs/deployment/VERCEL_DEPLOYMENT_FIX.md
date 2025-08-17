# Solution: Mixed Content Policy Fix for Vercel Deployment

## Problem
When deployed to Vercel (HTTPS), the app cannot make HTTP requests to `http://157.230.58.248:8081` due to browser security policies:
- **Mixed Content Policy**: HTTPS pages cannot make HTTP requests
- **Error**: "Failed to fetch" / "Network error: Cannot connect"

## Solution: API Proxy
Created Next.js API routes that proxy requests server-side to bypass browser restrictions.

### 1. Proxy Implementation
- **File**: `src/app/api/monitoring/[...path]/route.ts`
- **Purpose**: Proxies all monitoring API requests server-side
- **URL Pattern**: `/api/monitoring/*` → `http://157.230.58.248:8081/*`

### 2. Updated Hook Logic
- **Development**: Uses direct HTTP connection
- **Production (HTTPS)**: Automatically uses proxy endpoint
- **Environment Variable Override**: Supports custom endpoints

### 3. Vercel Environment Setup

Set this environment variable in your Vercel project:

```bash
NEXT_PUBLIC_MONITORING_API_URL=/api/monitoring
```

**How to set in Vercel:**
1. Go to your Vercel project dashboard
2. Navigate to "Settings" → "Environment Variables"
3. Add:
   - **Name**: `NEXT_PUBLIC_MONITORING_API_URL`
   - **Value**: `/api/monitoring`
   - **Environment**: Production

### 4. Testing Endpoints

After deployment, test these URLs:

```bash
# Health check (should work)
curl https://your-app.vercel.app/api/monitoring-health

# Proxy endpoints (should work)
curl https://your-app.vercel.app/api/monitoring/regime/current
curl https://your-app.vercel.app/api/monitoring/alerts/recent
curl https://your-app.vercel.app/api/monitoring/strategy/health
curl https://your-app.vercel.app/api/monitoring/performance/summary
```

### 5. Debug Information

The updated dashboard now shows:
- Which endpoint is being used (direct vs proxy)
- Environment details (HTTP vs HTTPS)
- Better error messages
- Link to test proxy health

### 6. Troubleshooting

**If proxy still fails:**
1. Check Vercel function logs in dashboard
2. Verify monitoring service is accessible from Vercel's servers
3. Test proxy health endpoint: `/api/monitoring-health`

**Error patterns:**
- `"Proxy connection failed"` = Server-side connection issue
- `"Direct connection failed"` = Browser CORS/mixed content issue
- `"Request timeout"` = Monitoring service is slow/down

### 7. Alternative Solutions

If proxy doesn't work, you can:

1. **Fix HTTPS on monitoring server** (recommended long-term)
   ```bash
   # Set this environment variable instead
   NEXT_PUBLIC_MONITORING_API_URL=https://157.230.58.248:8081
   ```

2. **Use subdomain with proper SSL**
   ```bash
   # Example: Set up api.4ex.ninja pointing to monitoring server
   NEXT_PUBLIC_MONITORING_API_URL=https://api.4ex.ninja
   ```

## Deployment Steps

1. **Add environment variable in Vercel**:
   ```
   NEXT_PUBLIC_MONITORING_API_URL=/api/monitoring
   ```

2. **Deploy the updated code** (includes proxy routes)

3. **Test the endpoints** after deployment

4. **Monitor Vercel function logs** for any server-side errors

The proxy approach is the most reliable solution for your current setup, avoiding the need to fix SSL certificates on the monitoring server.
