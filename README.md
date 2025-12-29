# API Gateway - FastAPI + SQLModel + SQLite

API Gateway managing external partner access to internal services with authentication, rate limiting, and audit logging.

## Features

- **JWT Token Authentication** - Two-step auth: API key → JWT token → API requests
- **API Key Management** - SHA-256 hashed keys for secure partner identification
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
uvicorn app.main:app --reload
```

**Server**: http://localhost:8000 (default port, configurable via config)  
**API Docs**: http://localhost:8000/docs

## Getting an API Key

To use the API Gateway, you need an API key. API keys are obtained by creating a new partner through the admin endpoint.

### Create a New Partner (Get API Key)

```bash
# Create a new partner and receive your API key
curl -X POST http://localhost:8000/admin/partners \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Company",
    "service_ids": [1, 2, 3],
    "rate_limit": 100
  }'

# Response: 200 OK
{
  "id": 1,
  "name": "My Company",
  "allowed_services": ["users", "posts", "comments"],
  "rate_limit": 100,
  "is_active": true,
  "api_key": "ak_XrNycAwJTDu6GdXbPIISDZuwQHL4JHoOOr-sCPchqIE",
  "created_at": "2025-01-29T12:00:00",
  "updated_at": "2025-01-29T12:00:00"
}
```

⚠️ **Important**: The `api_key` is only returned once when the partner is created. **Save it securely** - you won't be able to retrieve it again!

### Service IDs Reference

When creating a partner, specify which services they can access using service IDs:

- `1` - users
- `2` - posts
- `3` - comments
- `4` - todos
- `5` - albums
- `6` - photos

**Example**: `"service_ids": [1, 2, 4]` grants access to users, posts, and todos.

## Authentication Flow

The API Gateway uses a two-step authentication process:

1. **Exchange API Key for JWT Token** - Use your API key to get a JWT access token
2. **Use JWT Token for Requests** - Include the token in the `Authorization: Bearer <token>` header

### Quick Example

```bash
# 1. Get JWT token from API key
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your-api-key-here"}' | jq -r '.access_token')

# 2. Use token for API requests
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/users/1
```

### Step 1: Get JWT Token

```bash
# Exchange API key for JWT token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "premium-api-key-12345"}'

# Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "partner_id": 1,
  "partner_name": "Premium Partner",
  "allowed_services": ["users", "posts", "comments", "todos", "albums", "photos"],
  "rate_limit": 100
}
```

### Step 2: Use JWT Token for API Requests

```bash
# Store the token in a variable (replace with your actual token)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Premium Partner (all services, 100 req/min)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/users/1

# Basic Partner (users & posts, 30 req/min)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/posts/1

# Todo App (todos only, 50 req/min)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/todos/1
```

## Test Scenarios - Pass & Fail Cases

### ✅ Scenario 1: Valid API Key with Allowed Service (PASS)
```bash
# Step 1: Get JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "premium-api-key-12345"}' | jq -r '.access_token')

# Step 2: Use token to access users service
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/users/1

# Response: 200 OK
{
  "id": 1,
  "name": "Leanne Graham",
  "username": "Bret",
  "email": "Sincere@april.biz",
  ...
}
```

### ❌ Scenario 2: No Token (FAIL - 401 Unauthorized)
```bash
# Trying to access without JWT token
curl http://localhost:8000/users/1

# Response: 401 Unauthorized
{
  "detail": {
    "error": "Unauthorized",
    "message": "Could not validate credentials"
  }
}
```

### ❌ Scenario 3: Invalid API Key (FAIL - 401 Unauthorized)
```bash
# Using invalid/wrong API key to get token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "invalid-key-xyz"}'

# Response: 401 Unauthorized
{
  "detail": {
    "error": "Unauthorized",
    "message": "Invalid API key"
  }
}
```

### ❌ Scenario 4: Valid Token but Service Not Allowed (FAIL - 403 Forbidden)
```bash
# Step 1: Get token for Basic Partner (only has users & posts)
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "basic-api-key-67890"}' | jq -r '.access_token')

# Step 2: Try to access todos service (not allowed)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/todos/1

# Response: 403 Forbidden
{
  "detail": {
    "error": "Forbidden",
    "message": "Your API key does not have access to the 'todos' service",
    "allowed_services": ["users", "posts"]
  }
}
```

### ✅ Scenario 5: Valid Token with Correct Service (PASS)
```bash
# Step 1: Get token for Todo Partner
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "todo-api-key-11111"}' | jq -r '.access_token')

# Step 2: Access todos service
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/todos/1

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
# Step 1: Get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "basic-api-key-67890"}' | jq -r '.access_token')

# Step 2: Make more requests than rate limit allows
# Example: Basic Partner has 30 req/min limit

# After 30 requests within a minute:
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/users/1

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

### ✅ Scenario 7: Create New Partner via Admin (Get API Key)
```bash
# Create partner with users and posts access
# This is how you get your API key!
curl -X POST http://localhost:8000/admin/partners \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NewCompany",
    "service_ids": [1, 2],
    "rate_limit": 50
  }'

# Response: 200 OK
{
  "id": 4,
  "name": "NewCompany",
  "allowed_services": ["users", "posts"],
  "rate_limit": 50,
  "is_active": true,
  "api_key": "ak_XrNycAwJTDu6GdXbPIISDZuwQHL4JHoOOr-sCPchqIE",
  "created_at": "2025-01-29T12:00:00",
  "updated_at": "2025-01-29T12:00:00"
}
# ⚠️ Save the api_key - it's only shown once!
# Use this API key to get JWT tokens via /auth/token
```

### ✅ Scenario 8: POST Request Through Gateway (PASS)
```bash
# Step 1: Get JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "premium-api-key-12345"}' | jq -r '.access_token')

# Step 2: Premium Partner creating a post
curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer $TOKEN" \
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
curl http://localhost:8000/admin/analytics

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


## Admin Endpoints

```bash
# List all partners
curl http://localhost:8000/admin/partners | python3 -m json.tool

# Create new partner
curl -X POST http://localhost:8000/admin/partners \
  -H "Content-Type: application/json" \
  -d '{"name": "New Partner", "allowed_services": ["users"], "rate_limit": 50}'

# Get analytics
curl http://localhost:8000/admin/analytics | python3 -m json.tool

# View request logs
curl http://localhost:8000/admin/logs?limit=10 | python3 -m json.tool
```

## Architecture

- **FastAPI** - Modern async web framework
- **SQLModel** - Type-safe ORM (SQLAlchemy + Pydantic)
- **SQLite** - Persistent database (`api_gateway.db`)
- **httpx** - Async HTTP client for proxying

## Architectural Considerations

### Current Implementation: JWT Token Authentication

**Request Flow:**
1. **Token Exchange**: Client exchanges API key for JWT token via `/auth/token`
   - Database lookup: Partner + permissions + rate limit (2-3 queries)
   - JWT token contains partner metadata (ID, services, rate limit)
2. **API Requests**: Client uses JWT token in `Authorization: Bearer <token>` header
   - JWT validation (no database lookup needed)
   - Rate limit check (1 query)
   - Proxy to backend service
   - Log to audit table

*Benefits:*
- JWT tokens reduce database lookups for each request
- Token contains partner metadata (faster validation)
- Tokens expire after 1 hour (configurable)
- Better scalability than per-request API key lookups

*Limitations:*
- Still requires database for rate limiting and logging
- Token refresh needed after expiration
- Throughput: ~1000 req/sec (single instance)


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
