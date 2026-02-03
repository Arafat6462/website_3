#!/bin/bash

###############################################################################
# Health Check Test Script
#
# Tests the enhanced health check endpoint to verify database, cache,
# and storage connectivity checks.
#
# Usage: bash scripts/test_health_check.sh
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Testing Enhanced Health Check Endpoint...${NC}\n"

# Test health check endpoint
echo "Making request to /api/v1/health/..."

RESPONSE=$(curl -s http://localhost:8000/api/v1/health/ 2>/dev/null || echo "{\"error\": \"Server not running\"}")

echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

# Check if response contains expected fields
if echo "$RESPONSE" | grep -q "\"status\""; then
    echo -e "\n${GREEN}✓ Health check endpoint is working${NC}"
    
    if echo "$RESPONSE" | grep -q "\"checks\""; then
        echo -e "${GREEN}✓ Component checks included${NC}"
        
        if echo "$RESPONSE" | grep -q "\"database\""; then
            echo -e "${GREEN}✓ Database check present${NC}"
        fi
        
        if echo "$RESPONSE" | grep -q "\"cache\""; then
            echo -e "${GREEN}✓ Cache check present${NC}"
        fi
        
        if echo "$RESPONSE" | grep -q "\"storage\""; then
            echo -e "${GREEN}✓ Storage check present${NC}"
        fi
    fi
else
    echo -e "\n${RED}✗ Health check endpoint not responding correctly${NC}"
    echo -e "${YELLOW}Note: Ensure the development server is running:${NC}"
    echo -e "  cd src && python manage.py runserver"
fi

echo -e "\n${YELLOW}Expected Response Structure:${NC}"
cat << 'EOF'
{
    "status": "healthy",
    "version": "1.0",
    "api": "v1",
    "timestamp": 1234567890.123,
    "checks": {
        "database": {
            "status": "healthy",
            "message": "Database connection successful"
        },
        "cache": {
            "status": "healthy",
            "message": "Cache connection successful"
        },
        "storage": {
            "status": "healthy",
            "message": "Storage accessible"
        }
    }
}
EOF

echo ""
