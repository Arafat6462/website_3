"""
Locust Load Testing - Comprehensive API Testing

Tests ALL API endpoints to measure VPS capacity.
Use this for stress testing and finding breaking points.

Access Web UI: http://localhost:8089
Progressive testing: 10 → 50 → 100 → 200 → 500 users
"""

from locust import HttpUser, task, between
import random


class ComprehensiveAPITester(HttpUser):
    """
    Comprehensive API tester - hits all major endpoints.
    
    Tests every API endpoint to find bottlenecks and capacity limits.
    """
    weight = 10
    wait_time = between(0.5, 2)  # Faster testing
    
    # Health & System
    @task(10)
    def health_check(self):
        """API health check - fastest endpoint."""
        self.client.get("/api/v1/health/", name="/api/v1/health/")
    
    # Product Endpoints (Read-heavy)
    @task(20)
    def list_products(self):
        """List products with pagination."""
        page = random.randint(1, 3)
        self.client.get(f"/api/v1/products/?page={page}", name="/api/v1/products/")
    
    @task(10)
    def view_product_detail(self):
        """View specific product."""
        response = self.client.get("/api/v1/products/")
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    product = data['results'][0]
                    slug = product.get('slug')
                    if slug:
                        self.client.get(f"/api/v1/products/{slug}/", name="/api/v1/products/[slug]/")
            except:
                pass
    
    @task(8)
    def browse_featured_products(self):
        """Featured products."""
        self.client.get("/api/v1/products/featured/", name="/api/v1/products/featured/")
    
    @task(5)
    def browse_new_products(self):
        """New arrivals."""
        self.client.get("/api/v1/products/new/", name="/api/v1/products/new/")
    
    # Category Endpoints
    @task(8)
    def list_categories(self):
        """List all categories."""
        self.client.get("/api/v1/categories/", name="/api/v1/categories/")
    
    @task(5)
    def view_category_detail(self):
        """View category with products."""
        response = self.client.get("/api/v1/categories/")
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    category = data[0]
                    slug = category.get('slug')
                    if slug:
                        self.client.get(f"/api/v1/categories/{slug}/", name="/api/v1/categories/[slug]/")
            except:
                pass
    
    # Search Endpoint (Heavy database query)
    @task(7)
    def search_products(self):
        """Full-text search."""
        queries = ["laptop", "phone", "shirt", "shoes", "watch", "bag", ""]
        query = random.choice(queries)
        self.client.get(f"/api/v1/search/?q={query}", name="/api/v1/search/")
    
    # Cart Endpoints
    @task(5)
    def view_cart(self):
        """View shopping cart."""
        self.client.get("/api/v1/cart/", name="/api/v1/cart/")
    
    # Shipping
    @task(3)
    def list_shipping_zones(self):
        """List shipping zones."""
        self.client.get("/api/v1/shipping/zones/", name="/api/v1/shipping/zones/")
    
    # CMS Endpoints
    @task(4)
    def list_pages(self):
        """List CMS pages."""
        self.client.get("/api/v1/pages/", name="/api/v1/pages/")
    
    @task(3)
    def list_banners(self):
        """List banners."""
        self.client.get("/api/v1/banners/", name="/api/v1/banners/")
    
    # Static Files (served by WhiteNoise)
    @task(6)
    def load_static_css(self):
        """Load static CSS files."""
        self.client.get("/static/unfold/css/styles.css", name="/static/[css]")
    
    @task(2)
    def load_admin_page(self):
        """Load admin login page."""
        self.client.get("/admin/", name="/admin/")
    
    # Media Files (if exist)
    @task(3)
    def load_media_file(self):
        """Load uploaded images."""
        # Try to get first product with image
        response = self.client.get("/api/v1/products/")
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('results'):
                    for product in data['results']:
                        if product.get('primary_image'):
                            image_url = product['primary_image']
                            # Extract path after domain
                            if '/media/' in image_url:
                                media_path = image_url.split('/media/', 1)[1]
                                self.client.get(f"/media/{media_path}", name="/media/[image]")
                                break
            except:
                pass


class DatabaseIntensiveTester(HttpUser):
    """
    Database-heavy operations tester.
    Tests complex queries to stress database.
    """
    weight = 3
    wait_time = between(1, 3)
    
    @task(5)
    def complex_product_search(self):
        """Complex search with filters."""
        filters = [
            "?category=electronics",
            "?price_min=100&price_max=1000",
            "?in_stock=true",
            "?is_featured=true",
            "?sort=-created_at",
        ]
        filter_query = random.choice(filters)
        self.client.get(f"/api/v1/products/{filter_query}", name="/api/v1/products/[filtered]")
    
    @task(3)
    def search_with_query(self):
        """Text search (uses database indexing)."""
        queries = ["laptop gaming", "nike shoes", "iphone", "samsung", "adidas"]
        query = random.choice(queries)
        self.client.get(f"/api/v1/search/?q={query}", name="/api/v1/search/[complex]")
    
    @task(2)
    def category_with_products(self):
        """Category detail with products (join query)."""
        self.client.get("/api/v1/categories/?include_products=true", name="/api/v1/categories/[products]")


class StressTestMode(HttpUser):
    """
    EXTREME STRESS MODE - Use carefully!
    
    Change weight from 0 to 5+ to activate aggressive testing.
    This will hammer your server with rapid requests.
    """
    weight = 0  # Set to 5 or 10 for extreme stress testing
    wait_time = between(0.1, 0.5)  # Very fast
    
    @task
    def rapid_fire_health(self):
        """Rapid health checks."""
        self.client.get("/api/v1/health/")
    
    @task
    def rapid_fire_products(self):
        """Rapid product listing."""
        self.client.get("/api/v1/products/")
    
    @task
    def rapid_fire_search(self):
        """Rapid search."""
        self.client.get("/api/v1/search/?q=test")
