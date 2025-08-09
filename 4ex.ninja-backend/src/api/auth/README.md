# API Authentication and Rate Limiting

This document describes the authentication and rate limiting system implemented for the 4ex.ninja Trading Platform API.

## Overview

The API implements a comprehensive security system with:

1. **JWT-based Authentication** - Secure token-based authentication
2. **API Key Authentication** - Alternative authentication for integrations
3. **Rate Limiting** - Protection against abuse and DDoS attacks
4. **Role-based Access** - Different access levels for different user types

## Authentication Methods

### 1. JWT Bearer Token Authentication

#### Login Endpoint
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### OAuth2 Compatible Token Endpoint
```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=your_password&grant_type=password
```

#### Using the Token
Include the token in the Authorization header:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Demo Credentials
For testing purposes, use:
- Email: `demo@4ex.ninja`
- Password: `demo123`

### 2. API Key Authentication

For programmatic access, you can use API keys:

```http
X-API-Key: your-api-key-here
```

API keys provide premium access to all endpoints and are suitable for:
- Server-to-server integrations
- Automated trading systems
- Third-party applications

### 3. Current User Information

Get information about the authenticated user:
```http
GET /api/v1/auth/me
Authorization: Bearer your-token-here
```

**Response:**
```json
{
  "id": "user-123",
  "email": "user@example.com",
  "username": "user",
  "is_active": true,
  "is_premium": false
}
```

## Protected Endpoints

### Authentication Required
These endpoints require either JWT token or API key:

- `GET /api/v1/signals/{signal_id}` - Individual signal details
- `GET /api/v1/signals/stats/summary` - Signal statistics
- `GET /api/v1/auth/me` - Current user information
- `POST /api/v1/auth/refresh` - Token refresh

### Public Endpoints
These endpoints work without authentication (may return limited data):

- `GET /api/v1/signals/` - Public signal feed
- `GET /api/v1/market-data/` - Public market data
- `GET /health/` - Health checks

### Premium Endpoints
Future endpoints that require premium subscription:

- Advanced analytics endpoints
- Real-time streaming data
- Custom signal configurations

## Rate Limiting

### Default Rate Limits

**API Endpoints:**
- 100 requests per hour per IP address
- Headers included: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

**Authentication Endpoints:**
- 10 requests per 15 minutes per IP address (stricter limits)
- Applies to: `/auth/login`, `/auth/register`, `/auth/token`

### Rate Limit Response

When rate limit is exceeded:
```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1672531200
Retry-After: 3600

{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Limit: 100 per 3600 seconds",
  "retry_after": 3600
}
```

### Excluded Paths
These paths are not rate limited:
- `/health/` - Health checks
- `/docs` - API documentation
- `/redoc` - Alternative API documentation
- `/openapi.json` - OpenAPI specification

## Configuration

### Environment Variables

**JWT Configuration:**
- `JWT_SECRET_KEY` - Secret key for JWT signing (required in production)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time (default: 30)

**Rate Limiting:**
- `RATE_LIMIT_REQUESTS` - Default requests per hour (default: 100)
- `RATE_LIMIT_WINDOW` - Default time window in seconds (default: 3600)
- `AUTH_RATE_LIMIT_REQUESTS` - Auth requests limit (default: 10)
- `AUTH_RATE_LIMIT_WINDOW` - Auth time window in seconds (default: 900)

**API Keys:**
- `VALID_API_KEYS` - Comma-separated list of valid API keys

### Production Security

For production deployment:

1. **Set a strong JWT secret:**
   ```bash
   export JWT_SECRET_KEY="your-super-secret-256-bit-key"
   ```

2. **Configure valid API keys:**
   ```bash
   export VALID_API_KEYS="key1,key2,key3"
   ```

3. **Use HTTPS** - All authentication should be over HTTPS
4. **Set appropriate CORS origins** in the application configuration

## Error Handling

### Authentication Errors

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**401 No Authorization:**
```json
{
  "detail": "Authorization required"
}
```

**403 Forbidden (Premium Required):**
```json
{
  "detail": "Premium subscription required for this endpoint"
}
```

### Common Issues

1. **Token Expired:** Request a new token using refresh endpoint or login again
2. **Invalid Token:** Check token format and ensure it's not corrupted
3. **Missing Authorization Header:** Include `Authorization: Bearer <token>`
4. **API Key Not Found:** Verify the API key is in the `VALID_API_KEYS` environment variable

## Implementation Details

### Architecture

The authentication system follows clean architecture principles:

```
src/api/auth/
├── __init__.py          # Package exports
├── config.py            # Configuration settings
├── models.py            # Pydantic models
└── jwt_auth.py          # JWT utilities

src/api/middleware/
└── rate_limiting.py     # Rate limiting middleware

src/api/dependencies/
└── auth.py              # Authentication dependencies

src/api/routes/
└── auth.py              # Authentication endpoints
```

### Dependencies Usage

```python
from api.dependencies.auth import RequireAuth, RequireAuthOrApiKey, RequirePremium

@router.get("/protected")
async def protected_endpoint(user: User = RequireAuth):
    return {"user_id": user.id}

@router.get("/flexible")
async def flexible_endpoint(user: User = RequireAuthOrApiKey):
    return {"authenticated": True}

@router.get("/premium")
async def premium_endpoint(user: User = RequirePremium):
    return {"premium_data": "..."}
```

### Testing

Run authentication tests:
```bash
python -m pytest src/tests/test_auth_security.py -v
```

The test suite covers:
- JWT authentication flow
- Protected endpoint access
- Rate limiting behavior
- API key authentication
- Error scenarios

## Future Enhancements

1. **User Management** - Full user registration and profile management
2. **Role-based Access Control** - Granular permissions system
3. **OAuth2 Providers** - Social login (Google, GitHub, etc.)
4. **API Key Management** - Admin interface for API key creation/revocation
5. **Redis Rate Limiting** - Distributed rate limiting for multiple server instances
6. **Audit Logging** - Track authentication events and access patterns
