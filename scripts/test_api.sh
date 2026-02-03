#!/bin/bash
# Quick API Test Script
# Usage: ./scripts/test_api.sh

set -e

BASE_URL="http://localhost:8000/api/v1"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}   E-Commerce API Quick Test      ${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    
    echo -n "Testing: $description... "
    
    if curl -s -X $method "$BASE_URL$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

# Test counters
PASSED=0
FAILED=0

# Health Check
echo -e "\n${BLUE}[1/10] Health Check${NC}"
if test_endpoint "GET" "/health/" "System health"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Products API
echo -e "\n${BLUE}[2/10] Products API${NC}"
if test_endpoint "GET" "/products/" "List products"; then
    ((PASSED++))
else
    ((FAILED++))
fi

if test_endpoint "GET" "/products/featured/" "Featured products"; then
    ((PASSED++))
else
    ((FAILED++))
fi

if test_endpoint "GET" "/products/new/" "New arrivals"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Categories API
echo -e "\n${BLUE}[3/10] Categories API${NC}"
if test_endpoint "GET" "/categories/" "List categories"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Cart API
echo -e "\n${BLUE}[4/10] Cart API${NC}"
SESSION="test-$(date +%s)"
if curl -s -X GET "$BASE_URL/cart/" -H "X-Cart-Session: $SESSION" > /dev/null 2>&1; then
    echo -e "Testing: Get cart (guest)... ${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "Testing: Get cart (guest)... ${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Shipping API
echo -e "\n${BLUE}[5/10] Shipping API${NC}"
if test_endpoint "GET" "/shipping/zones/" "List shipping zones"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# CMS API
echo -e "\n${BLUE}[6/10] CMS API${NC}"
if test_endpoint "GET" "/pages/" "List pages"; then
    ((PASSED++))
else
    ((FAILED++))
fi

if test_endpoint "GET" "/banners/" "Get banners"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Auth API
echo -e "\n${BLUE}[7/10] Auth API (Registration)${NC}"
RANDOM_EMAIL="test$(date +%s)@example.com"
REGISTER_DATA=$(cat <<EOF
{
  "email": "$RANDOM_EMAIL",
  "password": "SecurePass123!",
  "first_name": "Test",
  "last_name": "User",
  "phone": "01812345678"
}
EOF
)

if curl -s -X POST "$BASE_URL/auth/register/" \
    -H "Content-Type: application/json" \
    -d "$REGISTER_DATA" > /dev/null 2>&1; then
    echo -e "Testing: User registration... ${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "Testing: User registration... ${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Login & Get Token
echo -e "\n${BLUE}[8/10] Auth API (Login)${NC}"
LOGIN_DATA=$(cat <<EOF
{
  "email": "$RANDOM_EMAIL",
  "password": "SecurePass123!"
}
EOF
)

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login/" \
    -H "Content-Type: application/json" \
    -d "$LOGIN_DATA")

if echo "$LOGIN_RESPONSE" | grep -q "access"; then
    echo -e "Testing: User login... ${GREEN}✓ PASS${NC}"
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
    ((PASSED++))
else
    echo -e "Testing: User login... ${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Authenticated Endpoints
if [ ! -z "$TOKEN" ]; then
    echo -e "\n${BLUE}[9/10] User Profile API${NC}"
    if curl -s -X GET "$BASE_URL/users/me/" \
        -H "Authorization: Bearer $TOKEN" > /dev/null 2>&1; then
        echo -e "Testing: Get user profile... ${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "Testing: Get user profile... ${RED}✗ FAIL${NC}"
        ((FAILED++))
    fi
    
    echo -e "\n${BLUE}[10/10] Wishlist API${NC}"
    if curl -s -X GET "$BASE_URL/wishlist/" \
        -H "Authorization: Bearer $TOKEN" > /dev/null 2>&1; then
        echo -e "Testing: Get wishlist... ${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "Testing: Get wishlist... ${RED}✗ FAIL${NC}"
        ((FAILED++))
    fi
else
    echo -e "\n${BLUE}[9/10] User Profile API${NC}"
    echo -e "Testing: Get user profile... ${RED}✗ SKIP (No token)${NC}"
    ((FAILED++))
    
    echo -e "\n${BLUE}[10/10] Wishlist API${NC}"
    echo -e "Testing: Get wishlist... ${RED}✗ SKIP (No token)${NC}"
    ((FAILED++))
fi

# Summary
echo ""
echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}         Test Summary             ${NC}"
echo -e "${BLUE}==================================${NC}"
TOTAL=$((PASSED + FAILED))
echo -e "Total Tests:  $TOTAL"
echo -e "${GREEN}Passed:       $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed:       $FAILED${NC}"
else
    echo -e "Failed:       $FAILED"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Check logs for details.${NC}"
    echo "View logs: docker compose -f docker-compose.dev.yml logs web"
    exit 1
fi
