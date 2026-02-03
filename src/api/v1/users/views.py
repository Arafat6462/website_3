"""Views for user management API.

Handles user profiles, addresses, orders, wishlist, and reviews.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.users.models import CustomerAddress
from apps.orders.models import Order
from apps.engagement.models import Wishlist, WishlistItem, ProductReview
from apps.products.models import ProductVariant

from .serializers import (
    UserProfileSerializer,
    UpdateProfileSerializer,
    CustomerAddressSerializer,
    UserOrderSerializer,
    WishlistItemSerializer,
    WishlistToggleSerializer,
    ProductReviewSerializer,
)


class UserProfileView(APIView):
    """API view for user profile.
    
    Get and update user profile information.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user profile.
        
        Returns:
            Response: User profile data
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        """Update user profile.
        
        Request Body:
            first_name (str): First name
            last_name (str): Last name
            phone (str): Phone number
        
        Returns:
            Response: Updated user profile
        """
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return full profile
        profile_serializer = UserProfileSerializer(request.user)
        return Response(profile_serializer.data)


class UserAddressListView(APIView):
    """API view for user address list.
    
    List and create addresses.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List user addresses.
        
        Returns:
            Response: List of addresses
        """
        addresses = CustomerAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')
        serializer = CustomerAddressSerializer(addresses, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create new address.
        
        Request Body:
            label (str): Address label (e.g., "Home", "Office")
            recipient_name (str): Recipient name
            phone (str): Phone number
            address_line1 (str): Address line 1
            address_line2 (str): Address line 2 (optional)
            city (str): City
            area (str): Area/District
            postal_code (str): Postal code (optional)
            is_default (bool): Set as default address
        
        Returns:
            Response: Created address
        """
        serializer = CustomerAddressSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserAddressDetailView(APIView):
    """API view for user address detail.
    
    Update and delete addresses.
    """
    
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, address_id):
        """Update address.
        
        Args:
            address_id (int): Address ID
        
        Returns:
            Response: Updated address
        """
        address = get_object_or_404(CustomerAddress, id=address_id, user=request.user)
        serializer = CustomerAddressSerializer(
            address,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def delete(self, request, address_id):
        """Delete address.
        
        Args:
            address_id (int): Address ID
        
        Returns:
            Response: Success message
        """
        address = get_object_or_404(CustomerAddress, id=address_id, user=request.user)
        address.delete()
        return Response(
            {'message': 'Address deleted successfully.'},
            status=status.HTTP_200_OK
        )


class UserOrderListView(APIView):
    """API view for user order list.
    
    List user's order history.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List user orders.
        
        Query Parameters:
            status (str): Filter by order status
        
        Returns:
            Response: List of orders
        """
        orders = Order.objects.filter(user=request.user, is_deleted=False).select_related(
            'shipping_zone'
        ).prefetch_related('items').order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        serializer = UserOrderSerializer(orders, many=True)
        return Response(serializer.data)


class UserOrderDetailView(APIView):
    """API view for user order detail.
    
    Get single order details.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_number):
        """Get order details.
        
        Args:
            order_number (str): Order number
        
        Returns:
            Response: Order details
        """
        order = get_object_or_404(
            Order,
            order_number=order_number,
            user=request.user,
            is_deleted=False
        )
        serializer = UserOrderSerializer(order)
        return Response(serializer.data)


class OrderTrackingView(APIView):
    """API view for order tracking.
    
    Track order status by order number (no auth required for guest orders).
    """
    
    permission_classes = []  # Allow anyone with order number
    
    def post(self, request):
        """Track order.
        
        Request Body:
            order_number (str): Order number
            phone (str): Customer phone number
        
        Returns:
            Response: Order tracking information
        """
        order_number = request.data.get('order_number')
        phone = request.data.get('phone')
        
        if not order_number or not phone:
            return Response(
                {'error': 'Order number and phone number are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order = get_object_or_404(
            Order,
            order_number=order_number,
            customer_phone=phone,
            is_deleted=False
        )
        
        # Return limited info for tracking
        return Response({
            'order_number': order.order_number,
            'status': order.status,
            'tracking_number': order.tracking_number,
            'courier_name': order.courier_name,
            'estimated_delivery': order.estimated_delivery,
            'created_at': order.created_at,
            'confirmed_at': order.confirmed_at,
            'shipped_at': order.shipped_at,
            'delivered_at': order.delivered_at,
        })


class WishlistView(APIView):
    """API view for user wishlist.
    
    Get user's wishlist.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user wishlist.
        
        Returns:
            Response: Wishlist items
        """
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        items = WishlistItem.objects.filter(wishlist=wishlist).select_related(
            'variant__product'
        ).prefetch_related('variant__images', 'variant__product__images').order_by('-created_at')
        
        serializer = WishlistItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)


class WishlistToggleView(APIView):
    """API view for toggling wishlist items.
    
    Add or remove items from wishlist.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Toggle wishlist item.
        
        Request Body:
            variant_id (int): Product variant ID
        
        Returns:
            Response: Action performed and item status
        """
        serializer = WishlistToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        variant_id = serializer.validated_data['variant_id']
        variant = ProductVariant.objects.get(id=variant_id)
        
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        # Check if item exists
        wishlist_item = WishlistItem.objects.filter(wishlist=wishlist, variant=variant).first()
        
        if wishlist_item:
            # Remove from wishlist
            wishlist_item.delete()
            return Response({
                'action': 'removed',
                'message': 'Item removed from wishlist.',
                'in_wishlist': False,
            }, status=status.HTTP_200_OK)
        else:
            # Add to wishlist
            WishlistItem.objects.create(wishlist=wishlist, variant=variant)
            return Response({
                'action': 'added',
                'message': 'Item added to wishlist.',
                'in_wishlist': True,
            }, status=status.HTTP_201_CREATED)


class ProductReviewCreateView(APIView):
    """API view for creating product reviews.
    
    Submit product review.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Submit product review.
        
        Request Body:
            product (int): Product ID
            rating (int): Rating (1-5)
            comment (str): Review text
            images (list): Review images (optional)
        
        Returns:
            Response: Created review
        """
        serializer = ProductReviewSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
