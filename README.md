# API Gateway - FastAPI + SQLModel + SQLite

Production-ready API Gateway managing external partner access to internal services with authentication, rate limiting, and audit logging.

## Features

- **API Key Authentication** - SHA-256 hashed keys for secure partner identification
- **Rate Limiting** - Database-backed sliding window rate limiting per partner
- **Service-Level Access Control** - Fine-grained permissions for backend services
- **Request Logging** - Complete audit trail with analytics
- **Auto-generated API Docs** - Interactive Swagger UI at `/docs`
- **Async HTTP Proxying** - High-performance request forwarding

## Quick Start

### 1. Setup Environment
```bash
cd /Users/adityadubey/Desktop/partner-api-gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Seed Database
```bash
python -m app.seed_data
```

### 3. Start Server
```bash
uvicorn app.main:app --port 8080 --reload
```

**Server**: http://localhost:8080  
**API Docs**: http://localhost:8080/docs

## Demo API Keys

```bash
# Premium Partner (all services, 100 req/min)
curl -H "X-API-Key: premium-api-key-12345" http://localhost:8080/users

# Basic Partner (users & posts, 30 req/min)
curl -H "X-API-Key: basic-api-key-67890" http://localhost:8080/posts/1

# Todo App (todos only, 50 req/min)
curl -H "X-API-Key: todo-api-key-11111" http://localhost:8080/todos
```

## Test Scenarios - Pass & Fail Cases

### ✅ Scenario 1: Valid API Key with Allowed Service (PASS)
```bash
# Premium Partner accessing users service
curl -H "X-API-Key: premium-api-key-12345" http://localhost:8080/users/1

# Response: 200 OK
{
  "id": 1,
  "name": "Leanne Graham",
  "username": "Bret",
  "email": "Sincere@april.biz",
  ...
}
```

### ❌ Scenario 2: No API Key (FAIL - 401 Unauthorized)
```bash
# Trying to access without API key
curl http://localhost:8080/users/1

# Response: 401 Unauthorized
{
  "detail": {
    "error": "Unauthorized",
    "message": "API key is required. Provide via 'X-API-Key' header or 'Authorization: Bearer <key>'"
  }
}
```

### ❌ Scenario 3: Invalid API Key (FAIL - 401 Unauthorized)
```bash
# Using invalid/wrong API key
curl -H "X-API-Key: invalid-key-xyz" http://localhost:8080/users/1

# Response: 401 Unauthorized
{
  "detail": {
    "error": "Unauthorized",
    "message": "Invalid API key"
  }
}
```

### ❌ Scenario 4: Valid Key but Service Not Allowed (FAIL - 403 Forbidden)
```bash
# Basic Partner (only has users & posts) trying to access todos
curl -H "X-API-Key: basic-api-key-67890" http://localhost:8080/todos/1

# Response: 403 Forbidden
{
  "detail": {
    "error": "Forbidden",
    "message": "Your API key does not have access to the 'todos' service",
    "allowed_services": ["users", "posts"]
  }
}
```

### ✅ Scenario 5: Valid Key with Correct Service (PASS)
```bash
# Todo Partner accessing todos service
curl -H "X-API-Key: todo-api-key-11111" http://localhost:8080/todos/1

# Response: 200 OK
{
  "userId": 1,
  "id": 1,
  "title": "delectus aut autem",
  "completed": false
}
```

### ❌ Scenario 6: Rate Limit Exceeded (FAIL - 429 Too Many Requests)
```bash
# Make more requests than rate limit allows
# Example: Basic Partner has 30 req/min limit

# After 30 requests within a minute:
curl -H "X-API-Key: basic-api-key-67890" http://localhost:8080/users/1

# Response: 429 Too Many Requests
{
  "detail": {
    "error": "Too Many Requests",
    "message": "Rate limit exceeded. Limit: 30 requests per 60 seconds",
    "retry_after": 42
  }
}
# Headers include:
# X-RateLimit-Limit: 30
# X-RateLimit-Remaining: 0
# X-RateLimit-Reset: 1735476320
# Retry-After: 42
```

### ✅ Scenario 7: Create New Partner via Admin (PASS)
```bash
# Create partner with users and posts access
curl -X POST http://localhost:8080/admin/partners \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NewCompany",
    "service_ids": [1, 2],
    "rate_limit": 50
  }'

# Response: 201 Created
{
  "id": 4,
  "name": "NewCompany",
  "allowed_services": ["users", "posts"],
  "rate_limit": 50,
  "is_active": true,
  "api_key": "ak_XrNycAwJTDu6GdXbPIISDZuwQHL4JHoOOr-sCPchqIE",
  "created_at": "2025-12-29T12:00:00",
  "updated_at": "2025-12-29T12:00:00"
}
# ⚠️ Save the api_key - it's only shown once!
```

### ✅ Scenario 8: POST Request Through Gateway (PASS)
```bash
# Premium Partner creating a post
curl -X POST http://localhost:8080/posts \
  -H "X-API-Key: premium-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My New Post",
    "body": "Post content here",
    "userId": 1
  }'

# Response: 201 Created
{
  "id": 101,
  "title": "My New Post",
  "body": "Post content here",
  "userId": 1
}
```

### 📊 Scenario 9: View Analytics (Admin)
```bash
curl http://localhost:8080/admin/analytics

# Response: 200 OK
{
  "period_hours": 24,
  "total_requests": 156,
  "total_errors": 12,
  "error_rate": 7.7,
  "average_response_time_ms": 245.8,
  "requests_by_partner": {
    "1": 89,
    "2": 45,
    "3": 22
  },
  "top_endpoints": [
    {"path": "/users/1", "count": 45},
    {"path": "/posts", "count": 32}
  ],
  "status_distribution": {
    "200": 120,
    "403": 8,
    "429": 4
  }
}
```

## Service IDs for Partner Creation

When creating partners, use these service IDs:

- `1` - users
- `2` - posts
- `3` - comments
- `4` - todos
- `5` - albums
- `6` - photos

**Example:** `"service_ids": [1, 2, 4]` grants access to users, posts, and todos.

## Admin Endpoints

```bash
# List all partners
curl http://localhost:8080/admin/partners | python3 -m json.tool

# Create new partner
curl -X POST http://localhost:8080/admin/partners \
  -H "Content-Type: application/json" \
  -d '{"name": "New Partner", "allowed_services": ["users"], "rate_limit": 50}'

# Get analytics
curl http://localhost:8080/admin/analytics | python3 -m json.tool

# View request logs
curl http://localhost:8080/admin/logs?limit=10 | python3 -m json.tool
```

## Architecture

- **FastAPI** - Modern async web framework
- **SQLModel** - Type-safe ORM (SQLAlchemy + Pydantic)
- **SQLite** - Persistent database (`api_gateway.db`)
- **httpx** - Async HTTP client for proxying

## Architectural Considerations

### Current Implementation: Database-Backed Authentication

**Request Flow:**
1. Extract API key from headers
2. Database lookup: Partner + permissions + rate limit (2-3 queries)
3. Proxy to backend service
4. Log to audit table

*Limitations:*
- Database I/O overhead: 2-3 queries per request
- Latency: 30-50ms per request
- Throughput: ~500 req/sec (single instance)
- Scaling bottleneck at high traffic


## Project Structure

```
app/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── database.py          # SQLModel database setup
├── seed_data.py         # Demo data seeding
├── models/              # Database models
│   ├── partner.py       # Partner model
│   ├── service.py       # Service model
│   ├── permission.py    # Partner-Service permissions
│   ├── rate_limit.py    # Rate limit tracking
│   └── audit.py         # Request logging
├── services/            # Business logic layer
└── api/
    ├── deps.py          # Authentication & rate limit dependencies
    └── routes/          # API endpoints
```

## Database Models

### Partner
Represents API partners/clients with secure authentication.

**Fields:**
- `id` - Primary key
- `name` - Partner name (indexed)
- `api_key_hash` - SHA-256 hashed API key (unique, indexed)
- `rate_limit` - Requests per minute (default: 60)
- `is_active` - Partner status
- `created_at` / `updated_at` - Timestamps

**Methods:**
- `hash_api_key(api_key)` - Generate SHA-256 hash
- `generate_api_key()` - Create new secure API key
- `verify_api_key(api_key)` - Validate API key

### Service
Represents backend services that partners can access.

**Fields:**
- `id` - Primary key
- `name` - Unique service identifier (indexed)
- `display_name` - Human-readable name
- `description` - Service description
- `base_url` - Backend service URL
- `is_active` - Service availability status
- `created_at` / `updated_at` - Timestamps

### PartnerServicePermission
Junction table managing many-to-many relationship between partners and services.

**Fields:**
- `id` - Primary key
- `partner_id` - Foreign key to Partner
- `service_id` - Foreign key to Service
- `granted_at` - Permission grant timestamp

### RateLimitEntry
Tracks individual request timestamps for sliding window rate limiting.

**Fields:**
- `id` - Primary key
- `partner_id` - Foreign key to Partner (indexed)
- `timestamp` - Request timestamp (indexed)

### RequestLog
Complete audit trail of all API requests.

**Fields:**
- `id` - Primary key
- `partner_id` - Foreign key to Partner (indexed)
- `method` - HTTP method (GET, POST, etc.)
- `path` - Request path (indexed)
- `status_code` - HTTP response code
- `response_time_ms` - Request duration
- `ip_address` - Client IP
- `user_agent` - Client user agent
- `timestamp` - Request timestamp (indexed)
