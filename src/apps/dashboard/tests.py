"""
Tests for dashboard app.

This module tests dashboard services, views, and statistics calculations.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.dashboard.services import DashboardService
from apps.orders.models import Order, Cart, CartItem
from apps.products.models import (
    Category,
    Product,
    ProductType,
    ProductVariant,
)
from apps.engagement.models import ProductReview

User = get_user_model()


class DashboardServiceTest(TestCase):
    """Test DashboardService methods."""
    
    def setUp(self):
        """Set up test data."""
        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            phone='01712345678',
            password='testpass123'
        )
        
        # Create product setup
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            status='active'
        )
        
        self.product_type = ProductType.objects.create(
            name='Test Type',
            slug='test-type',
            is_active=True
        )
        
        self.product = Product.objects.create(
            product_type=self.product_type,
            category=self.category,
            name='Test Product',
            slug='test-product',
            base_price=Decimal('100.00'),
            status='published'
        )
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='TEST-001',
            name='Default',
            price=Decimal('100.00'),
            stock_quantity=5,
            low_stock_threshold=10,
            is_active=True
        )
    
    def test_get_today_stats(self):
        """Test today's statistics calculation."""
        # Create today's order
        order = Order.objects.create(
            user=self.user,
            customer_name='Test Customer',
            customer_email='test@example.com',
            customer_phone='01712345678',
            shipping_address_line1='123 Test St',
            shipping_city='Dhaka',
            shipping_area='Gulshan',
            status='confirmed',
            payment_method='cod',
            payment_status='pending',
            subtotal=Decimal('100.00'),
            total=Decimal('100.00')
        )
        
        stats = DashboardService.get_today_stats()
        
        self.assertEqual(stats['orders_count'], 1)
        self.assertEqual(stats['revenue'], Decimal('100.00'))
        self.assertIsInstance(stats['new_customers'], int)
        self.assertIsInstance(stats['pending_reviews'], int)
    
    def test_get_abandoned_carts(self):
        """Test abandoned cart statistics."""
        # Create cart older than 24 hours
        old_time = timezone.now() - timedelta(hours=25)
        cart = Cart.objects.create(
            user=self.user,
            expires_at=old_time + timedelta(days=30)
        )
        cart.created_at = old_time
        cart.save()
        
        # Add item to cart
        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=2,
            unit_price=Decimal('100.00')
        )
        
        abandoned = DashboardService.get_abandoned_carts()
        
        self.assertEqual(abandoned['count'], 1)
        self.assertEqual(abandoned['potential_revenue'], Decimal('200.00'))
    
    def test_get_revenue_chart(self):
        """Test revenue chart data generation."""
        # Create order
        Order.objects.create(
            user=self.user,
            customer_name='Test Customer',
            customer_email='test@example.com',
            customer_phone='01712345678',
            shipping_address_line1='123 Test St',
            shipping_city='Dhaka',
            shipping_area='Gulshan',
            status='confirmed',
            payment_method='cod',
            payment_status='pending',
            subtotal=Decimal('100.00'),
            total=Decimal('100.00')
        )
        
        chart_data = DashboardService.get_revenue_chart(days=7)
        
        self.assertIn('labels', chart_data)
        self.assertIn('data', chart_data)
        self.assertEqual(len(chart_data['labels']), 7)
        self.assertEqual(len(chart_data['data']), 7)
    
    def test_get_low_stock_alerts(self):
        """Test low stock alerts."""
        # Variant already has stock (5) <= threshold (10)
        alerts = DashboardService.get_low_stock_alerts(limit=10)
        
        self.assertGreater(len(alerts), 0)
        self.assertEqual(alerts[0]['sku'], 'TEST-001')
        self.assertEqual(alerts[0]['stock_quantity'], 5)
    
    def test_get_recent_orders(self):
        """Test recent orders retrieval."""
        # Create order
        Order.objects.create(
            user=self.user,
            customer_name='Test Customer',
            customer_email='test@example.com',
            customer_phone='01712345678',
            shipping_address_line1='123 Test St',
            shipping_city='Dhaka',
            shipping_area='Gulshan',
            status='pending',
            payment_method='cod',
            payment_status='pending',
            subtotal=Decimal('100.00'),
            total=Decimal('100.00')
        )
        
        recent = DashboardService.get_recent_orders(limit=10)
        
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]['customer_name'], 'Test Customer')
    
    def test_get_sales_by_status(self):
        """Test sales grouped by status."""
        # Create orders with different statuses
        Order.objects.create(
            user=self.user,
            customer_name='Test Customer 1',
            customer_email='test1@example.com',
            customer_phone='01712345678',
            shipping_address_line1='123 Test St',
            shipping_city='Dhaka',
            shipping_area='Gulshan',
            status='pending',
            payment_method='cod',
            payment_status='pending',
            subtotal=Decimal('100.00'),
            total=Decimal('100.00')
        )
        
        Order.objects.create(
            user=self.user,
            customer_name='Test Customer 2',
            customer_email='test2@example.com',
            customer_phone='01812345678',
            shipping_address_line1='456 Test St',
            shipping_city='Dhaka',
            shipping_area='Dhanmondi',
            status='confirmed',
            payment_method='cod',
            payment_status='pending',
            subtotal=Decimal('200.00'),
            total=Decimal('200.00')
        )
        
        sales_by_status = DashboardService.get_sales_by_status()
        
        self.assertEqual(sales_by_status['pending'], 1)
        self.assertEqual(sales_by_status['confirmed'], 1)
    
    def test_get_top_selling_products(self):
        """Test top selling products calculation."""
        from apps.orders.models import OrderItem
        
        # Create order with items
        order = Order.objects.create(
            user=self.user,
            customer_name='Test Customer',
            customer_email='test@example.com',
            customer_phone='01712345678',
            shipping_address_line1='123 Test St',
            shipping_city='Dhaka',
            shipping_area='Gulshan',
            status='delivered',
            payment_method='cod',
            payment_status='paid',
            subtotal=Decimal('200.00'),
            total=Decimal('200.00')
        )
        
        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            product_name='Test Product',
            variant_name='Default',
            sku='TEST-001',
            unit_price=Decimal('100.00'),
            quantity=2
        )
        
        top_products = DashboardService.get_top_selling_products(limit=5)
        
        self.assertEqual(len(top_products), 1)
        self.assertEqual(top_products[0]['quantity_sold'], 2)
        self.assertEqual(top_products[0]['revenue'], Decimal('200.00'))
    
    def test_calculate_percentage_change(self):
        """Test percentage change calculation."""
        # Increase
        change = DashboardService._calculate_percentage_change(100, 150)
        self.assertEqual(change, 50.0)
        
        # Decrease
        change = DashboardService._calculate_percentage_change(100, 50)
        self.assertEqual(change, -50.0)
        
        # No change
        change = DashboardService._calculate_percentage_change(100, 100)
        self.assertEqual(change, 0.0)
        
        # From zero
        change = DashboardService._calculate_percentage_change(0, 100)
        self.assertEqual(change, 100.0)


class DashboardViewTest(TestCase):
    """Test dashboard views."""
    
    def setUp(self):
        """Set up test client and staff user."""
        self.client = Client()
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            phone='01712345679',
            password='staffpass123',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            phone='01712345680',
            password='userpass123'
        )
    
    def test_dashboard_ajax_requires_staff(self):
        """Test dashboard AJAX endpoint requires staff permission."""
        url = reverse('dashboard:ajax')
        
        # Anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Regular user
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect (not staff)
        
        # Staff user
        self.client.login(email='staff@example.com', password='staffpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_ajax_returns_json(self):
        """Test dashboard AJAX returns JSON data."""
        self.client.login(email='staff@example.com', password='staffpass123')
        url = reverse('dashboard:ajax')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check structure
        self.assertIn('today_stats', data)
        self.assertIn('abandoned_carts', data)
        self.assertIn('revenue_chart', data)
        self.assertIn('low_stock', data)
        self.assertIn('recent_orders', data)
    
    def test_analytics_view_requires_staff(self):
        """Test analytics view requires staff permission."""
        url = reverse('dashboard:analytics')
        
        # Anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        # Regular user
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        # Staff user
        self.client.login(email='staff@example.com', password='staffpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
