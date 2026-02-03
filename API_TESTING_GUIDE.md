# API Testing Guide

Complete guide to test all REST API endpoints of the e-commerce backend.

---

## Quick Start

### 1. Run All Automated Tests
```bash
# Run all tests
docker compose -f docker-compose.dev.yml exec web pytest

# Run with coverage
docker compose -f docker-compose.dev.yml exec web pytest --cov=apps --cov-report=html

# Run specific test file
docker compose -f docker-compose.dev.yml exec web pytest apps/api/tests/test_products.py -v
```

### 2. Manual API Testing Tools

**Option A: HTTPie (Recommended - Human-friendly)**
```bash
# Install HTTPie
pip install httpie

# Test example
http GET http://localhost:8000/api/v1/products/
```

**Option B: cURL (Built-in)**
```bash
curl -X GET http://localhost:8000/api/v1/products/
```

**Option C: Postman/Insomnia**
- Import the collection from `postman_collection.json` (see below to generate)

---

## API Endpoint Testing Checklist

### ✅ Public Endpoints (No Auth Required)

#### Health Check
```bash
# Check system health
http GET http://localhost:8000/api/v1/health/

# Expected: {"status": "healthy", "components": {...}}
```

#### Products API
```bash
# List all products
http GET http://localhost:8000/api/v1/products/

# Get product detail
http GET http://localhost:8000/api/v1/products/cotton-tshirt/

# Featured products
http GET http://localhost:8000/api/v1/products/featured/

# New arrivals
http GET http://localhost:8000/api/v1/products/new/

# Filter products
http GET http://localhost:8000/api/v1/products/ category==clothing price_min==100 price_max==5000

# Search products
http GET http://localhost:8000/api/v1/search/ q==shirt
```

#### Categories API
```bash
# List categories
http GET http://localhost:8000/api/v1/categories/

# Category detail with products
http GET http://localhost:8000/api/v1/categories/clothing/
```

#### Cart API (Guest)
```bash
# Get cart (guest)
http GET http://localhost:8000/api/v1/cart/ X-Cart-Session:guest-12345

# Add item to cart
http POST http://localhost:8000/api/v1/cart/items/ \
  X-Cart-Session:guest-12345 \
  variant_id=1 \
  quantity=2

# Update cart item
http PATCH http://localhost:8000/api/v1/cart/items/1/ \
  X-Cart-Session:guest-12345 \
  quantity=3

# Remove from cart
http DELETE http://localhost:8000/api/v1/cart/items/1/ \
  X-Cart-Session:guest-12345

# Clear cart
http POST http://localhost:8000/api/v1/cart/clear/ \
  X-Cart-Session:guest-12345
```

#### Shipping API
```bash
# List shipping zones
http GET http://localhost:8000/api/v1/shipping/zones/

# Calculate shipping
http POST http://localhost:8000/api/v1/shipping/calculate/ \
  city="Dhaka" \
  area="Gulshan"
```

#### Checkout (Guest)
```bash
# Create order (guest checkout)
http POST http://localhost:8000/api/v1/checkout/ \
  X-Cart-Session:guest-12345 \
  customer_name="John Doe" \
  customer_email="john@example.com" \
  customer_phone="01712345678" \
  shipping_address_line1="123 Main St" \
  shipping_city="Dhaka" \
  shipping_area="Gulshan" \
  payment_method="cod"
```

#### Order Tracking
```bash
# Track order by number and phone
http POST http://localhost:8000/api/v1/orders/track/ \
  order_number="ORD-2026-00001" \
  customer_phone="01712345678"
```

#### Coupons
```bash
# Validate coupon
http POST http://localhost:8000/api/v1/coupons/validate/ \
  code="WELCOME10" \
  cart_total=5000
```

#### CMS API
```bash
# List pages
http GET http://localhost:8000/api/v1/pages/

# Get page content
http GET http://localhost:8000/api/v1/pages/about/

# Get active banners
http GET http://localhost:8000/api/v1/banners/

# Submit contact form
http POST http://localhost:8000/api/v1/contact/ \
  name="John Doe" \
  email="john@example.com" \
  phone="01712345678" \
  subject="Inquiry" \
  message="Hello, I need help"
```

#### Reviews (Public - Read Only)
```bash
# List product reviews
http GET http://localhost:8000/api/v1/reviews/products/1/
```

---

### 🔐 Authenticated Endpoints (Auth Required)

#### Step 1: Register & Login
```bash
# Register new user
http POST http://localhost:8000/api/v1/auth/register/ \
  email="test@example.com" \
  password="SecurePass123!" \
  first_name="Test" \
  last_name="User" \
  phone="01812345678"

# Login (get JWT token)
http POST http://localhost:8000/api/v1/auth/login/ \
  email="test@example.com" \
  password="SecurePass123!"

# Response: 
# {
#   "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
# }

# Save the access token for subsequent requests
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

#### Step 2: Use Token in Requests
```bash
# All authenticated requests need Authorization header
http GET http://localhost:8000/api/v1/users/me/ \
  "Authorization: Bearer $TOKEN"
```

#### User Profile API
```bash
# Get profile
http GET http://localhost:8000/api/v1/users/me/ \
  "Authorization: Bearer $TOKEN"

# Update profile
http PATCH http://localhost:8000/api/v1/users/me/ \
  "Authorization: Bearer $TOKEN" \
  first_name="Updated" \
  phone="01912345678"

# Change password
http POST http://localhost:8000/api/v1/users/me/change-password/ \
  "Authorization: Bearer $TOKEN" \
  old_password="SecurePass123!" \
  new_password="NewSecurePass123!"
```

#### Address Management
```bash
# List addresses
http GET http://localhost:8000/api/v1/users/me/addresses/ \
  "Authorization: Bearer $TOKEN"

# Add address
http POST http://localhost:8000/api/v1/users/me/addresses/ \
  "Authorization: Bearer $TOKEN" \
  label="Home" \
  recipient_name="Test User" \
  phone="01712345678" \
  address_line1="123 Main St" \
  city="Dhaka" \
  area="Gulshan" \
  postal_code="1212" \
  is_default=true

# Update address
http PATCH http://localhost:8000/api/v1/users/me/addresses/1/ \
  "Authorization: Bearer $TOKEN" \
  area="Banani"

# Delete address
http DELETE http://localhost:8000/api/v1/users/me/addresses/1/ \
  "Authorization: Bearer $TOKEN"
```

#### Cart API (Authenticated)
```bash
# User cart (automatically linked to user)
http GET http://localhost:8000/api/v1/cart/ \
  "Authorization: Bearer $TOKEN"

# Add to cart
http POST http://localhost:8000/api/v1/cart/items/ \
  "Authorization: Bearer $TOKEN" \
  variant_id=1 \
  quantity=2
```

#### Order API
```bash
# List my orders
http GET http://localhost:8000/api/v1/orders/ \
  "Authorization: Bearer $TOKEN"

# Get order detail
http GET http://localhost:8000/api/v1/orders/ORD-2026-00001/ \
  "Authorization: Bearer $TOKEN"
```

#### Reviews API
```bash
# Submit review (must have purchased)
http POST http://localhost:8000/api/v1/reviews/ \
  "Authorization: Bearer $TOKEN" \
  product_id=1 \
  rating=5 \
  comment="Great product!"
```

#### Wishlist API
```bash
# Get wishlist
http GET http://localhost:8000/api/v1/wishlist/ \
  "Authorization: Bearer $TOKEN"

# Toggle wishlist item (add/remove)
http POST http://localhost:8000/api/v1/wishlist/toggle/ \
  "Authorization: Bearer $TOKEN" \
  variant_id=1

# Move to cart
http POST http://localhost:8000/api/v1/wishlist/move-to-cart/ \
  "Authorization: Bearer $TOKEN" \
  wishlist_item_id=1
```

#### Password Reset Flow
```bash
# Step 1: Request password reset (sends email)
http POST http://localhost:8000/api/v1/auth/password-reset/ \
  email="test@example.com"

# Step 2: Check email for reset link (token)
# Link format: https://yoursite.com/reset-password?token=xxx

# Step 3: Confirm with token
http POST http://localhost:8000/api/v1/auth/password-reset/confirm/ \
  token="token-from-email" \
  new_password="NewSecurePass123!"
```

#### Token Refresh
```bash
# Refresh access token
http POST http://localhost:8000/api/v1/auth/refresh/ \
  refresh="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Logout (blacklist token)
http POST http://localhost:8000/api/v1/auth/logout/ \
  "Authorization: Bearer $TOKEN"
```

---

## Testing Scenarios

### Scenario 1: Guest Checkout Flow
```bash
# 1. Browse products
http GET http://localhost:8000/api/v1/products/

# 2. Add to cart
SESSION="guest-$(date +%s)"
http POST http://localhost:8000/api/v1/cart/items/ \
  X-Cart-Session:$SESSION \
  variant_id=1 \
  quantity=2

# 3. View cart
http GET http://localhost:8000/api/v1/cart/ \
  X-Cart-Session:$SESSION

# 4. Validate coupon
http POST http://localhost:8000/api/v1/coupons/validate/ \
  code="WELCOME10" \
  cart_total=2500

# 5. Calculate shipping
http POST http://localhost:8000/api/v1/shipping/calculate/ \
  city="Dhaka" \
  area="Gulshan"

# 6. Checkout
http POST http://localhost:8000/api/v1/checkout/ \
  X-Cart-Session:$SESSION \
  customer_name="Guest User" \
  customer_email="guest@example.com" \
  customer_phone="01712345678" \
  shipping_address_line1="123 Main St" \
  shipping_city="Dhaka" \
  shipping_area="Gulshan" \
  payment_method="cod"

# 7. Track order
http POST http://localhost:8000/api/v1/orders/track/ \
  order_number="ORD-2026-00001" \
  customer_phone="01712345678"
```

### Scenario 2: User Registration → Purchase Flow
```bash
# 1. Register
http POST http://localhost:8000/api/v1/auth/register/ \
  email="newuser@example.com" \
  password="SecurePass123!" \
  first_name="New" \
  last_name="User" \
  phone="01812345678"

# 2. Login
TOKEN=$(http POST http://localhost:8000/api/v1/auth/login/ \
  email="newuser@example.com" \
  password="SecurePass123!" \
  | jq -r '.access')

# 3. Add address
http POST http://localhost:8000/api/v1/users/me/addresses/ \
  "Authorization: Bearer $TOKEN" \
  label="Home" \
  recipient_name="New User" \
  phone="01812345678" \
  address_line1="456 Oak Ave" \
  city="Dhaka" \
  area="Dhanmondi" \
  is_default=true

# 4. Add to cart
http POST http://localhost:8000/api/v1/cart/items/ \
  "Authorization: Bearer $TOKEN" \
  variant_id=1 \
  quantity=1

# 5. Checkout
http POST http://localhost:8000/api/v1/checkout/ \
  "Authorization: Bearer $TOKEN" \
  payment_method="bkash"

# 6. View order history
http GET http://localhost:8000/api/v1/orders/ \
  "Authorization: Bearer $TOKEN"

# 7. Submit review
http POST http://localhost:8000/api/v1/reviews/ \
  "Authorization: Bearer $TOKEN" \
  product_id=1 \
  rating=5 \
  comment="Excellent product!"
```

### Scenario 3: Cart Merge on Login
```bash
# 1. Add to cart as guest
SESSION="guest-$(date +%s)"
http POST http://localhost:8000/api/v1/cart/items/ \
  X-Cart-Session:$SESSION \
  variant_id=1 \
  quantity=2

# 2. Login (cart should merge)
http POST http://localhost:8000/api/v1/auth/login/ \
  email="test@example.com" \
  password="SecurePass123!" \
  X-Cart-Session:$SESSION

# 3. Check merged cart
http GET http://localhost:8000/api/v1/cart/ \
  "Authorization: Bearer $TOKEN"
```

---

## Automated Testing

### Run Tests by Category
```bash
# All tests
docker compose -f docker-compose.dev.yml exec web pytest

# API tests only
docker compose -f docker-compose.dev.yml exec web pytest apps/api/tests/ -v

# Product tests
docker compose -f docker-compose.dev.yml exec web pytest apps/api/tests/test_products.py -v

# Cart tests
docker compose -f docker-compose.dev.yml exec web pytest apps/api/tests/test_cart.py -v

# Auth tests
docker compose -f docker-compose.dev.yml exec web pytest apps/api/tests/test_auth.py -v

# With output
docker compose -f docker-compose.dev.yml exec web pytest -s -v

# Stop on first failure
docker compose -f docker-compose.dev.yml exec web pytest -x

# Run specific test
docker compose -f docker-compose.dev.yml exec web pytest apps/api/tests/test_products.py::TestProductList::test_list_products -v
```

### Test Coverage
```bash
# Generate coverage report
docker compose -f docker-compose.dev.yml exec web pytest --cov=apps --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## Load Testing

### Using Apache Bench
```bash
# Test product list endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/api/v1/products/

# Test with POST (checkout)
ab -n 50 -c 5 -p checkout_data.json -T application/json \
  http://localhost:8000/api/v1/checkout/
```

### Using Locust
```bash
# Install Locust
pip install locust

# Create locustfile.py (see below)
# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

---

## Debugging Failed Tests

### View detailed test output
```bash
# Very verbose
docker compose -f docker-compose.dev.yml exec web pytest -vvs

# Show print statements
docker compose -f docker-compose.dev.yml exec web pytest -s

# Show local variables on failure
docker compose -f docker-compose.dev.yml exec web pytest -l

# Drop into debugger on failure
docker compose -f docker-compose.dev.yml exec web pytest --pdb
```

### Check API logs
```bash
# View Django logs
docker compose -f docker-compose.dev.yml logs -f web

# View specific request logs
docker compose -f docker-compose.dev.yml logs web | grep POST
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check token validity, ensure `Authorization: Bearer <token>` header |
| 403 Forbidden | Check user permissions, ensure user owns resource |
| 404 Not Found | Verify endpoint URL, check if resource exists |
| 400 Bad Request | Check request payload, review required fields |
| 500 Server Error | Check Django logs: `docker compose logs web` |
| CSRF Failed | Use `X-CSRFToken` header or disable CSRF for API |
| Token expired | Refresh token using `/api/v1/auth/refresh/` |

---

## Quick Reference

### Base URL
```
http://localhost:8000/api/v1/
```

### Authentication Header
```
Authorization: Bearer <your_access_token>
```

### Guest Cart Header
```
X-Cart-Session: <session_id>
```

### Common HTTP Status Codes
- **200 OK** - Success
- **201 Created** - Resource created
- **204 No Content** - Success, no response body
- **400 Bad Request** - Invalid input
- **401 Unauthorized** - Authentication required
- **403 Forbidden** - Permission denied
- **404 Not Found** - Resource not found
- **500 Server Error** - Internal error

---

**Next Steps:**
1. Start with health check: `http GET http://localhost:8000/api/v1/health/`
2. Test product endpoints (no auth needed)
3. Register a test user
4. Test authenticated endpoints
5. Run automated test suite
6. Check coverage report

Happy Testing! 🚀
