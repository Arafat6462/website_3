"""URL patterns for user management API."""

from django.urls import path

from .views import (
    UserProfileView,
    UserAddressListView,
    UserAddressDetailView,
    UserOrderListView,
    UserOrderDetailView,
    OrderTrackingView,
    WishlistView,
    WishlistToggleView,
    ProductReviewCreateView,
)

urlpatterns = [
    # User profile
    path('me/', UserProfileView.as_view(), name='user-profile'),
    
    # Addresses
    path('me/addresses/', UserAddressListView.as_view(), name='user-address-list'),
    path('me/addresses/<int:address_id>/', UserAddressDetailView.as_view(), name='user-address-detail'),
    
    # Orders
    path('me/orders/', UserOrderListView.as_view(), name='user-order-list'),
    path('me/orders/<str:order_number>/', UserOrderDetailView.as_view(), name='user-order-detail'),
    
    # Order tracking (public)
    path('orders/track/', OrderTrackingView.as_view(), name='order-tracking'),
    
    # Wishlist
    path('me/wishlist/', WishlistView.as_view(), name='user-wishlist'),
    path('me/wishlist/toggle/', WishlistToggleView.as_view(), name='wishlist-toggle'),
    
    # Reviews
    path('me/reviews/', ProductReviewCreateView.as_view(), name='review-create'),
]
