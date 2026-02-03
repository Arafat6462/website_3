"""
Dashboard service for generating admin statistics and analytics.

This module provides methods to calculate and retrieve dashboard metrics
including orders, revenue, customer statistics, and inventory alerts.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.orders.models import Order, Cart, CartItem
from apps.products.models import ProductVariant
from apps.engagement.models import ProductReview

User = get_user_model()


class DashboardService:
    """
    Service for dashboard statistics and analytics.
    
    Provides methods to calculate key business metrics for the admin dashboard
    including sales, revenue, customer stats, inventory alerts, and trends.
    """
    
    @staticmethod
    def get_today_stats() -> Dict[str, Any]:
        """
        Get today's key statistics.
        
        Returns:
            dict: Dictionary containing:
                - orders_count: Number of orders today
                - orders_change: Percentage change vs yesterday
                - revenue: Total revenue today
                - revenue_change: Percentage change vs yesterday
                - new_customers: New users registered today
                - customers_change: Percentage change vs yesterday
                - pending_reviews: Count of unapproved reviews
        """
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Today's orders
        today_orders = Order.objects.filter(
            created_at__date=today,
            is_deleted=False
        ).count()
        
        yesterday_orders = Order.objects.filter(
            created_at__date=yesterday,
            is_deleted=False
        ).count()
        
        orders_change = DashboardService._calculate_percentage_change(
            yesterday_orders, today_orders
        )
        
        # Today's revenue
        today_revenue = Order.objects.filter(
            created_at__date=today,
            is_deleted=False,
            status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        
        yesterday_revenue = Order.objects.filter(
            created_at__date=yesterday,
            is_deleted=False,
            status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        
        revenue_change = DashboardService._calculate_percentage_change(
            float(yesterday_revenue), float(today_revenue)
        )
        
        # New customers today
        today_customers = User.objects.filter(
            date_joined__date=today,
            is_staff=False
        ).count()
        
        yesterday_customers = User.objects.filter(
            date_joined__date=yesterday,
            is_staff=False
        ).count()
        
        customers_change = DashboardService._calculate_percentage_change(
            yesterday_customers, today_customers
        )
        
        # Pending reviews
        pending_reviews = ProductReview.objects.filter(
            is_approved=False
        ).count()
        
        return {
            'orders_count': today_orders,
            'orders_change': orders_change,
            'revenue': today_revenue,
            'revenue_change': revenue_change,
            'new_customers': today_customers,
            'customers_change': customers_change,
            'pending_reviews': pending_reviews,
        }
    
    @staticmethod
    def get_abandoned_carts() -> Dict[str, Any]:
        """
        Get abandoned cart statistics.
        
        Carts are considered abandoned if:
        - They have items
        - No associated order
        - Created more than 24 hours ago
        
        Returns:
            dict: Dictionary containing:
                - count: Number of abandoned carts
                - potential_revenue: Sum of all cart totals
        """
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        # Get carts with items, no order, older than 24h
        abandoned_carts = Cart.objects.filter(
            created_at__lt=cutoff_time
        ).annotate(
            items_count=Count('items')
        ).filter(
            items_count__gt=0
        )
        
        # Calculate potential revenue
        potential_revenue = Decimal('0.00')
        for cart in abandoned_carts:
            cart_total = cart.items.aggregate(
                total=Sum(F('quantity') * F('unit_price'))
            )['total'] or Decimal('0.00')
            potential_revenue += cart_total
        
        return {
            'count': abandoned_carts.count(),
            'potential_revenue': potential_revenue,
        }
    
    @staticmethod
    def get_revenue_chart(days: int = 7) -> Dict[str, List]:
        """
        Get daily revenue data for chart.
        
        Args:
            days: Number of days to include (default 7)
            
        Returns:
            dict: Dictionary containing:
                - labels: List of date labels
                - data: List of revenue amounts
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days - 1)
        
        labels = []
        data = []
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            
            # Get revenue for this date
            revenue = Order.objects.filter(
                created_at__date=date,
                is_deleted=False,
                status__in=['confirmed', 'processing', 'shipped', 'delivered']
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            
            labels.append(date.strftime('%a'))  # Mon, Tue, etc.
            data.append(float(revenue))
        
        return {
            'labels': labels,
            'data': data,
        }
    
    @staticmethod
    def get_low_stock_alerts(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get products with low stock levels.
        
        Returns variants where stock_quantity <= low_stock_threshold.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            list: List of dictionaries containing:
                - variant_id: Variant ID
                - variant_name: Full product + variant name
                - sku: Stock keeping unit
                - stock_quantity: Current stock
                - low_stock_threshold: Alert threshold
        """
        low_stock_variants = ProductVariant.objects.filter(
            is_active=True,
            is_deleted=False,
            stock_quantity__lte=F('low_stock_threshold')
        ).select_related('product').order_by('stock_quantity')[:limit]
        
        alerts = []
        for variant in low_stock_variants:
            alerts.append({
                'variant_id': variant.id,
                'variant_name': f"{variant.product.name} - {variant.name}",
                'sku': variant.sku,
                'stock_quantity': variant.stock_quantity,
                'low_stock_threshold': variant.low_stock_threshold,
            })
        
        return alerts
    
    @staticmethod
    def get_recent_orders(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent orders.
        
        Args:
            limit: Maximum number of orders to return
            
        Returns:
            list: List of dictionaries containing order details
        """
        orders = Order.objects.filter(
            is_deleted=False
        ).select_related('user').order_by('-created_at')[:limit]
        
        recent_orders = []
        for order in orders:
            recent_orders.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'customer_phone': order.customer_phone,
                'status': order.status,
                'payment_status': order.payment_status,
                'total': order.total,
                'created_at': order.created_at,
            })
        
        return recent_orders
    
    @staticmethod
    def get_sales_by_status() -> Dict[str, int]:
        """
        Get order count by status.
        
        Returns:
            dict: Dictionary mapping status to count
        """
        status_counts = Order.objects.filter(
            is_deleted=False
        ).values('status').annotate(
            count=Count('id')
        )
        
        result = {}
        for item in status_counts:
            result[item['status']] = item['count']
        
        return result
    
    @staticmethod
    def get_top_selling_products(limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top selling products by quantity sold.
        
        Args:
            limit: Number of products to return
            
        Returns:
            list: List of dictionaries containing:
                - product_name: Product name
                - variant_name: Variant name
                - quantity_sold: Total quantity
                - revenue: Total revenue
        """
        from apps.orders.models import OrderItem
        
        top_products = OrderItem.objects.filter(
            order__is_deleted=False,
            order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).values(
            'product_name', 'variant_name'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-quantity_sold')[:limit]
        
        return list(top_products)
    
    @staticmethod
    def _calculate_percentage_change(old_value: float, new_value: float) -> float:
        """
        Calculate percentage change between two values.
        
        Args:
            old_value: Previous value
            new_value: Current value
            
        Returns:
            float: Percentage change (positive or negative)
        """
        if old_value == 0:
            if new_value == 0:
                return 0.0
            return 100.0  # Infinite increase
        
        change = ((new_value - old_value) / old_value) * 100
        return round(change, 1)
