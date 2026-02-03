"""Tests for Cart API.

This module provides comprehensive tests for:
- Cart operations (get, add, update, remove, clear)
- Checkout and order creation
- Coupon validation
- Shipping calculation
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient

from apps.products.models import (
    Category, ProductType, Product, ProductVariant, Attribute, ProductTypeAttribute
)
from apps.orders.models import Cart, CartItem, Coupon, ShippingZone, Order
from apps.users.models import User


class CartAPITestCase(TestCase):
    """Base test case with common setup for cart tests."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        # Create category
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            status="active"
        )
        
        # Create product type
        self.product_type = ProductType.objects.create(
            name="Phone",
            slug="phone",
            is_active=True
        )
        
        # Create products and variants
        self.product1 = Product.objects.create(
            name="Phone A",
            slug="phone-a",
            category=self.category,
            product_type=self.product_type,
            base_price=Decimal("10000.00"),
            status="published",
            track_inventory=True
        )
        
        self.variant1 = ProductVariant.objects.create(
            product=self.product1,
            sku="PHONE-A-001",
            name="64GB Black",
            price=Decimal("10000.00"),
            stock_quantity=50,
            is_active=True,
            is_default=True
        )
        
        self.product2 = Product.objects.create(
            name="Phone B",
            slug="phone-b",
            category=self.category,
            product_type=self.product_type,
            base_price=Decimal("15000.00"),
            status="published",
            track_inventory=True
        )
        
        self.variant2 = ProductVariant.objects.create(
            product=self.product2,
            sku="PHONE-B-001",
            name="128GB White",
            price=Decimal("15000.00"),
            stock_quantity=30,
            is_active=True,
            is_default=True
        )
        
        # Create shipping zone
        self.shipping_zone = ShippingZone.objects.create(
            name="Dhaka",
            areas=["Dhaka", "Mirpur", "Gulshan"],
            shipping_cost=Decimal("100.00"),
            free_shipping_threshold=Decimal("20000.00"),
            estimated_days="1-2 days",
            is_active=True,
            sort_order=1
        )
        
        # Create coupon
        self.coupon = Coupon.objects.create(
            code="SAVE10",
            name="10% Off",
            description="Save 10% on your order",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            minimum_order=Decimal("5000.00"),
            maximum_discount=Decimal("1000.00"),
            usage_limit=100,
            usage_limit_per_user=1,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True
        )


class CartOperationTest(CartAPITestCase):
    """Test cart operations."""
    
    def test_get_empty_cart(self):
        """Test getting empty cart."""
        url = '/api/v1/cart/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['item_count'], 0)
        self.assertEqual(response.data['subtotal'], 0)
        self.assertEqual(len(response.data['items']), 0)
    
    def test_add_to_cart(self):
        """Test adding item to cart."""
        url = '/api/v1/cart/items/'
        data = {
            'variant_id': self.variant1.id,
            'quantity': 2
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item_count'], 2)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['quantity'], 2)
    
    def test_add_to_cart_insufficient_stock(self):
        """Test adding more items than available stock."""
        url = '/api/v1/cart/items/'
        data = {
            'variant_id': self.variant1.id,
            'quantity': 100  # More than stock_quantity=50
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', response.data)
    
    def test_add_multiple_items_to_cart(self):
        """Test adding multiple different items."""
        url = '/api/v1/cart/items/'
        
        # Add first item
        response = self.client.post(url, {
            'variant_id': self.variant1.id,
            'quantity': 1
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Add second item
        response = self.client.post(url, {
            'variant_id': self.variant2.id,
            'quantity': 2
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item_count'], 3)  # 1 + 2
        self.assertEqual(len(response.data['items']), 2)  # 2 different items
    
    def test_add_same_item_increases_quantity(self):
        """Test adding same item twice increases quantity."""
        url = '/api/v1/cart/items/'
        
        # Add first time
        response = self.client.post(url, {
            'variant_id': self.variant1.id,
            'quantity': 2
        }, format='json')
        self.assertEqual(response.data['items'][0]['quantity'], 2)
        
        # Add again
        response = self.client.post(url, {
            'variant_id': self.variant1.id,
            'quantity': 3
        }, format='json')
        
        # Should increase quantity
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['quantity'], 5)  # 2 + 3
    
    def test_update_cart_item_quantity(self):
        """Test updating cart item quantity."""
        # Add item first
        add_url = '/api/v1/cart/items/'
        self.client.post(add_url, {
            'variant_id': self.variant1.id,
            'quantity': 2
        }, format='json')
        
        # Get cart to find item ID
        cart_url = '/api/v1/cart/'
        response = self.client.get(cart_url)
        item_id = response.data['items'][0]['id']
        
        # Update quantity
        update_url = f'/api/v1/cart/items/{item_id}/'
        response = self.client.patch(update_url, {
            'quantity': 5
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 5)
    
    def test_remove_cart_item(self):
        """Test removing item from cart."""
        # Add item first
        add_url = '/api/v1/cart/items/'
        self.client.post(add_url, {
            'variant_id': self.variant1.id,
            'quantity': 2
        }, format='json')
        
        # Get cart to find item ID
        cart_url = '/api/v1/cart/'
        response = self.client.get(cart_url)
        item_id = response.data['items'][0]['id']
        
        # Remove item
        remove_url = f'/api/v1/cart/items/{item_id}/'
        response = self.client.delete(remove_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cart is empty
        response = self.client.get(cart_url)
        self.assertEqual(response.data['item_count'], 0)
    
    def test_clear_cart(self):
        """Test clearing cart."""
        # Add multiple items
        add_url = '/api/v1/cart/items/'
        self.client.post(add_url, {
            'variant_id': self.variant1.id,
            'quantity': 2
        }, format='json')
        self.client.post(add_url, {
            'variant_id': self.variant2.id,
            'quantity': 1
        }, format='json')
        
        # Clear cart
        clear_url = '/api/v1/cart/'
        response = self.client.delete(clear_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cart is empty
        response = self.client.get(clear_url)
        self.assertEqual(response.data['item_count'], 0)
        self.assertEqual(len(response.data['items']), 0)


class CheckoutTest(CartAPITestCase):
    """Test checkout and order creation."""
    
    def test_checkout_creates_order(self):
        """Test successful checkout creates order."""
        # Add item to cart
        add_url = '/api/v1/cart/items/'
        self.client.post(add_url, {
            'variant_id': self.variant1.id,
            'quantity': 2
        }, format='json')
        
        # Checkout
        checkout_url = '/api/v1/checkout/'
        checkout_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'customer_phone': '01712345678',
            'shipping_address_line1': '123 Main Street',
            'shipping_address_line2': 'Apt 4B',
            'shipping_city': 'Dhaka',
            'shipping_area': 'Gulshan',
            'shipping_postal_code': '1212',
            'shipping_zone_id': self.shipping_zone.id,
            'payment_method': 'cod',
            'customer_notes': 'Please deliver in the evening'
        }
        response = self.client.post(checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order_number', response.data)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['payment_method'], 'cod')
        self.assertEqual(len(response.data['items']), 1)
        
        # Verify cart is cleared
        cart_url = '/api/v1/cart/'
        cart_response = self.client.get(cart_url)
        self.assertEqual(cart_response.data['item_count'], 0)
    
    def test_checkout_empty_cart_fails(self):
        """Test checkout with empty cart fails."""
        checkout_url = '/api/v1/checkout/'
        checkout_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'customer_phone': '01712345678',
            'shipping_address_line1': '123 Main Street',
            'shipping_city': 'Dhaka',
            'shipping_area': 'Gulshan',
            'shipping_zone_id': self.shipping_zone.id,
            'payment_method': 'cod',
        }
        response = self.client.post(checkout_url, checkout_data, format='json')
        
        # Should return 400 for empty cart
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_checkout_with_coupon(self):
        """Test checkout with valid coupon applies discount."""
        # Add item to cart
        add_url = '/api/v1/cart/items/'
        self.client.post(add_url, {
            'variant_id': self.variant1.id,
            'quantity': 1  # 10000.00
        }, format='json')
        
        # Checkout with coupon
        checkout_url = '/api/v1/checkout/'
        checkout_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'customer_phone': '01712345678',
            'shipping_address_line1': '123 Main Street',
            'shipping_city': 'Dhaka',
            'shipping_area': 'Gulshan',
            'shipping_zone_id': self.shipping_zone.id,
            'payment_method': 'cod',
            'coupon_code': 'SAVE10'
        }
        response = self.client.post(checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['coupon_code'], 'SAVE10')
        self.assertGreater(float(response.data['discount_amount']), 0)
    
    def test_checkout_invalid_coupon_fails(self):
        """Test checkout with invalid coupon fails."""
        # Add item to cart
        add_url = '/api/v1/cart/items/'
        self.client.post(add_url, {
            'variant_id': self.variant1.id,
            'quantity': 1
        }, format='json')
        
        # Checkout with invalid coupon
        checkout_url = '/api/v1/checkout/'
        checkout_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'customer_phone': '01712345678',
            'shipping_address_line1': '123 Main Street',
            'shipping_city': 'Dhaka',
            'shipping_area': 'Gulshan',
            'shipping_zone_id': self.shipping_zone.id,
            'payment_method': 'cod',
            'coupon_code': 'INVALID123'
        }
        response = self.client.post(checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('coupon_code', response.data)


class CouponValidationTest(CartAPITestCase):
    """Test coupon validation."""
    
    def test_validate_valid_coupon(self):
        """Test validating valid coupon."""
        url = '/api/v1/coupons/validate/'
        data = {
            'code': 'SAVE10',
            'cart_total': '10000.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertIn('discount_amount', response.data['coupon'])
    
    def test_validate_invalid_coupon(self):
        """Test validating invalid coupon."""
        url = '/api/v1/coupons/validate/'
        data = {
            'code': 'NOTEXIST',
            'cart_total': '10000.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])
    
    def test_validate_expired_coupon(self):
        """Test validating expired coupon."""
        # Create expired coupon
        expired_coupon = Coupon.objects.create(
            code="EXPIRED",
            name="Expired Coupon",
            discount_type="percentage",
            discount_value=Decimal("20.00"),
            valid_from=timezone.now() - timedelta(days=30),
            valid_to=timezone.now() - timedelta(days=1),
            is_active=True
        )
        
        url = '/api/v1/coupons/validate/'
        data = {
            'code': 'EXPIRED',
            'cart_total': '10000.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])
    
    def test_validate_coupon_below_minimum(self):
        """Test validating coupon with cart below minimum."""
        url = '/api/v1/coupons/validate/'
        data = {
            'code': 'SAVE10',
            'cart_total': '1000.00'  # Below minimum of 5000
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])


class ShippingTest(CartAPITestCase):
    """Test shipping zones and calculation."""
    
    def test_list_shipping_zones(self):
        """Test listing active shipping zones."""
        url = '/api/v1/shipping/zones/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Dhaka')
    
    def test_calculate_shipping_below_threshold(self):
        """Test shipping calculation below free shipping threshold."""
        url = '/api/v1/shipping/calculate/'
        data = {
            'shipping_zone_id': self.shipping_zone.id,
            'cart_total': '10000.00'  # Below 20000 threshold
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['shipping_cost'], '100.00')
        self.assertFalse(response.data['is_free_shipping'])
    
    def test_calculate_shipping_above_threshold(self):
        """Test free shipping above threshold."""
        url = '/api/v1/shipping/calculate/'
        data = {
            'shipping_zone_id': self.shipping_zone.id,
            'cart_total': '25000.00'  # Above 20000 threshold
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['shipping_cost'], '0.00')
        self.assertTrue(response.data['is_free_shipping'])
    
    def test_calculate_shipping_invalid_zone(self):
        """Test shipping calculation with invalid zone."""
        url = '/api/v1/shipping/calculate/'
        data = {
            'shipping_zone_id': 99999,
            'cart_total': '10000.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
