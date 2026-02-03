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
    """Health check endpoint.
    
    Returns system status.
    """
    return Response({
        'status': 'healthy',
        'version': '1.0',
        'api': 'v1'
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('health/', health_check, name='health-check'),
    path('auth/', include('api.v1.auth.urls')),
    path('users/', include('api.v1.users.urls')),
    path('', include('api.v1.products.urls')),
    path('', include('api.v1.cart.urls')),
]
