# 🚀 Quick Start: Test Your E-Commerce APIs

## Option 1: Quick Test Script (Recommended)
```bash
# Run automated quick test
./scripts/test_api.sh
```

## Option 2: Manual Testing (HTTPie - Beginner Friendly)

### Install HTTPie
```bash
pip install httpie
```

### Test Basic Endpoints
```bash
# 1. Health check
http GET http://localhost:8000/api/v1/health/

# 2. List products
http GET http://localhost:8000/api/v1/products/

# 3. Get categories
http GET http://localhost:8000/api/v1/categories/

# 4. Register user
http POST http://localhost:8000/api/v1/auth/register/ \
  email="test@example.com" \
  password="SecurePass123!" \
  first_name="Test" \
  last_name="User" \
  phone="01812345678"

# 5. Login (save the token)
http POST http://localhost:8000/api/v1/auth/login/ \
  email="test@example.com" \
  password="SecurePass123!"

# 6. Get profile (use token from login)
http GET http://localhost:8000/api/v1/users/me/ \
  "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Option 3: Using cURL
```bash
# Health check
curl http://localhost:8000/api/v1/health/

# List products
curl http://localhost:8000/api/v1/products/

# Register
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User",
    "phone": "01812345678"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

## Option 4: Run Automated Tests
```bash
# Run all API tests
docker compose -f docker-compose.dev.yml exec web pytest apps/api/tests/ -v

# Run specific test file
docker compose -f docker-compose.dev.yml exec web pytest apps/api/tests/test_products.py -v

# Run with coverage
docker compose -f docker-compose.dev.yml exec web pytest --cov=apps --cov-report=html
```

## Option 5: Postman/Insomnia
1. Import the Postman collection: `postman_collection.json`
2. Set base URL variable: `http://localhost:8000/api/v1`
3. Start testing!

---

## Full API Endpoint List

### Public (No Auth)
- ✅ `GET /health/` - Health check
- ✅ `GET /products/` - List products
- ✅ `GET /products/{slug}/` - Product detail
- ✅ `GET /products/featured/` - Featured products
- ✅ `GET /products/new/` - New arrivals
- ✅ `GET /categories/` - Categories
- ✅ `GET /search/` - Search products
- ✅ `GET /cart/` - Get cart (guest)
- ✅ `POST /cart/items/` - Add to cart
- ✅ `POST /checkout/` - Create order
- ✅ `GET /shipping/zones/` - Shipping zones
- ✅ `GET /pages/` - CMS pages
- ✅ `GET /banners/` - Banners
- ✅ `POST /contact/` - Contact form

### Authenticated (Requires Token)
- 🔐 `POST /auth/register/` - Register
- 🔐 `POST /auth/login/` - Login
- 🔐 `POST /auth/logout/` - Logout
- 🔐 `POST /auth/refresh/` - Refresh token
- 🔐 `GET /users/me/` - Get profile
- 🔐 `PATCH /users/me/` - Update profile
- 🔐 `GET /users/me/addresses/` - List addresses
- 🔐 `POST /users/me/addresses/` - Add address
- 🔐 `GET /orders/` - My orders
- 🔐 `POST /reviews/` - Submit review
- 🔐 `GET /wishlist/` - Get wishlist
- 🔐 `POST /wishlist/toggle/` - Add/remove wishlist

---

## Testing Checklist

### ✅ What to Test

#### 1. Products
- [ ] List all products
- [ ] Filter by category
- [ ] Filter by price range
- [ ] Search products
- [ ] Get product detail
- [ ] Featured products
- [ ] New arrivals

#### 2. Cart
- [ ] Add item (guest)
- [ ] Add item (user)
- [ ] Update quantity
- [ ] Remove item
- [ ] Clear cart
- [ ] Cart merge on login

#### 3. Checkout
- [ ] Guest checkout
- [ ] User checkout
- [ ] Apply coupon
- [ ] Calculate shipping
- [ ] Validate stock

#### 4. Auth
- [ ] Register
- [ ] Login
- [ ] Logout
- [ ] Refresh token
- [ ] Password reset

#### 5. User Profile
- [ ] Get profile
- [ ] Update profile
- [ ] Change password
- [ ] Add address
- [ ] Update address
- [ ] Delete address

#### 6. Orders
- [ ] List orders
- [ ] Get order detail
- [ ] Track order

#### 7. Engagement
- [ ] Submit review
- [ ] Get reviews
- [ ] Add to wishlist
- [ ] View wishlist
- [ ] Move to cart

---

## Troubleshooting

### API not responding?
```bash
# Check if server is running
docker compose -f docker-compose.dev.yml ps

# View logs
docker compose -f docker-compose.dev.yml logs -f web
```

### Getting 401 errors?
- Make sure you include the Authorization header
- Token format: `Authorization: Bearer <your_token>`
- Token might be expired - login again

### Getting 404 errors?
- Check the URL path
- Make sure you're using `/api/v1/` prefix

### Getting 500 errors?
```bash
# Check Django logs
docker compose -f docker-compose.dev.yml logs web | tail -50
```

---

## Next Steps

1. ✅ Test health endpoint
2. ✅ Test product endpoints
3. ✅ Register a test user
4. ✅ Test authenticated endpoints
5. ✅ Run automated tests
6. ✅ Check test coverage

**For complete testing guide:** See [API_TESTING_GUIDE.md](API_TESTING_GUIDE.md)

Happy Testing! 🎉
