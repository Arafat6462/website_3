"""API v1 URLs.

Main URL configuration for API version 1.
"""

from django.urls import path, include
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def api_root(request):
    """API root endpoint.
    
    Returns available API endpoints and version info.
    """
    return Response({
        'version': '1.0',
        'endpoints': {
            # Authentication
            'auth-register': request.build_absolute_uri('auth/register/'),
            'auth-login': request.build_absolute_uri('auth/login/'),
            'auth-logout': request.build_absolute_uri('auth/logout/'),
            'auth-token-refresh': request.build_absolute_uri('auth/token/refresh/'),
            'auth-password-reset': request.build_absolute_uri('auth/password-reset/'),
            
            # Products
            'products': request.build_absolute_uri('products/'),
            'categories': request.build_absolute_uri('categories/'),
            'product-types': request.build_absolute_uri('product-types/'),
            
            # Cart & Checkout
            'cart': request.build_absolute_uri('cart/'),
            'checkout': request.build_absolute_uri('checkout/'),
            'shipping-zones': request.build_absolute_uri('shipping/zones/'),
            
            # User
            'user-profile': request.build_absolute_uri('users/me/'),
            'user-addresses': request.build_absolute_uri('users/me/addresses/'),
            'user-orders': request.build_absolute_uri('users/me/orders/'),
            'user-wishlist': request.build_absolute_uri('users/me/wishlist/'),
            'order-tracking': request.build_absolute_uri('users/orders/track/'),
            
            # System
            'health': request.build_absolute_uri('health/'),
        }
    })


@api_view(['GET'])
def health_check(request):
    """Comprehensive health check endpoint.
    
    Checks database, cache, and storage connectivity.
    Returns detailed system status.
    
    Returns:
        Response: Health status with component details
            - HTTP 200: All systems healthy
            - HTTP 503: One or more systems unhealthy
    """
    from django.db import connection
    from django.core.cache import cache
    from django.core.files.storage import default_storage
    import time
    
    health_status = {
        'status': 'healthy',
        'version': '1.0',
        'api': 'v1',
        'timestamp': time.time(),
        'checks': {}
    }
    
    overall_healthy = True
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        overall_healthy = False
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database error: {str(e)}'
        }
    
    # Cache check (Redis)
    try:
        cache_key = 'health_check_test'
        cache_value = 'ok'
        cache.set(cache_key, cache_value, timeout=10)
        retrieved_value = cache.get(cache_key)
        
        if retrieved_value == cache_value:
            health_status['checks']['cache'] = {
                'status': 'healthy',
                'message': 'Cache connection successful'
            }
        else:
            overall_healthy = False
            health_status['checks']['cache'] = {
                'status': 'unhealthy',
                'message': 'Cache read/write mismatch'
            }
    except Exception as e:
        overall_healthy = False
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'message': f'Cache error: {str(e)}'
        }
    
    # Storage check
    try:
        # Check if default_storage is accessible
        if default_storage.exists('') or not default_storage.exists(''):
            # Both True and False mean storage is accessible
            health_status['checks']['storage'] = {
                'status': 'healthy',
                'message': 'Storage accessible'
            }
    except Exception as e:
        overall_healthy = False
        health_status['checks']['storage'] = {
            'status': 'unhealthy',
            'message': f'Storage error: {str(e)}'
        }
    
    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
        return Response(health_status, status=503)
    
    return Response(health_status)


urlpatterns = [
    path('', api_root, name='api-root'),
    path('health/', health_check, name='health-check'),
    path('auth/', include('api.v1.auth.urls')),
    path('users/', include('api.v1.users.urls')),
    path('', include('api.v1.products.urls')),
    path('', include('api.v1.cart.urls')),
]
