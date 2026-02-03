# 🚀 E-Commerce Backend - Complete System Reference

**Quick access to everything in your backend system.**

---

## 📋 Table of Contents
1. [Access Points](#access-points)
2. [Admin Panel](#admin-panel)
3. [API Endpoints](#api-endpoints)
4. [Database](#database)
5. [System Commands](#system-commands)
6. [File Structure](#file-structure)
7. [Features Overview](#features-overview)
8. [Testing](#testing)
9. [Credentials](#credentials)
10. [Troubleshooting](#troubleshooting)

---

## 🌐 Access Points

### **Live Services**
| Service | URL | Purpose |
|---------|-----|---------|
| 🎨 **Admin Panel** | http://localhost:8000/admin/ | Manage everything |
| 📡 **API Root** | http://localhost:8000/api/v1/ | REST API endpoints |
| 📖 **Swagger UI** | http://localhost:8000/api/v1/docs/ | Interactive API docs |
| 🔍 **API Schema** | http://localhost:8000/api/v1/schema/ | OpenAPI JSON |
| ❤️ **Health Check** | http://localhost:8000/api/v1/health/ | System status |
| 💾 **Database** | localhost:5432 | PostgreSQL |
| 🔴 **Redis** | localhost:6379 | Cache & sessions |

### **Development Tools**
| Tool | Command | Purpose |
|------|---------|---------|
| Django Shell | `docker compose -f docker-compose.dev.yml exec web python manage.py shell` | Interactive Python |
| Database Shell | `docker compose -f docker-compose.dev.yml exec web python manage.py dbshell` | PostgreSQL CLI |
| Logs | `docker compose -f docker-compose.dev.yml logs -f web` | View logs |
| Migrations | `docker compose -f docker-compose.dev.yml exec web python manage.py migrate` | Apply migrations |

---

## 🎨 Admin Panel

### **Access**
```
URL: http://localhost:8000/admin/
```

### **Default Credentials**
```
Email: admin@example.com
Password: admin123
```

### **What You Can Manage**

#### 📦 **Catalog**
- **Products** - All products with variants, images, prices
- **Categories** - Hierarchical category tree
- **Product Types** - Templates with attributes (Clothing, Electronics, etc.)
- **Attributes** - Reusable product attributes (Size, Color, RAM, etc.)

#### 🛒 **Sales**
- **Orders** - Order management with status workflow
- **Carts** - Active and abandoned carts
- **Coupons** - Discount codes and usage tracking
- **Shipping Zones** - Delivery areas and costs

#### 📄 **Content (CMS)**
- **Pages** - About, Contact, FAQ pages
- **Banners** - Homepage banners and promotions
- **Contact Submissions** - Customer inquiries
- **Site Settings** - Global configuration

#### 👥 **Customers**
- **Users** - Customer accounts
- **Addresses** - Shipping addresses

#### 🎭 **Engagement**
- **Reviews** - Product reviews (approval queue)
- **Wishlists** - Customer wishlists

#### ⚙️ **Settings**
- **Shipping Zones** - Areas and shipping costs
- **Tax Rules** - Tax configuration
- **Return Requests** - Return/refund management

### **Quick Actions**
```
✅ Confirm Order → Orders → Select → Actions → Confirm
✅ Approve Review → Reviews → Select → Actions → Approve
✅ Generate Variants → Product → Save → Auto-generates SKUs
✅ View Stats → Dashboard (home page)
```

---

## 📡 API Endpoints

### **Base URL**
```
http://localhost:8000/api/v1/
```

### **Public Endpoints** (No Authentication)

#### **Products**
```bash
GET  /products/                    # List all products
GET  /products/{slug}/             # Product detail
GET  /products/featured/           # Featured products
GET  /products/new/                # New arrivals
GET  /products/filters/            # Available filters
GET  /categories/                  # Category tree
GET  /categories/{slug}/           # Category with products
GET  /search/?q=                   # Search products
```

#### **Cart (Guest)**
```bash
GET    /cart/                      # Get cart
POST   /cart/items/                # Add to cart
PATCH  /cart/items/{id}/           # Update quantity
DELETE /cart/items/{id}/           # Remove item
POST   /cart/clear/                # Clear cart

# Header: X-Cart-Session: your-session-id
```

#### **Orders**
```bash
POST  /checkout/                   # Create order (guest or user)
POST  /orders/track/               # Track order by number+phone
GET   /shipping/zones/             # List shipping zones
POST  /shipping/calculate/         # Calculate shipping cost
```

#### **Coupons**
```bash
POST  /coupons/validate/           # Validate coupon code
```

#### **CMS**
```bash
GET   /pages/                      # List pages
GET   /pages/{slug}/               # Page content
GET   /banners/                    # Active banners
POST  /contact/                    # Submit contact form
GET   /settings/                   # Public site settings
```

#### **Reviews**
```bash
GET   /reviews/products/{id}/      # List product reviews
```

### **Authenticated Endpoints** (Requires Token)

#### **Authentication**
```bash
POST  /auth/register/              # Create account
POST  /auth/login/                 # Login (get token)
POST  /auth/logout/                # Logout
POST  /auth/refresh/               # Refresh access token
POST  /auth/password-reset/        # Request password reset
POST  /auth/password-reset/confirm/ # Confirm reset with token
```

#### **User Profile**
```bash
GET    /users/me/                  # Get profile
PATCH  /users/me/                  # Update profile
POST   /users/me/change-password/  # Change password
```

#### **Addresses**
```bash
GET    /users/me/addresses/        # List addresses
POST   /users/me/addresses/        # Add address
PATCH  /users/me/addresses/{id}/   # Update address
DELETE /users/me/addresses/{id}/   # Delete address
```

#### **Orders (User)**
```bash
GET   /orders/                     # My order history
GET   /orders/{order_number}/      # Order detail
```

#### **Reviews**
```bash
POST  /reviews/                    # Submit review
```

#### **Wishlist**
```bash
GET   /wishlist/                   # Get wishlist
POST  /wishlist/toggle/            # Add/remove item
POST  /wishlist/move-to-cart/      # Move to cart
```

### **Authentication Header**
```bash
Authorization: Bearer <your_access_token>
```

### **Guest Cart Header**
```bash
X-Cart-Session: <session_id>
```

---

## 💾 Database

### **Access PostgreSQL**
```bash
# Via Django
docker compose -f docker-compose.dev.yml exec web python manage.py dbshell

# Direct access
docker compose -f docker-compose.dev.yml exec db psql -U ecom_user -d ecom_db
```

### **Database Credentials**
```
Host: localhost (or 'db' from container)
Port: 5432
Database: ecom_db
Username: ecom_user
Password: ecom_password
```

### **Main Tables**
```sql
-- Products
products_product
products_productvariant
products_category
products_producttype
products_attribute

-- Orders
orders_order
orders_orderitem
orders_cart
orders_cartitem

-- Users
users_user
users_customeraddress

-- Promotions
promotions_coupon
promotions_couponusage

-- CMS
cms_page
cms_banner
cms_contactsubmission

-- Engagement
engagement_productreview
engagement_wishlist
```

### **Useful Queries**
```sql
-- Count products
SELECT COUNT(*) FROM products_product;

-- List orders today
SELECT * FROM orders_order 
WHERE created_at::date = CURRENT_DATE;

-- Active coupons
SELECT * FROM promotions_coupon 
WHERE is_active = true;

-- Low stock variants
SELECT * FROM products_productvariant 
WHERE stock_quantity <= low_stock_threshold;
```

---

## 🛠️ System Commands

### **Docker Commands**
```bash
# Start services
docker compose -f docker-compose.dev.yml up -d

# Stop services
docker compose -f docker-compose.dev.yml down

# Restart web service
docker compose -f docker-compose.dev.yml restart web

# View logs
docker compose -f docker-compose.dev.yml logs -f web

# Check status
docker compose -f docker-compose.dev.yml ps

# Rebuild
docker compose -f docker-compose.dev.yml up --build
```

### **Django Management Commands**
```bash
# Migrations
docker compose -f docker-compose.dev.yml exec web python manage.py makemigrations
docker compose -f docker-compose.dev.yml exec web python manage.py migrate

# Create superuser
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

# Collect static files
docker compose -f docker-compose.dev.yml exec web python manage.py collectstatic

# Django shell
docker compose -f docker-compose.dev.yml exec web python manage.py shell

# Database shell
docker compose -f docker-compose.dev.yml exec web python manage.py dbshell

# Check deployment
docker compose -f docker-compose.dev.yml exec web python manage.py check --deploy

# Custom commands
docker compose -f docker-compose.dev.yml exec web python manage.py cleanup_expired_carts
```

### **Testing Commands**
```bash
# Run all tests
docker compose -f docker-compose.dev.yml exec web pytest

# Run specific app tests
docker compose -f docker-compose.dev.yml exec web pytest apps/products/tests/

# Run with coverage
docker compose -f docker-compose.dev.yml exec web pytest --cov=apps --cov-report=html

# Run verbose
docker compose -f docker-compose.dev.yml exec web pytest -v

# Stop on first failure
docker compose -f docker-compose.dev.yml exec web pytest -x
```

---

## 📁 File Structure

```
website_3/
├── .github/
│   └── copilot-instructions.md        # AI build instructions
├── src/
│   ├── apps/                          # Django applications
│   │   ├── core/                      # Base models, utilities
│   │   ├── users/                     # User management
│   │   ├── products/                  # Products & variants
│   │   ├── orders/                    # Cart, orders, shipping
│   │   ├── promotions/                # Coupons
│   │   ├── engagement/                # Reviews, wishlist
│   │   ├── cms/                       # Pages, banners
│   │   ├── notifications/             # Email service
│   │   └── dashboard/                 # Admin dashboard
│   ├── api/
│   │   └── v1/                        # API endpoints
│   │       ├── products/
│   │       ├── cart/
│   │       ├── users/
│   │       └── cms/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py               # Shared settings
│   │   │   ├── dev.py                # Development
│   │   │   └── prod.py               # Production
│   │   ├── urls.py                   # URL routing
│   │   └── wsgi.py                   # WSGI config
│   └── manage.py                      # Django CLI
├── scripts/
│   ├── backup.sh                      # Database backup
│   ├── deploy.sh                      # Deployment
│   ├── validate_production.sh         # Pre-deploy checks
│   └── test_api.sh                    # Quick API test
├── nginx/                             # Nginx config (production)
├── requirements/
│   ├── base.txt                       # Core dependencies
│   └── dev.txt                        # Dev dependencies
├── docker-compose.dev.yml             # Development setup
├── docker-compose.prod.yml            # Production setup
├── Dockerfile                         # Development image
├── Dockerfile.prod                    # Production image
└── README.md                          # Project overview
```

---

## ⚡ Features Overview

### **🎯 Product Management (EAV System)**
```
✅ Dynamic Attributes - Add any attribute without code changes
✅ Product Types - Template-based (Clothing, Electronics, etc.)
✅ Variant Generation - Auto-generate SKUs from attributes
✅ Multi-image Support - Upload multiple images per product/variant
✅ SEO Fields - Meta title, description, slug
✅ Inventory Tracking - Stock levels, low-stock alerts
✅ Price Management - Base, compare, cost prices
✅ Price History - Track all price changes
```

### **🛒 Order Management**
```
✅ Guest Checkout - No account required
✅ User Checkout - Saved addresses
✅ Order Status Workflow - Pending → Confirmed → Shipped → Delivered
✅ Status Logging - Full audit trail
✅ Payment Methods - COD, bKash, Nagad, Cards
✅ Payment Logging - Transaction history
✅ Shipping Zones - Area-based pricing
✅ Coupon System - Discount codes with rules
✅ Return/Refund - Request workflow
```

### **👤 User Management**
```
✅ JWT Authentication - Token-based auth
✅ Role-based Permissions - Staff groups (Order Manager, Product Manager, etc.)
✅ Customer Profiles - Order history, stats
✅ Address Management - Multiple addresses
✅ Block Users - Prevent access with reason
```

### **🎨 Content Management**
```
✅ Pages - About, Contact, FAQ
✅ Banners - Scheduled promotions
✅ Contact Forms - Customer inquiries
✅ Site Settings - Key-value config
```

### **💬 Engagement**
```
✅ Product Reviews - Star rating + text + images
✅ Review Approval - Admin moderation
✅ Wishlist - Save for later
✅ Admin Replies - Respond to reviews
```

### **📧 Notifications**
```
✅ Order Confirmation - Email on order
✅ Shipped Notification - Tracking info
✅ Welcome Email - On registration
✅ Password Reset - Secure token
```

---

## 🧪 Testing

### **Quick API Test**
```bash
./scripts/test_api.sh
```

### **Interactive Testing (Swagger)**
```
http://localhost:8000/api/v1/docs/
```

### **Automated Tests**
```bash
# All tests
docker compose -f docker-compose.dev.yml exec web pytest

# Specific app
docker compose -f docker-compose.dev.yml exec web pytest apps/products/tests/ -v

# Coverage report
docker compose -f docker-compose.dev.yml exec web pytest --cov=apps --cov-report=html
open htmlcov/index.html
```

### **Manual Testing (HTTPie)**
```bash
# Install
pip install httpie

# Test endpoint
http GET http://localhost:8000/api/v1/products/

# With auth
http GET http://localhost:8000/api/v1/users/me/ "Authorization: Bearer TOKEN"
```

### **Manual Testing (cURL)**
```bash
# Health check
curl http://localhost:8000/api/v1/health/

# List products
curl http://localhost:8000/api/v1/products/

# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}'
```

---

## 🔐 Credentials

### **Admin Panel**
```
URL: http://localhost:8000/admin/
Email: admin@example.com
Password: admin123
```

### **Database**
```
Host: localhost
Port: 5432
Database: ecom_db
Username: ecom_user
Password: ecom_password
```

### **Redis**
```
Host: localhost
Port: 6379
Password: (none in dev)
```

### **Test User** (Create via API)
```
Email: test@example.com
Password: SecurePass123!
Phone: 01812345678
```

---

## 🔍 Troubleshooting

### **Services Not Running?**
```bash
# Check status
docker compose -f docker-compose.dev.yml ps

# Start services
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f web
```

### **Admin Panel Not Loading?**
```bash
# Collect static files
docker compose -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput

# Restart web
docker compose -f docker-compose.dev.yml restart web
```

### **Database Issues?**
```bash
# Check migrations
docker compose -f docker-compose.dev.yml exec web python manage.py showmigrations

# Apply migrations
docker compose -f docker-compose.dev.yml exec web python manage.py migrate

# Reset database (⚠️ DANGER: Deletes all data)
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

### **API Returning 401/403?**
```bash
# Check token validity
# Login again to get fresh token

# For authenticated endpoints
# Include: Authorization: Bearer <token>
```

### **Port Already in Use?**
```bash
# Stop existing containers
docker compose -f docker-compose.dev.yml down

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Restart
docker compose -f docker-compose.dev.yml up -d
```

---

## 📊 Quick Stats Commands

### **Product Stats**
```bash
# Count products
docker compose -f docker-compose.dev.yml exec web python manage.py shell -c "from apps.products.models import Product; print(Product.objects.count())"

# Count variants
docker compose -f docker-compose.dev.yml exec web python manage.py shell -c "from apps.products.models import ProductVariant; print(ProductVariant.objects.count())"
```

### **Order Stats**
```bash
# Today's orders
docker compose -f docker-compose.dev.yml exec web python manage.py shell -c "from apps.orders.models import Order; from django.utils import timezone; print(Order.objects.filter(created_at__date=timezone.now().date()).count())"

# Total revenue
docker compose -f docker-compose.dev.yml exec web python manage.py shell -c "from apps.orders.models import Order; from django.db.models import Sum; print(Order.objects.aggregate(Sum('total')))"
```

### **User Stats**
```bash
# Total users
docker compose -f docker-compose.dev.yml exec web python manage.py shell -c "from apps.users.models import User; print(User.objects.count())"

# Users registered today
docker compose -f docker-compose.dev.yml exec web python manage.py shell -c "from apps.users.models import User; from django.utils import timezone; print(User.objects.filter(created_at__date=timezone.now().date()).count())"
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Project overview & setup |
| **SYSTEM_REFERENCE.md** | This file - complete system guide |
| **API_TESTING_GUIDE.md** | Comprehensive API testing guide |
| **QUICK_TEST.md** | Quick start testing guide |
| **SWAGGER_GUIDE.md** | Swagger UI usage guide |
| **DEPLOYMENT.md** | Production deployment guide |
| **PRODUCTION_CHECKLIST.md** | Pre-deployment checklist |
| **.github/copilot-instructions.md** | AI build instructions (2,228 lines) |

---

## 🎯 Common Tasks

### **Add New Product**
```
1. Admin Panel → Catalog → Products → Add Product
2. Select Product Type (e.g., Clothing)
3. Fill required fields (name, category, base price)
4. Save
5. Add images (multiple supported)
6. Generate variants (if has variant attributes)
```

### **Process Order**
```
1. Admin Panel → Sales → Orders
2. Find order
3. Actions → Confirm (deducts stock)
4. Actions → Process → Shipped
5. Enter tracking number
6. Customer gets notification
```

### **Create Coupon**
```
1. Admin Panel → Sales → Coupons → Add Coupon
2. Enter code, name, discount (% or fixed)
3. Set validity dates, usage limits
4. Optional: Restrict to categories/products
5. Save
```

### **Approve Review**
```
1. Admin Panel → Engagement → Reviews
2. Filter: is_approved=False
3. Select reviews
4. Actions → Approve
5. Optionally: Add admin reply
```

### **Register API User**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "first_name": "New",
    "last_name": "User",
    "phone": "01812345678"
  }'
```

---

## 🚀 Next Steps

### **For Development:**
1. ✅ Access admin: http://localhost:8000/admin/
2. ✅ Add sample products
3. ✅ Test APIs: http://localhost:8000/api/v1/docs/
4. ✅ Run tests: `docker compose -f docker-compose.dev.yml exec web pytest`

### **For Production:**
1. ✅ Review: `PRODUCTION_CHECKLIST.md`
2. ✅ Read: `DEPLOYMENT.md`
3. ✅ Run: `./scripts/validate_production.sh`
4. ✅ Deploy: `./scripts/deploy.sh`

---

## 📞 Quick Help

**Can't find something?**
- Check [README.md](README.md) for project overview
- Check [API_TESTING_GUIDE.md](API_TESTING_GUIDE.md) for API details
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Check `.github/copilot-instructions.md` for complete build guide

**Have an issue?**
1. Check logs: `docker compose -f docker-compose.dev.yml logs -f web`
2. Check database: `docker compose -f docker-compose.dev.yml exec web python manage.py dbshell`
3. Check Django check: `docker compose -f docker-compose.dev.yml exec web python manage.py check`

---

**Last Updated:** February 3, 2026  
**Version:** 3.0  
**Status:** ✅ Production Ready

🎉 **Everything you need to know about your e-commerce backend!**
