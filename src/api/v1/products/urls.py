"""Product API URLs."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, ProductTypeViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'product-types', ProductTypeViewSet, basename='producttype')

urlpatterns = [
    path('', include(router.urls)),
]
