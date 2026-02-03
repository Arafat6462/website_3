"""Phase 14: Product API - Comprehensive Tests.

This test module validates:
- Product list endpoint with pagination
- Product detail endpoint with nested data
- Category endpoints (list, tree, products)
- Filtering (category, price, stock, featured, new)
- Search functionality
- Product type endpoints
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.products.models import (
    Product, ProductVariant, Category, ProductType, Attribute,
    ProductTypeAttribute, ProductImage, ProductAttributeValue,
    VariantAttributeValue
)
from apps.engagement.models import ProductReview
from apps.users.models import User


class ProductAPITestCase(TestCase):
    """Base test case with common setup."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        # Create category
        self.category = Category.objects.create(
            name="Clothing",
            slug="clothing",
            status="active"
        )
        
        # Create product type
        self.product_type = ProductType.objects.create(
            name="T-Shirt",
            slug="t-shirt",
            is_active=True
        )
        
        # Create attributes
        self.size_attr = Attribute.objects.create(
            name="Size",
            code="size",
            field_type="select",
            is_variant=True,
            is_filterable=True
        )
        
        self.color_attr = Attribute.objects.create(
            name="Color",
            code="color",
            field_type="color",
            is_variant=True,
            is_filterable=True
        )
        
        # Link attributes to product type
        ProductTypeAttribute.objects.create(
            product_type=self.product_type,
            attribute=self.size_attr,
            sort_order=1
        )
        ProductTypeAttribute.objects.create(
            product_type=self.product_type,
            attribute=self.color_attr,
            sort_order=2
        )
        
        # Create product
        self.product = Product.objects.create(
            name="Cotton T-Shirt",
            slug="cotton-t-shirt",
            short_description="Comfortable cotton tee",
            description="High quality 100% cotton t-shirt",
            category=self.category,
            product_type=self.product_type,
            base_price=Decimal("500.00"),
            compare_price=Decimal("700.00"),
            status="published",
            is_featured=True,
            is_new=True
        )
        
        # Create variant
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="CTEE-M-BLK",
            name="Medium Black",
            price=Decimal("500.00"),
            stock_quantity=10,
            is_active=True,
            is_default=True
        )
        
        # Create variant attributes
        VariantAttributeValue.objects.create(
            variant=self.variant,
            attribute=self.size_attr,
            value="M"
        )
        VariantAttributeValue.objects.create(
            variant=self.variant,
            attribute=self.color_attr,
            value="#000000"
        )
        
        # Create image
        ProductImage.objects.create(
            product=self.product,
            variant=None,
            image="products/test.jpg",
            alt_text="Cotton T-Shirt",
            is_primary=True,
            sort_order=1
        )


class ProductListAPITest(ProductAPITestCase):
    """Test product list endpoint."""
    
    def test_list_products(self):
        """Test getting product list."""
        url = reverse('api-v1:product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        
        product_data = response.data['results'][0]
        self.assertEqual(product_data['name'], 'Cotton T-Shirt')
        self.assertEqual(product_data['slug'], 'cotton-t-shirt')
        self.assertIn('category', product_data)
        self.assertIn('primary_image', product_data)
    
    def test_list_products_pagination(self):
        """Test product list pagination."""
        # Create more products
        for i in range(25):
            Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                category=self.category,
                product_type=self.product_type,
                base_price=Decimal("100.00"),
                status="published"
            )
        
        url = reverse('api-v1:product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertEqual(response.data['count'], 26)  # 1 + 25
    
    def test_product_ordering(self):
        """Test product ordering."""
        # Create another product (created after the one in setUp, so it's newer)
        old_product = Product.objects.create(
            name="Old Product",
            slug="old-product",
            category=self.category,
            product_type=self.product_type,
            base_price=Decimal("100.00"),
            status="published"
        )
        
        url = reverse('api-v1:product-list')
        
        # Default ordering (-created_at, newest first)
        # Since old_product was created after cotton-t-shirt in setUp, it should be first
        response = self.client.get(url)
        self.assertEqual(response.data['results'][0]['slug'], 'old-product')
        
        # Order by price ascending (old-product has lower price)
        response = self.client.get(url, {'ordering': 'base_price'})
        self.assertEqual(response.data['results'][0]['slug'], 'old-product')


class ProductDetailAPITest(ProductAPITestCase):
    """Test product detail endpoint."""
    
    def test_get_product_detail(self):
        """Test getting product detail."""
        url = reverse('api-v1:product-detail', kwargs={'slug': 'cotton-t-shirt'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Cotton T-Shirt')
        self.assertEqual(response.data['slug'], 'cotton-t-shirt')
        
        # Check nested data
        self.assertIn('category', response.data)
        self.assertIn('product_type', response.data)
        self.assertIn('variants', response.data)
        self.assertIn('images', response.data)
        self.assertIn('attributes', response.data)
        
        # Check variants
        self.assertEqual(len(response.data['variants']), 1)
        variant_data = response.data['variants'][0]
        self.assertEqual(variant_data['sku'], 'CTEE-M-BLK')
        self.assertEqual(len(variant_data['attributes']), 2)
    
    def test_product_detail_increments_view_count(self):
        """Test view count increments on detail view."""
        url = reverse('api-v1:product-detail', kwargs={'slug': 'cotton-t-shirt'})
        
        initial_count = self.product.view_count
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from DB
        self.product.refresh_from_db()
        self.assertEqual(self.product.view_count, initial_count + 1)
    
    def test_product_not_found(self):
        """Test 404 for non-existent product."""
        url = reverse('api-v1:product-detail', kwargs={'slug': 'non-existent'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProductFilterAPITest(ProductAPITestCase):
    """Test product filtering."""
    
    def setUp(self):
        """Create additional test data for filtering."""
        super().setUp()
        
        # Create another category
        self.electronics = Category.objects.create(
            name="Electronics",
            slug="electronics",
            status="active"
        )
        
        # Create another product in different category
        self.phone = Product.objects.create(
            name="Smartphone",
            slug="smartphone",
            category=self.electronics,
            product_type=self.product_type,
            base_price=Decimal("15000.00"),
            status="published",
            is_featured=False,
            is_new=False
        )
        
        ProductVariant.objects.create(
            product=self.phone,
            sku="PHONE-001",
            name="64GB Black",
            price=Decimal("15000.00"),
            stock_quantity=0,  # Out of stock
            is_active=True,
            is_default=True
        )
    
    def test_filter_by_category(self):
        """Test filtering by category."""
        url = reverse('api-v1:product-list')
        response = self.client.get(url, {'category': 'clothing'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['slug'], 'cotton-t-shirt')
    
    def test_filter_by_price_range(self):
        """Test filtering by price range."""
        url = reverse('api-v1:product-list')
        
        # Min price filter
        response = self.client.get(url, {'price_min': '10000'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['slug'], 'smartphone')
        
        # Max price filter
        response = self.client.get(url, {'price_max': '1000'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['slug'], 'cotton-t-shirt')
        
        # Range filter
        response = self.client.get(url, {'price_min': '100', 'price_max': '1000'})
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_in_stock(self):
        """Test filtering by stock availability."""
        url = reverse('api-v1:product-list')
        response = self.client.get(url, {'in_stock': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['slug'], 'cotton-t-shirt')
    
    def test_filter_featured(self):
        """Test filtering featured products."""
        url = reverse('api-v1:product-list')
        response = self.client.get(url, {'is_featured': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['is_featured'], True)
    
    def test_filter_new(self):
        """Test filtering new products."""
        url = reverse('api-v1:product-list')
        response = self.client.get(url, {'is_new': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['is_new'], True)


class ProductSearchAPITest(ProductAPITestCase):
    """Test product search functionality."""
    
    def setUp(self):
        """Create additional products for search."""
        super().setUp()
        
        Product.objects.create(
            name="Denim Jeans",
            slug="denim-jeans",
            short_description="Classic denim jeans",
            description="Comfortable blue jeans",
            category=self.category,
            product_type=self.product_type,
            base_price=Decimal("1200.00"),
            status="published"
        )
    
    def test_search_products(self):
        """Test product search."""
        url = reverse('api-v1:product-list')
        
        # Search by name
        response = self.client.get(url, {'search': 'cotton'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['slug'], 'cotton-t-shirt')
        
        # Search by description
        response = self.client.get(url, {'search': 'jeans'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['slug'], 'denim-jeans')
        
        # No results
        response = self.client.get(url, {'search': 'nonexistent'})
        self.assertEqual(len(response.data['results']), 0)


class CategoryAPITest(ProductAPITestCase):
    """Test category endpoints."""
    
    def setUp(self):
        """Create category hierarchy."""
        super().setUp()
        
        # Create child category
        self.mens = Category.objects.create(
            name="Men's Clothing",
            slug="mens-clothing",
            parent=self.category,
            status="active"
        )
    
    def test_list_categories(self):
        """Test getting category list."""
        url = reverse('api-v1:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return root categories (no parent)
        # Check if response is paginated or direct list
        if isinstance(response.data, dict) and 'results' in response.data:
            categories = response.data['results']
        elif isinstance(response.data, list):
            categories = response.data
        else:
            # If it's a dict but not paginated, it might be the direct response
            categories = [response.data] if isinstance(response.data, dict) else response.data
        
        self.assertEqual(len(categories), 1, f"Expected 1 category, got {len(categories)}: {categories}")
        self.assertEqual(categories[0]['slug'], 'clothing')
    
    def test_category_detail(self):
        """Test getting category detail."""
        url = reverse('api-v1:category-detail', kwargs={'slug': 'clothing'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Clothing')
    
    def test_category_tree(self):
        """Test getting category tree."""
        url = reverse('api-v1:category-tree')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Check nested children
        category_data = response.data[0]
        self.assertIn('children', category_data)
        self.assertEqual(len(category_data['children']), 1)
        self.assertEqual(category_data['children'][0]['slug'], 'mens-clothing')
    
    def test_category_products(self):
        """Test getting products in category."""
        url = reverse('api-v1:category-products', kwargs={'slug': 'clothing'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class ProductActionAPITest(ProductAPITestCase):
    """Test product custom actions."""
    
    def test_featured_products(self):
        """Test getting featured products."""
        url = reverse('api-v1:product-featured')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(response.data['results'][0]['is_featured'])
    
    def test_new_products(self):
        """Test getting new products."""
        url = reverse('api-v1:product-new')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(response.data['results'][0]['is_new'])
    
    def test_product_filters_endpoint(self):
        """Test getting available filter options."""
        url = reverse('api-v1:product-filters')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('categories', response.data)
        self.assertIn('price_range', response.data)
        self.assertIn('product_types', response.data)
        
        # Check price range
        self.assertIn('min', response.data['price_range'])
        self.assertIn('max', response.data['price_range'])


class ProductTypeAPITest(ProductAPITestCase):
    """Test product type endpoints."""
    
    def test_list_product_types(self):
        """Test getting product type list."""
        url = reverse('api-v1:producttype-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated or direct list
        if isinstance(response.data, dict) and 'results' in response.data:
            product_types = response.data['results']
        elif isinstance(response.data, list):
            product_types = response.data
        else:
            product_types = [response.data] if isinstance(response.data, dict) else response.data
        
        self.assertEqual(len(product_types), 1, f"Expected 1 product type, got {len(product_types)}")
        self.assertEqual(product_types[0]['slug'], 't-shirt')
    
    def test_product_type_detail(self):
        """Test getting product type detail with attributes."""
        url = reverse('api-v1:producttype-detail', kwargs={'slug': 't-shirt'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'T-Shirt')
        self.assertIn('attributes', response.data)
        self.assertEqual(len(response.data['attributes']), 2)


class HealthCheckAPITest(TestCase):
    """Test API health check endpoint."""
    
    def test_health_check(self):
        """Test health check returns OK."""
        response = self.client.get('/api/v1/health/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['api'], 'v1')


class APIRootTest(TestCase):
    """Test API root endpoint."""
    
    def test_api_root(self):
        """Test API root returns endpoint list."""
        response = self.client.get('/api/v1/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('version', response.data)
        self.assertIn('endpoints', response.data)
        self.assertIn('products', response.data['endpoints'])
