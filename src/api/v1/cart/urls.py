"""URL configuration for Cart API.

This module defines URL patterns for:
- Cart operations
- Checkout
- Coupon validation
- Shipping zones and calculation
"""

from django.urls import path
from .views import (
    CartView,
    CartItemView,
    CheckoutView,
    CouponValidateView,
    ShippingZoneListView,
    ShippingCalculateView,
)

urlpatterns = [
    # Cart endpoints
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/items/', CartItemView.as_view(), name='cart-items'),
    path('cart/items/<int:item_id>/', CartItemView.as_view(), name='cart-item-detail'),
    
    # Checkout
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    
    # Coupons
    path('coupons/validate/', CouponValidateView.as_view(), name='coupon-validate'),
    
    # Shipping
    path('shipping/zones/', ShippingZoneListView.as_view(), name='shipping-zones'),
    path('shipping/calculate/', ShippingCalculateView.as_view(), name='shipping-calculate'),
]
