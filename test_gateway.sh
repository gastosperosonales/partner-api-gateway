#!/bin/bash
# =============================================================================
# API Gateway Test Script - Core Functionality
# =============================================================================

GATEWAY_URL="http://localhost:8080"
PREMIUM_KEY="premium-api-key-12345"
BASIC_KEY="basic-api-key-67890"
TODO_KEY="todo-api-key-11111"

echo "=============================================="
echo "API Gateway Test Suite"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
echo "1. Health Check"
echo "---------------------------------------------"
curl -s "$GATEWAY_URL/health" | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "2. Gateway Info"
echo "---------------------------------------------"
curl -s "$GATEWAY_URL/" | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "3. Test WITHOUT API Key (Should Fail - 401)"
echo "---------------------------------------------"
curl -s -w "\nHTTP Status: %{http_code}\n" "$GATEWAY_URL/users/1" 2>&1 | tail -5
echo ""

# -----------------------------------------------------------------------------
echo "4. Test WITH Invalid API Key (Should Fail - 401)"
echo "---------------------------------------------"
curl -s -H "X-API-Key: invalid-key" "$GATEWAY_URL/users/1" | python3 -m json.tool 2>&1 | head -10
echo ""

# -----------------------------------------------------------------------------
echo "5. Premium Partner - Get Users (Should Work)"
echo "---------------------------------------------"
curl -s -H "X-API-Key: $PREMIUM_KEY" "$GATEWAY_URL/users/1" | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "6. Premium Partner - Get Posts (Should Work)"
echo "---------------------------------------------"
curl -s -H "X-API-Key: $PREMIUM_KEY" "$GATEWAY_URL/posts/1" | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "7. Basic Partner - Get Users (Should Work)"
echo "---------------------------------------------"
curl -s -H "X-API-Key: $BASIC_KEY" "$GATEWAY_URL/users/1" | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "8. Basic Partner - Access Control Test (Should FAIL - 403)"
echo "---------------------------------------------"
curl -s -H "X-API-Key: $BASIC_KEY" "$GATEWAY_URL/todos/1" | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "9. Todo Partner - Get Todos (Should Work)"
echo "---------------------------------------------"
curl -s -H "X-API-Key: $TODO_KEY" "$GATEWAY_URL/todos/1" | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "10. Todo Partner - Access Control Test (Should FAIL - 403)"
echo "---------------------------------------------"
curl -s -H "X-API-Key: $TODO_KEY" "$GATEWAY_URL/users/1" | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "11. Create a Post via Gateway"
echo "---------------------------------------------"
curl -s -X POST \
  -H "X-API-Key: $PREMIUM_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Post", "body": "Created via API Gateway", "userId": 1}' \
  "$GATEWAY_URL/posts" | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "12. View Analytics"
echo "---------------------------------------------"
curl -s "$GATEWAY_URL/admin/analytics" | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "13. View All Partners"
echo "---------------------------------------------"
curl -s "$GATEWAY_URL/admin/partners" | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "14. Create New Partner"
echo "---------------------------------------------"
curl -s -X POST "$GATEWAY_URL/admin/partners" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Partner", "allowed_services": ["users", "posts"], "rate_limit": 10}' \
  | python3 -m json.tool
echo ""

# -----------------------------------------------------------------------------
echo "15. Rate Limiting Test"
echo "---------------------------------------------"
echo "Making 12 requests with Test Partner (limit: 10/min)..."
echo "Extracting API key from previous response..."

TEST_KEY=$(curl -s -X POST "$GATEWAY_URL/admin/partners" \
  -H "Content-Type: application/json" \
  -d '{"name": "Rate Test Partner", "allowed_services": ["users"], "rate_limit": 10}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['api_key'])")

echo "Testing rate limit with key: $TEST_KEY"
for i in {1..12}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "X-API-Key: $TEST_KEY" \
    "$GATEWAY_URL/users/1")
  if [ "$STATUS" == "429" ]; then
    echo "Request $i: HTTP $STATUS - Rate Limited! ✓"
  else
    echo "Request $i: HTTP $STATUS"
  fi
done
echo ""

# -----------------------------------------------------------------------------
echo "16. View Request Logs"
echo "---------------------------------------------"
curl -s "$GATEWAY_URL/admin/logs?limit=5" | python3 -m json.tool
echo ""

echo "=============================================="
echo "Test Suite Complete!"
echo "API Documentation: http://localhost:8080/docs"
echo "=============================================="
