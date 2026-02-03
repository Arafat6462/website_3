# 📋 E-Commerce Backend - One-Page Cheat Sheet

## 🌐 URLS TO REMEMBER
```
Admin:   http://localhost:8000/admin/
API:     http://localhost:8000/api/v1/
Swagger: http://localhost:8000/api/v1/docs/
Health:  http://localhost:8000/api/v1/health/
```

## 🔐 DEFAULT CREDENTIALS
```
Admin:    admin@example.com / admin123
DB:       ecom_user / ecom_password
Port:     PostgreSQL=5432, Redis=6379
```

## 🚀 ESSENTIAL COMMANDS

### Start/Stop
```bash
# Start all services
docker compose -f docker-compose.dev.yml up -d

# Stop all services
docker compose -f docker-compose.dev.yml down

# View logs
docker compose -f docker-compose.dev.yml logs -f web
```

### Django Management
```bash
# Base command
docker compose -f docker-compose.dev.yml exec web python manage.py

# Common tasks
... migrate                 # Apply migrations
... makemigrations         # Create migrations
... createsuperuser        # Create admin user
... shell                  # Django shell
... dbshell                # PostgreSQL shell
... collectstatic          # Gather static files
```

### Testing
```bash
# Quick test
./scripts/test_api.sh

# All tests
docker compose -f docker-compose.dev.yml exec web pytest

# With coverage
docker compose -f docker-compose.dev.yml exec web pytest --cov=apps
```

## 📦 WHAT YOU CAN MANAGE

### In Admin Panel (http://localhost:8000/admin/)
```
📦 Catalog
   └─ Products, Categories, Product Types, Attributes

🛒 Sales
   └─ Orders, Carts, Coupons, Shipping Zones

📄 Content
   └─ Pages, Banners, Contact Forms

👥 Customers
   └─ Users, Addresses

🎭 Engagement
   └─ Reviews, Wishlists
```

## 🔌 API ENDPOINTS

### Public (No Auth)
```
GET  /products/              List products
GET  /products/{slug}/       Product detail
GET  /categories/            Categories
GET  /cart/                  Get cart (guest)
POST /cart/items/            Add to cart
POST /checkout/              Create order
GET  /shipping/zones/        Shipping zones
POST /orders/track/          Track order
```

### Authenticated (Bearer Token)
```
POST /auth/register/         Register
POST /auth/login/            Login
GET  /users/me/              Profile
GET  /orders/                My orders
POST /reviews/               Submit review
GET  /wishlist/              My wishlist
```

## 🧪 QUICK TESTS

### Test API (HTTPie)
```bash
# Install
pip install httpie

# Test
http GET http://localhost:8000/api/v1/products/
http POST http://localhost:8000/api/v1/auth/login/ email=test@example.com password=pass
```

### Test API (cURL)
```bash
curl http://localhost:8000/api/v1/health/
curl http://localhost:8000/api/v1/products/
```

### Test API (Swagger)
```
1. Open: http://localhost:8000/api/v1/docs/
2. Click endpoint → Try it out → Execute
```

## 🗃️ DATABASE

### Access DB
```bash
# Django shell
docker compose -f docker-compose.dev.yml exec web python manage.py dbshell

# Direct PostgreSQL
docker compose -f docker-compose.dev.yml exec db psql -U ecom_user -d ecom_db
```

### Quick Queries
```sql
-- Count products
SELECT COUNT(*) FROM products_product;

-- Today's orders
SELECT * FROM orders_order WHERE created_at::date = CURRENT_DATE;

-- Active coupons
SELECT * FROM promotions_coupon WHERE is_active = true;
```

## 🔧 TROUBLESHOOTING

### Service not running?
```bash
docker compose -f docker-compose.dev.yml ps
docker compose -f docker-compose.dev.yml up -d
```

### Check logs
```bash
docker compose -f docker-compose.dev.yml logs -f web
```

### Reset database (⚠️ DANGER)
```bash
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

### Port conflict
```bash
docker compose -f docker-compose.dev.yml down
lsof -ti:8000 | xargs kill -9
docker compose -f docker-compose.dev.yml up -d
```

## 📁 KEY FILES

```
src/
├── apps/             # Django apps
│   ├── products/     # Product management
│   ├── orders/       # Cart & orders
│   ├── users/        # Authentication
│   └── ...
├── api/v1/          # API endpoints
├── config/          # Settings & URLs
└── manage.py        # Django CLI

Root:
├── docker-compose.dev.yml    # Docker setup
├── requirements/             # Dependencies
├── scripts/                  # Utility scripts
├── SYSTEM_REFERENCE.md       # Complete guide
└── README.md                 # Overview
```

## 📚 DOCUMENTATION

| File | What's Inside |
|------|---------------|
| **SYSTEM_REFERENCE.md** | Complete system guide |
| **API_TESTING_GUIDE.md** | Full API documentation |
| **QUICK_TEST.md** | Quick start guide |
| **SWAGGER_GUIDE.md** | Swagger usage |
| **DEPLOYMENT.md** | Production deployment |
| **.github/copilot-instructions.md** | AI build instructions |

## 🎯 COMMON TASKS

### Add Product (Admin)
```
Admin → Catalog → Products → Add Product
→ Fill details → Save → Upload images
```

### Process Order (Admin)
```
Admin → Sales → Orders → Select order
→ Actions → Confirm → Shipped
```

### Register User (API)
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass","first_name":"User","last_name":"Name","phone":"01812345678"}'
```

### Test with Token (API)
```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}' | jq -r '.access')

# 2. Use token
curl http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer $TOKEN"
```

---

**For complete details:** See [SYSTEM_REFERENCE.md](SYSTEM_REFERENCE.md)

🎉 **Everything at your fingertips!**
