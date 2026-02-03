"""Views for Cart API.

This module provides API views for:
- Shopping cart operations (get, add, update, remove, clear)
- Checkout and order creation
- Coupon validation
- Shipping zone listing and cost calculation
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction

from apps.orders.models import Cart, CartItem, ShippingZone, Coupon
from apps.products.models import ProductVariant
from apps.orders.services import CartService, CouponService, ShippingService
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
    CartItemSerializer,
    CheckoutSerializer,
    OrderSerializer,
    CouponValidationSerializer,
    ShippingZoneSerializer,
    ShippingCalculationSerializer,
)


class CartView(APIView):
    """API view for cart operations.
    
    Handles getting and clearing the cart.
    Supports both authenticated users and guest sessions.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get current cart with items.
        
        Returns cart for authenticated user or guest session.
        
        Returns:
            Response: Cart data with items and totals
        """
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        cart_service = CartService()
        cart = cart_service.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key
        )
        
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)
    
    def delete(self, request):
        """Clear cart (remove all items).
        
        Returns:
            Response: Success message
        """
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        cart_service = CartService()
        cart = cart_service.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key
        )
        
        cart_service.clear_cart(cart)
        
        return Response(
            {'message': 'Cart cleared successfully.'},
            status=status.HTTP_200_OK
        )


class CartItemView(APIView):
    """API view for cart item operations.
    
    Handles adding, updating, and removing cart items.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Add item to cart.
        
        Creates or updates cart item with specified quantity.
        
        Request Body:
            variant_id (int): Product variant ID
            quantity (int): Quantity to add
        
        Returns:
            Response: Updated cart data
        """
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        cart_service = CartService()
        cart = cart_service.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key
        )
        
        # Get variant object
        variant = ProductVariant.objects.get(id=serializer.validated_data['variant_id'])
        
        # Add to cart
        cart_item = cart_service.add_item(
            cart=cart,
            variant=variant,
            quantity=serializer.validated_data['quantity']
        )
        
        # Return updated cart
        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_201_CREATED)
    
    def patch(self, request, item_id):
        """Update cart item quantity.
        
        Args:
            item_id (int): Cart item ID
        
        Request Body:
            quantity (int): New quantity
        
        Returns:
            Response: Updated cart item
        """
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        cart_service = CartService()
        cart = cart_service.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key
        )
        
        # Get cart item
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate and update
        serializer = UpdateCartItemSerializer(cart_item, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cart_item = cart_service.update_item(
            item=cart_item,
            quantity=serializer.validated_data['quantity']
        )
        
        item_serializer = CartItemSerializer(cart_item, context={'request': request})
        return Response(item_serializer.data)
    
    def delete(self, request, item_id):
        """Remove item from cart.
        
        Args:
            item_id (int): Cart item ID
        
        Returns:
            Response: Success message
        """
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        cart_service = CartService()
        cart = cart_service.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key
        )
        
        # Get cart item
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        cart_service.remove_item(cart_item)
        
        return Response(
            {'message': 'Item removed from cart.'},
            status=status.HTTP_200_OK
        )


class CheckoutView(APIView):
    """API view for checkout.
    
    Creates order from cart with payment and shipping details.
    """
    
    permission_classes = [AllowAny]
    
    @transaction.atomic
    def post(self, request):
        """Create order from cart.
        
        Validates cart, applies coupon, calculates shipping,
        creates order and clears cart.
        
        Request Body:
            customer_name (str): Customer name
            customer_email (str): Customer email
            customer_phone (str): Customer phone
            shipping_address_line1 (str): Address line 1
            shipping_address_line2 (str): Address line 2 (optional)
            shipping_city (str): City
            shipping_area (str): Area/district
            shipping_postal_code (str): Postal code (optional)
            shipping_zone_id (int): Shipping zone ID
            payment_method (str): Payment method (cod, bkash, nagad, card)
            coupon_code (str): Coupon code (optional)
            customer_notes (str): Customer notes (optional)
        
        Returns:
            Response: Created order data
        """
        # Ensure session exists for guest checkout
        if not request.session.session_key:
            request.session.create()
        
        # Get cart
        cart_service = CartService()
        cart = cart_service.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key
        )
        
        # Validate and create order
        serializer = CheckoutSerializer(
            data=request.data,
            context={'request': request, 'cart': cart}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Clear cart after successful order creation
        cart_service.clear_cart(cart)
        
        # Return order details
        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)


class CouponValidateView(APIView):
    """API view for coupon validation.
    
    Validates coupon code and returns discount information.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Validate coupon code.
        
        Request Body:
            code (str): Coupon code
            cart_total (Decimal): Cart subtotal
        
        Returns:
            Response: Validation result and discount amount
        """
        serializer = CouponValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        cart_total = serializer.validated_data['cart_total']
        
        # Get coupon
        try:
            coupon = Coupon.objects.get(code=code.upper(), is_deleted=False, is_active=True)
        except Coupon.DoesNotExist:
            return Response(
                {'valid': False, 'message': 'Invalid coupon code.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Basic validation
        errors = []
        
        # Check validity period
        if not coupon.is_valid:
            errors.append("This coupon has expired or is not yet valid")
        
        # Check global usage limit
        if coupon.is_exhausted:
            errors.append("This coupon has reached its usage limit")
        
        # Check minimum order amount
        if cart_total < coupon.minimum_order:
            errors.append(
                f"Minimum order amount of ৳{coupon.minimum_order} required (current: ৳{cart_total})"
            )
        
        if errors:
            return Response(
                {'valid': False, 'message': ', '.join(errors)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate discount
        if coupon.discount_type == "percentage":
            discount = float(cart_total) * (float(coupon.discount_value) / 100)
            if coupon.maximum_discount:
                discount = min(discount, float(coupon.maximum_discount))
        else:  # fixed
            discount = float(coupon.discount_value)
        
        discount = min(discount, float(cart_total))
        discount = round(discount, 2)
        
        return Response({
            'valid': True,
            'message': 'Coupon is valid.',
            'coupon': {
                'code': coupon.code,
                'name': coupon.name,
                'description': coupon.description,
                'discount_type': coupon.discount_type,
                'discount_value': coupon.discount_value,
                'discount_amount': discount,
            }
        })


class ShippingZoneListView(APIView):
    """API view for listing shipping zones.
    
    Returns all active shipping zones with costs.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """List all active shipping zones.
        
        Returns:
            Response: List of shipping zones
        """
        zones = ShippingZone.objects.filter(is_active=True).order_by('sort_order')
        serializer = ShippingZoneSerializer(zones, many=True)
        return Response(serializer.data)


class ShippingCalculateView(APIView):
    """API view for shipping cost calculation.
    
    Calculates shipping cost based on zone and cart total.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Calculate shipping cost.
        
        Request Body:
            shipping_zone_id (int): Shipping zone ID
            cart_total (Decimal): Cart subtotal
        
        Returns:
            Response: Shipping cost and free shipping info
        """
        serializer = ShippingCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get zone
        zone = ShippingZone.objects.get(id=serializer.validated_data['shipping_zone_id'])
        
        # Calculate shipping using zone's method
        cart_total = float(serializer.validated_data['cart_total'])
        shipping_cost = zone.calculate_shipping_cost(cart_total)
        
        return Response({
            'zone_name': zone.name,
            'shipping_cost': f'{shipping_cost:.2f}',
            'free_shipping_threshold': str(zone.free_shipping_threshold),
            'is_free_shipping': shipping_cost == 0,
            'estimated_days': zone.estimated_days,
        })
