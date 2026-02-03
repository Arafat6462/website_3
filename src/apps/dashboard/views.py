"""
Dashboard views for admin interface.

This module provides custom dashboard views and callbacks for the
Django Unfold admin interface, displaying key metrics and statistics.
"""

from typing import List, Dict, Any

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render

from .services import DashboardService


def dashboard_callback(request, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Dashboard callback for Django Unfold admin.
    
    This function is called by Unfold to render dashboard widgets.
    Returns a list of widget configurations with data.
    
    Args:
        request: HTTP request object
        context: Context dictionary from admin
        
    Returns:
        list: List of widget dictionaries for rendering
    """
    # Get statistics
    today_stats = DashboardService.get_today_stats()
    abandoned_carts = DashboardService.get_abandoned_carts()
    revenue_chart = DashboardService.get_revenue_chart(days=7)
    low_stock = DashboardService.get_low_stock_alerts(limit=5)
    recent_orders = DashboardService.get_recent_orders(limit=5)
    
    widgets = []
    
    # Row 1: Key Metrics Cards
    widgets.append({
        "type": "metric",
        "title": "Today's Orders",
        "value": today_stats['orders_count'],
        "change": today_stats['orders_change'],
        "icon": "shopping_bag",
        "color": "primary",
    })
    
    widgets.append({
        "type": "metric",
        "title": "Today's Revenue",
        "value": f"৳{today_stats['revenue']:,.2f}",
        "change": today_stats['revenue_change'],
        "icon": "payments",
        "color": "success",
    })
    
    widgets.append({
        "type": "metric",
        "title": "New Customers",
        "value": today_stats['new_customers'],
        "change": today_stats['customers_change'],
        "icon": "person_add",
        "color": "info",
    })
    
    widgets.append({
        "type": "metric",
        "title": "Pending Reviews",
        "value": today_stats['pending_reviews'],
        "icon": "rate_review",
        "color": "warning",
    })
    
    # Row 2: Charts and Lists
    widgets.append({
        "type": "chart",
        "title": "Revenue (Last 7 Days)",
        "chart_type": "bar",
        "data": {
            "labels": revenue_chart['labels'],
            "datasets": [{
                "label": "Revenue",
                "data": revenue_chart['data'],
            }],
        },
        "width": 8,  # 2/3 width
    })
    
    widgets.append({
        "type": "list",
        "title": "Low Stock Alerts",
        "items": [
            {
                "title": item['variant_name'],
                "subtitle": f"Stock: {item['stock_quantity']} (SKU: {item['sku']})",
                "badge": "⚠️" if item['stock_quantity'] == 0 else "📦",
            }
            for item in low_stock
        ],
        "width": 4,  # 1/3 width
    })
    
    # Row 3: Recent Orders Table
    widgets.append({
        "type": "table",
        "title": "Recent Orders",
        "headers": ["Order #", "Customer", "Phone", "Status", "Amount"],
        "rows": [
            [
                order['order_number'],
                order['customer_name'],
                order['customer_phone'],
                order['status'].title(),
                f"৳{order['total']:,.2f}",
            ]
            for order in recent_orders
        ],
        "width": 12,  # Full width
    })
    
    # Row 4: Abandoned Carts
    widgets.append({
        "type": "metric",
        "title": "Abandoned Carts",
        "value": abandoned_carts['count'],
        "subtitle": f"Potential Revenue: ৳{abandoned_carts['potential_revenue']:,.2f}",
        "icon": "remove_shopping_cart",
        "color": "error",
        "width": 6,
    })
    
    return widgets


@staff_member_required
def dashboard_ajax(request):
    """
    AJAX endpoint for refreshing dashboard data.
    
    Returns JSON data for dynamic dashboard updates without page reload.
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse: Dashboard statistics as JSON
    """
    today_stats = DashboardService.get_today_stats()
    abandoned_carts = DashboardService.get_abandoned_carts()
    revenue_chart = DashboardService.get_revenue_chart(days=7)
    low_stock = DashboardService.get_low_stock_alerts(limit=10)
    recent_orders = DashboardService.get_recent_orders(limit=10)
    
    return JsonResponse({
        'today_stats': {
            'orders_count': today_stats['orders_count'],
            'orders_change': today_stats['orders_change'],
            'revenue': float(today_stats['revenue']),
            'revenue_change': today_stats['revenue_change'],
            'new_customers': today_stats['new_customers'],
            'customers_change': today_stats['customers_change'],
            'pending_reviews': today_stats['pending_reviews'],
        },
        'abandoned_carts': {
            'count': abandoned_carts['count'],
            'potential_revenue': float(abandoned_carts['potential_revenue']),
        },
        'revenue_chart': revenue_chart,
        'low_stock': low_stock,
        'recent_orders': [
            {
                'order_number': order['order_number'],
                'customer_name': order['customer_name'],
                'customer_phone': order['customer_phone'],
                'status': order['status'],
                'total': float(order['total']),
                'created_at': order['created_at'].isoformat(),
            }
            for order in recent_orders
        ],
    })


@staff_member_required
def analytics_view(request):
    """
    Detailed analytics API endpoint.
    
    Provides deeper insights with charts and reports beyond the dashboard.
    Returns JSON data for analytics page.
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse: Analytics data
    """
    revenue_30_days = DashboardService.get_revenue_chart(days=30)
    sales_by_status = DashboardService.get_sales_by_status()
    top_products = DashboardService.get_top_selling_products(limit=10)
    
    return JsonResponse({
        'revenue_30_days': revenue_30_days,
        'sales_by_status': sales_by_status,
        'top_products': [
            {
                'product_name': p['product_name'],
                'variant_name': p['variant_name'],
                'quantity_sold': p['quantity_sold'],
                'revenue': float(p['revenue']),
            }
            for p in top_products
        ],
    })
