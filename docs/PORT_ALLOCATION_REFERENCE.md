# 4ex.ninja Port Allocation Reference

**Digital Ocean Droplet: 157.230.58.248**

## Port Usage Status

### Currently Allocated Ports

| Port | Service | Status | Process | Description |
|------|---------|--------|---------|-------------|
| 8000 | Backend (Legacy) | 🔴 **OCCUPIED** | Unknown process | Original backend service - port conflict |
| 8081 | Monitoring Dashboard | 🟢 **ACTIVE** | PID 57709 (`/var/www/4ex.ninja/venv/bin/python -m uvicorn src.monitoring.dashboard_api:app`) | Phase 2 Monitoring Dashboard API |
| 8082 | Backtesting API | 🟢 **ACTIVE** | systemd service `4ex-backend.service` | **Phase 2.1 Universal Backtesting API** |
| 8083 | **RESERVED** | 🟡 **AVAILABLE** | N/A | **LAST AVAILABLE PORT - Reserve for critical service** |

### Available Ports (Tested)

| Port | Status | Notes |
|------|--------|-------|
| 8083 | � **RESERVED** | **LAST AVAILABLE PORT** - Reserve for critical service only |
| 8084+ | ❌ **NOT AVAILABLE** | Beyond droplet port allocation limit |

## Service Configurations

### Phase 2.1 Backtesting API (Port 8082)
- **Service File**: `/etc/systemd/system/4ex-backend.service`
- **Working Directory**: `/var/www/4ex.ninja/4ex.ninja-backend/src`
- **Command**: `/root/venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8082`
- **Status**: ✅ **OPERATIONAL**
- **Endpoints**: `http://157.230.58.248:8082/api/v1/backtest/*`

### Monitoring Dashboard (Port 8081)
- **Process**: `/var/www/4ex.ninja/venv/bin/python -m uvicorn src.monitoring.dashboard_api:app --host 0.0.0.0 --port 8081`
- **Status**: ✅ **OPERATIONAL**
- **Endpoints**: `http://157.230.58.248:8081/*`

## Deployment History & Issues

### Port 8000 - FAILED ❌
- **Issue**: Address already in use
- **Error**: `ERROR: [Errno 98] error while attempting to bind on address ('0.0.0.0', 8000): address already in use`
- **Resolution**: Switched to port 8082

### Port 8081 - CONFLICT ❌
- **Issue**: Already occupied by monitoring dashboard
- **Process**: PID 57709 - monitoring dashboard API
- **Resolution**: Switched to port 8082

### Port 8082 - SUCCESS ✅
- **Status**: Successfully deployed Phase 2.1 Backtesting API
- **Service**: `4ex-backend.service` running successfully
- **Endpoints**: All 5 backtest endpoints operational

## Quick Reference Commands

### Check Port Usage
```bash
# Check what's running on a specific port
ssh root@157.230.58.248 "netstat -tlnp | grep :8082"

# Check all Python processes and their ports
ssh root@157.230.58.248 "ps aux | grep python | grep -v grep"

# Check systemd services
ssh root@157.230.58.248 "systemctl status 4ex-backend"
```

### Test Endpoints
```bash
# Test Backtesting API (Port 8082)
curl http://157.230.58.248:8082/api/v1/backtest/health
curl http://157.230.58.248:8082/api/v1/backtest/strategies

# Test Monitoring Dashboard (Port 8081)
curl http://157.230.58.248:8081/health
```

### Deploy to New Port
```bash
# Update systemd service to use port 8083 (example)
ssh root@157.230.58.248 "
sed -i 's/--port 8082/--port 8083/g' /etc/systemd/system/4ex-backend.service
systemctl daemon-reload
systemctl restart 4ex-backend
"
```

## Future Deployment Guidelines

1. **Always check port availability first**:
   ```bash
   ssh root@157.230.58.248 "netstat -tlnp | grep :XXXX"
   ```

2. **Use ports in sequence**: 8083, 8084, 8085, etc.

3. **Update this document** when allocating new ports

4. **Test endpoints** after deployment to confirm functionality

## Service Architecture

```
Digital Ocean Droplet (157.230.58.248)
├── Port 8081: Monitoring Dashboard API
│   ├── /health
│   ├── /performance/*
│   ├── /regime/*
│   └── /alerts/*
│
└── Port 8082: Phase 2.1 Backtesting API  
    └── /api/v1/backtest/*
        ├── /health
        ├── /strategies
        ├── /run
        └── /results
```

## Port Constraint Analysis & Recommendations

### 🚨 **CRITICAL: Only 1 Port Remaining (8083)**

**Current Usage (3/4 ports occupied):**
- Port 8000: Legacy Backend (essential)
- Port 8081: Monitoring Dashboard (essential)
- Port 8082: Backtesting API (newly deployed)
- Port 8083: **LAST AVAILABLE PORT**

### 🎯 **Strategic Recommendations for Future Deployments**

#### **Option 1: Service Consolidation (RECOMMENDED)**
**Merge backtesting API into monitoring dashboard to free up port 8082:**

```bash
# Stop backtesting service
ssh root@157.230.58.248 "systemctl stop 4ex-backend"

# Update monitoring dashboard (port 8081) to include backtesting routes
# Add to existing dashboard_api.py:
app.include_router(backtest_router, prefix="/api/v1/backtest")
app.include_router(monitoring_router, prefix="/api/v1/monitoring")

# Result: Single API on port 8081 with both monitoring and backtesting
```

**Benefits:**
- ✅ Frees up port 8082 for critical future services
- ✅ Single API endpoint: `http://157.230.58.248:8081/api/v1/`
- ✅ Easier management and documentation
- ✅ Preserves port 8083 for truly essential services

#### **Option 2: Nginx Reverse Proxy (LONG-TERM SOLUTION)**
**Set up nginx to route multiple services through port 80/443:**

```nginx
# nginx configuration example
server {
    listen 80;
    server_name 157.230.58.248;
    
    location /api/v1/backtest/ {
        proxy_pass http://localhost:8082;
    }
    
    location /api/v1/monitoring/ {
        proxy_pass http://localhost:8081;
    }
    
    location /api/v1/trading/ {
        proxy_pass http://localhost:8083;  # Future trading API
    }
}
```

**Benefits:**
- ✅ Unlimited services behind standard HTTP ports
- ✅ Professional deployment structure
- ✅ SSL termination capability
- ✅ Load balancing possibilities

#### **Option 3: Reserve Port 8083 (CURRENT APPROACH)**
**Keep current setup and reserve final port for critical service:**

**Suitable for port 8083:**
- Live Trading API (highest priority)
- Real-time Strategy Execution Engine
- External Integration Gateway
- WebSocket Real-time Data Feed

### 🚨 **Immediate Action Required**

**For next deployment, MUST choose:**
1. **Consolidate APIs** (recommended for immediate relief)
2. **Set up nginx** (recommended for long-term scalability)
3. **Use final port 8083** (only if absolutely critical service)

### 📋 **Future Deployment Checklist**

Before deploying any new service:
1. ✅ Check available ports: `./check_ports.sh`
2. ✅ Consider consolidation with existing services
3. ✅ Evaluate if nginx setup is needed
4. ✅ Update this document with new allocations
5. ✅ Test all existing services after changes

## Last Updated
- **Date**: August 16, 2025
- **Deployment**: Phase 2.1 Universal Backtesting API
- **Current Status**: All services operational
- **Port Status**: 🚨 **3/4 ports used - ONLY 1 REMAINING**
