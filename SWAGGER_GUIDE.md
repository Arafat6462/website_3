# 📖 Swagger API Documentation - Quick Guide

## ✅ **YES! Swagger is Already Included & Working!**

### 🌐 **Access Swagger UI:**
```
http://localhost:8000/api/v1/docs/
```

### 📄 **Download OpenAPI Schema (JSON):**
```
http://localhost:8000/api/v1/schema/
```

---

## 🎯 Why Swagger/drf-spectacular?

### ✅ **Lightweight & Fast**
- Minimal overhead (~50KB)
- Auto-generates from your code
- No manual writing needed

### ✅ **Always Up-to-Date**
- Automatically reflects code changes
- No documentation drift
- Real-time accuracy

### ✅ **Developer Friendly**
- Interactive testing interface
- Try APIs without external tools
- Built-in authentication support

---

## 🚀 How to Use Swagger UI

### 1️⃣ **Browse All Endpoints**
Open http://localhost:8000/api/v1/docs/ - you'll see:
- ✅ All API endpoints grouped by category
- ✅ HTTP methods (GET, POST, PATCH, DELETE)
- ✅ Request/Response schemas
- ✅ Required parameters

### 2️⃣ **Test Public Endpoints** (No Auth)
```
1. Find endpoint (e.g., "GET /api/v1/products/")
2. Click to expand
3. Click "Try it out"
4. Click "Execute"
5. See response below!
```

### 3️⃣ **Test Authenticated Endpoints**
```
Step 1: Get a token
  - Find "POST /api/v1/auth/login/"
  - Click "Try it out"
  - Enter email & password
  - Click "Execute"
  - Copy the "access" token from response

Step 2: Authorize
  - Click "Authorize" button (🔓 top right)
  - Enter: Bearer YOUR_ACCESS_TOKEN
  - Click "Authorize"
  - Click "Close"

Step 3: Test protected endpoints
  - Now all 🔒 endpoints work!
  - Try "GET /api/v1/users/me/"
```

---

## 📊 What You'll See

### **Grouped by Category:**
```
✅ Products API
  - GET /products/           List products
  - GET /products/{slug}/    Product detail
  - GET /products/featured/  Featured products
  
✅ Cart API
  - GET /cart/               Get cart
  - POST /cart/items/        Add to cart
  - PATCH /cart/items/{id}/  Update quantity
  
✅ Auth API
  - POST /auth/register/     Register user
  - POST /auth/login/        Login
  - POST /auth/logout/       Logout
  
✅ Orders API
  - GET /orders/             My orders
  - POST /checkout/          Create order
  
... and more!
```

### **For Each Endpoint:**
- **Description** - What it does
- **Parameters** - What data it needs
- **Request Body** - Example JSON (for POST/PATCH)
- **Responses** - Status codes & examples (200, 400, 401, etc.)
- **Try it out** - Interactive testing

---

## 🔧 Technical Details

### **Package:** `drf-spectacular`
- **Size:** ~50KB
- **Performance:** Negligible overhead
- **Standards:** OpenAPI 3.0 compliant
- **Auto-generation:** 100% automatic

### **Configuration:**
```python
# In settings/base.py
SPECTACULAR_SETTINGS = {
    "TITLE": "E-Commerce API",
    "DESCRIPTION": "API for e-commerce backend",
    "VERSION": "1.0.0",
    "SCHEMA_PATH_PREFIX": "/api/v1",
}
```

### **URLs:**
```python
# Swagger UI - Interactive docs
/api/v1/docs/

# OpenAPI Schema - JSON file
/api/v1/schema/
```

---

## 💡 Pro Tips

### **Export Schema for Postman/Insomnia**
```bash
# Download the schema
curl http://localhost:8000/api/v1/schema/ -o openapi.json

# Import to Postman:
# File → Import → openapi.json
```

### **Test Scenarios**
Use Swagger UI to:
1. ✅ Register a new user
2. ✅ Login and get token
3. ✅ Browse products
4. ✅ Add items to cart
5. ✅ Checkout
6. ✅ View order history

### **Share with Frontend Team**
```
Just send them: http://localhost:8000/api/v1/docs/

They can:
- See all endpoints
- Test APIs directly
- Download OpenAPI schema
- Generate API client code
```

---

## 📱 Screenshots (What You'll See)

```
┌─────────────────────────────────────────────────┐
│  E-Commerce API                         Authorize│
├─────────────────────────────────────────────────┤
│                                                  │
│  ▼ Products API                                 │
│     GET  /api/v1/products/     [Try it out]    │
│     GET  /api/v1/products/{slug}/              │
│                                                  │
│  ▼ Cart API                                     │
│     GET  /api/v1/cart/         [Try it out]    │
│     POST /api/v1/cart/items/                   │
│                                                  │
│  ▼ Auth API                                     │
│     POST /api/v1/auth/register/                │
│     POST /api/v1/auth/login/   [Try it out]    │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## ✅ Summary

**Is Swagger included?** ✅ **YES!**

**Is it lightweight?** ✅ **YES!** (~50KB, auto-generated)

**Is it easy to use?** ✅ **YES!** (Click, test, done!)

**Should you use it?** ✅ **ABSOLUTELY!**

---

## 🚀 Get Started Now

```bash
# 1. Open Swagger UI in browser
http://localhost:8000/api/v1/docs/

# 2. Click any endpoint → "Try it out" → "Execute"

# 3. For auth endpoints:
#    - Login first → Copy token
#    - Click "Authorize" → Enter token
#    - Now test protected endpoints!
```

**That's it!** No installation, no configuration needed. Just open and test! 🎉
