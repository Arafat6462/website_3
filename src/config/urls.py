"""
URL Configuration for E-Commerce Backend.

This module defines the root URL routing for the entire application.
All API endpoints are versioned and prefixed with /api/v1/.

URL Structure:
    /admin/                 - Django admin interface (Unfold)
    /api/v1/               - API version 1 root
    /api/v1/health/        - Health check endpoint
    /api/v1/schema/        - OpenAPI schema (JSON)
    /api/v1/docs/          - Swagger UI documentation

In development, also includes:
    /debug/                - Django Debug Toolbar
    /media/<path>          - User-uploaded files

References:
    - URL dispatcher: https://docs.djangoproject.com/en/5.1/topics/http/urls/
    - DRF routers: https://www.django-rest-framework.org/api-guide/routers/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


def health_check(request) -> JsonResponse:
    """
    Health check endpoint for monitoring and container orchestration.
    
    Returns a simple JSON response indicating the service is running.
    Used by Docker health checks and load balancers.
    
    Args:
        request: The HTTP request object.
    
    Returns:
        JsonResponse with status "ok" and HTTP 200.
    
    Example:
        GET /api/v1/health/
        Response: {"status": "ok", "service": "ecom-backend"}
    """
    return JsonResponse({
        "status": "ok",
        "service": "ecom-backend",
        "version": "1.0.0",
    })


# =============================================================================
# API URL Patterns (Version 1)
# =============================================================================

api_v1_patterns = [
    # Health check
    path("health/", health_check, name="health-check"),
    
    # API Documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    
    # App-specific URLs will be added here as we build each app
    # path("products/", include("apps.products.urls")),
    # path("orders/", include("apps.orders.urls")),
    # path("users/", include("apps.users.urls")),
    # path("auth/", include("apps.users.auth_urls")),
    # path("cart/", include("apps.orders.cart_urls")),
    # path("coupons/", include("apps.promotions.urls")),
    # path("cms/", include("apps.cms.urls")),
]

# =============================================================================
# Root URL Patterns
# =============================================================================

urlpatterns = [
    # Admin site (using Unfold)
    path("admin/", admin.site.urls),
    
    # API version 1
    path("api/v1/", include((api_v1_patterns, "api-v1"))),
]

# =============================================================================
# Development-only URLs
# =============================================================================
# These URLs are only available when DEBUG=True
# =============================================================================

if settings.DEBUG:
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Serve static files in development (usually handled by runserver automatically)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
