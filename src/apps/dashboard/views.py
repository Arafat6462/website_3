"""
Dashboard views for admin interface.

This module provides custom dashboard views and callbacks for the
Django Unfold admin interface, displaying key metrics and statistics.
"""

from typing import Dict, Any

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse

from .services import DashboardService


def dashboard_callback(request, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dashboard callback for Django Unfold admin.
    
    This function is called by Unfold to render dashboard widgets.
    Updates the context with dashboard data.
    
    Args:
        request: HTTP request object
        context: Context dictionary from admin
        
    Returns:
        dict: Updated context dictionary with dashboard data
    """
    # Get statistics
    today_stats = DashboardService.get_today_stats()
    abandoned_carts = DashboardService.get_abandoned_carts()
    revenue_chart = DashboardService.get_revenue_chart(days=7)
    low_stock = DashboardService.get_low_stock_alerts(limit=5)
    recent_orders = DashboardService.get_recent_orders(limit=5)
    
    # Add dashboard data to context
    context.update({
        'dashboard_stats': {
            'today': today_stats,
            'abandoned_carts': abandoned_carts,
            'revenue_chart': revenue_chart,
            'low_stock': low_stock,
            'recent_orders': recent_orders,
        }
    })
    
    return context


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

