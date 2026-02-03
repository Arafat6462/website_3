"""Tests for user management API endpoints.

Tests profile, addresses, orders, wishlist, and reviews.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from apps.users.models import CustomerAddress
from apps.products.models import Category, ProductType, Product, ProductVariant
from apps.orders.models import Order, OrderItem, ShippingZone
from apps.engagement.models import Wishlist, WishlistItem, ProductReview

User = get_user_model()


class UserAPITestCase(TestCase):
    """Base test case for user management tests."""
    
    def setUp(self):
        """Set up test client, user, and test data."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            phone='01712345678',
            first_name='Test',
            last_name='User',
            password='Test@123456'
        )
        
        # Create product for testing
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product_type = ProductType.objects.create(name='Test Type', slug='test-type')
        self.product = Product.objects.create(
            product_type=self.product_type,
            category=self.category,
            name='Test Product',
            slug='test-product',
            base_price=Decimal('1000.00'),
            status='published'
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='TEST-001',
            name='Default',
            price=Decimal('1000.00'),
            stock_quantity=50,
            is_default=True
        )
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)


class UserProfileTest(UserAPITestCase):
    """Test user profile endpoints."""
    
    def test_get_profile(self):
        """Test getting user profile."""
        url = '/api/v1/users/me/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
    
    def test_update_profile(self):
        """Test updating user profile."""
        url = '/api/v1/users/me/'
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '01798765432',
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        self.assertEqual(response.data['phone'], '01798765432')


class AddressManagementTest(UserAPITestCase):
    """Test address management endpoints."""
    
    def test_list_addresses(self):
        """Test listing user addresses."""
        # Create test address
        CustomerAddress.objects.create(
            user=self.user,
            label='Home',
            recipient_name='Test User',
            phone='01712345678',
            address_line1='123 Main St',
            city='Dhaka',
            area='Gulshan',
            is_default=True
        )
        
        url = '/api/v1/users/me/addresses/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['label'], 'Home')
    
    def test_create_address(self):
        """Test creating new address."""
        url = '/api/v1/users/me/addresses/'
        data = {
            'label': 'Office',
            'recipient_name': 'Test User',
            'phone': '01712345678',
            'address_line1': '456 Office St',
            'city': 'Dhaka',
            'area': 'Banani',
            'is_default': False,
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['label'], 'Office')
    
    def test_update_address(self):
        """Test updating address."""
        address = CustomerAddress.objects.create(
            user=self.user,
            label='Home',
            recipient_name='Test User',
            phone='01712345678',
            address_line1='123 Main St',
            city='Dhaka',
            area='Gulshan'
        )
        
        url = f'/api/v1/users/me/addresses/{address.id}/'
        data = {'label': 'Home (Updated)'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['label'], 'Home (Updated)')
    
    def test_delete_address(self):
        """Test deleting address."""
        address = CustomerAddress.objects.create(
            user=self.user,
            label='Temporary',
            recipient_name='Test User',
            phone='01712345678',
            address_line1='789 Temp St',
            city='Dhaka',
            area='Dhanmondi'
        )
        
        url = f'/api/v1/users/me/addresses/{address.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CustomerAddress.objects.filter(id=address.id).exists())


class OrderManagementTest(UserAPITestCase):
    """Test order management endpoints."""
    
    def test_list_user_orders(self):
        """Test listing user orders."""
        # Create test order
        shipping_zone = ShippingZone.objects.create(
            name='Dhaka',
            areas=['Gulshan', 'Banani'],
            shipping_cost=Decimal('100.00')
        )
        
        order = Order.objects.create(
            user=self.user,
            order_number='ORD-2026-00001',
            shipping_zone=shipping_zone,
            customer_name='Test User',
            customer_email='test@example.com',
            customer_phone='01712345678',
            shipping_address_line1='123 Main St',
            shipping_city='Dhaka',
            shipping_area='Gulshan',
            status='pending',
            subtotal=Decimal('1000.00'),
            shipping_cost=Decimal('100.00'),
            total=Decimal('1100.00'),
            payment_method='cod',
            payment_status='pending'
        )
        
        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            product_name='Test Product',
            variant_name='Default',
            sku='TEST-001',
            unit_price=Decimal('1000.00'),
            quantity=1,
            line_total=Decimal('1000.00')
        )
        
        url = '/api/v1/users/me/orders/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['order_number'], 'ORD-2026-00001')
    
    def test_get_order_detail(self):
        """Test getting single order details."""
        shipping_zone = ShippingZone.objects.create(
            name='Dhaka',
            areas=['Gulshan'],
            shipping_cost=Decimal('100.00')
        )
        
        order = Order.objects.create(
            user=self.user,
            order_number='ORD-2026-00002',
            shipping_zone=shipping_zone,
            customer_name='Test User',
            customer_email='test@example.com',
            customer_phone='01712345678',
            shipping_address_line1='123 Main St',
            shipping_city='Dhaka',
            shipping_area='Gulshan',
            status='confirmed',
            subtotal=Decimal('1000.00'),
            shipping_cost=Decimal('100.00'),
            total=Decimal('1100.00'),
            payment_method='cod',
            payment_status='pending'
        )
        
        url = f'/api/v1/users/me/orders/{order.order_number}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], 'ORD-2026-00002')
        self.assertEqual(response.data['status'], 'confirmed')


class WishlistTest(UserAPITestCase):
    """Test wishlist endpoints."""
    
    def test_get_empty_wishlist(self):
        """Test getting empty wishlist."""
        url = '/api/v1/users/me/wishlist/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_add_to_wishlist(self):
        """Test adding item to wishlist."""
        url = '/api/v1/users/me/wishlist/toggle/'
        data = {'variant_id': self.variant.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['action'], 'added')
        self.assertTrue(response.data['in_wishlist'])
    
    def test_remove_from_wishlist(self):
        """Test removing item from wishlist."""
        # Add item first
        wishlist, _ = Wishlist.objects.get_or_create(user=self.user)
        WishlistItem.objects.create(wishlist=wishlist, variant=self.variant)
        
        url = '/api/v1/users/me/wishlist/toggle/'
        data = {'variant_id': self.variant.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'removed')
        self.assertFalse(response.data['in_wishlist'])


class ProductReviewTest(UserAPITestCase):
    """Test product review endpoints."""
    
    def test_submit_review(self):
        """Test submitting product review."""
        url = '/api/v1/users/me/reviews/'
        data = {
            'product': self.product.id,
            'rating': 5,
            'comment': 'Great product!',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 5)
        self.assertEqual(response.data['comment'], 'Great product!')
    
    def test_submit_duplicate_review(self):
        """Test submitting duplicate review."""
        # Create first review
        ProductReview.objects.create(
            user=self.user,
            product=self.product,
            rating=4,
            comment='First review'
        )
        
        url = '/api/v1/users/me/reviews/'
        data = {
            'product': self.product.id,
            'rating': 5,
            'comment': 'Second review',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderTrackingTest(TestCase):
    """Test public order tracking endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create guest order
        shipping_zone = ShippingZone.objects.create(
            name='Dhaka',
            areas=['Gulshan'],
            shipping_cost=Decimal('100.00')
        )
        
        self.order = Order.objects.create(
            order_number='ORD-2026-00003',
            shipping_zone=shipping_zone,
            customer_name='Guest User',
            customer_email='guest@example.com',
            customer_phone='01712345678',
            shipping_address_line1='123 Main St',
            shipping_city='Dhaka',
            shipping_area='Gulshan',
            status='shipped',
            subtotal=Decimal('1000.00'),
            shipping_cost=Decimal('100.00'),
            total=Decimal('1100.00'),
            payment_method='cod',
            payment_status='pending',
            tracking_number='TRACK123',
            courier_name='Test Courier'
        )
    
    def test_track_order(self):
        """Test tracking order with correct credentials."""
        url = '/api/v1/users/orders/track/'
        data = {
            'order_number': 'ORD-2026-00003',
            'phone': '01712345678',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], 'ORD-2026-00003')
        self.assertEqual(response.data['status'], 'shipped')
        self.assertEqual(response.data['tracking_number'], 'TRACK123')
    
    def test_track_order_wrong_phone(self):
        """Test tracking order with wrong phone."""
        url = '/api/v1/users/orders/track/'
        data = {
            'order_number': 'ORD-2026-00003',
            'phone': '01798765432',  # Wrong phone
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
