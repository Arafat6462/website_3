"""Serializers for Cart API.

This module provides serializers for:
- Shopping cart and cart items
- Checkout and order creation
- Coupon validation
- Shipping calculation
"""

from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Cart, CartItem, Order, OrderItem, Coupon, ShippingZone
from apps.products.models import ProductVariant
from apps.users.models import CustomerAddress
from apps.orders.services import CartService, CouponService, ShippingService, OrderService


class CartItemProductVariantSerializer(serializers.ModelSerializer):
    """Lightweight variant serializer for cart items.
    
    Displays essential product and variant information in cart.
    """
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'sku',
            'name',
            'product_name',
            'product_slug',
            'price',
            'compare_price',
            'stock_quantity',
            'product_image',
            'is_active',
        ]
        read_only_fields = ['id']
    
    def get_product_image(self, obj):
        """Get primary product image.
        
        Args:
            obj (ProductVariant): Variant instance
        
        Returns:
            str: Image URL or None
        """
        # Check variant-specific image first
        variant_image = obj.images.filter(is_primary=True).first()
        if variant_image:
            return self.context['request'].build_absolute_uri(variant_image.image.url) if variant_image.image else None
        
        # Fallback to product primary image
        product_image = obj.product.images.filter(is_primary=True).first()
        if product_image:
            return self.context['request'].build_absolute_uri(product_image.image.url) if product_image.image else None
        
        return None


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items.
    
    Used for displaying cart contents with product details.
    """
    
    variant = CartItemProductVariantSerializer(read_only=True)
    line_total = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = [
            'id',
            'variant',
            'quantity',
            'unit_price',
            'line_total',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'unit_price', 'created_at', 'updated_at']
    
    def get_line_total(self, obj):
        """Calculate line total.
        
        Args:
            obj (CartItem): Cart item instance
        
        Returns:
            Decimal: Quantity × unit price
        """
        return obj.quantity * obj.unit_price


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart.
    
    Validates variant and quantity before adding.
    """
    
    variant_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)
    
    def validate_variant_id(self, value):
        """Validate variant exists and is active.
        
        Args:
            value (int): Variant ID
        
        Returns:
            int: Validated variant ID
        
        Raises:
            ValidationError: If variant not found or inactive
        """
        try:
            variant = ProductVariant.objects.select_related('product').get(
                id=value,
                is_active=True,
                product__status='published'
            )
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError("Product variant not found or not available.")
        
        return value
    
    def validate(self, data):
        """Validate stock availability.
        
        Args:
            data (dict): Validated data
        
        Returns:
            dict: Validated data
        
        Raises:
            ValidationError: If insufficient stock
        """
        variant = ProductVariant.objects.get(id=data['variant_id'])
        
        if variant.product.track_inventory:
            if data['quantity'] > variant.stock_quantity:
                raise serializers.ValidationError({
                    'quantity': f"Only {variant.stock_quantity} items available in stock."
                })
        
        return data


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity.
    
    Validates new quantity against stock.
    """
    
    quantity = serializers.IntegerField(required=True, min_value=1)
    
    def validate_quantity(self, value):
        """Validate quantity against stock.
        
        Args:
            value (int): Requested quantity
        
        Returns:
            int: Validated quantity
        
        Raises:
            ValidationError: If insufficient stock
        """
        cart_item = self.instance
        variant = cart_item.variant
        
        if variant.product.track_inventory:
            if value > variant.stock_quantity:
                raise serializers.ValidationError(
                    f"Only {variant.stock_quantity} items available in stock."
                )
        
        return value


class CartSerializer(serializers.ModelSerializer):
    """Serializer for shopping cart.
    
    Displays cart with all items and totals.
    """
    
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'public_id',
            'items',
            'item_count',
            'subtotal',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['public_id', 'created_at', 'updated_at']
    
    def get_item_count(self, obj):
        """Get total item count.
        
        Args:
            obj (Cart): Cart instance
        
        Returns:
            int: Sum of all quantities
        """
        return sum(item.quantity for item in obj.items.all())
    
    def get_subtotal(self, obj):
        """Calculate cart subtotal.
        
        Args:
            obj (Cart): Cart instance
        
        Returns:
            Decimal: Sum of all line totals
        """
        return sum(item.quantity * item.unit_price for item in obj.items.all())


class CouponValidationSerializer(serializers.Serializer):
    """Serializer for coupon validation.
    
    Validates coupon code and calculates discount.
    """
    
    code = serializers.CharField(required=True, max_length=50)
    cart_total = serializers.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.00')
    )
    
    def validate_code(self, value):
        """Normalize coupon code to uppercase.
        
        Args:
            value (str): Coupon code
        
        Returns:
            str: Uppercased code
        """
        return value.upper()


class ShippingZoneSerializer(serializers.ModelSerializer):
    """Serializer for shipping zones.
    
    Displays shipping options with costs.
    """
    
    class Meta:
        model = ShippingZone
        fields = [
            'id',
            'name',
            'areas',
            'shipping_cost',
            'free_shipping_threshold',
            'estimated_days',
            'is_active',
        ]
        read_only_fields = ['id']


class ShippingCalculationSerializer(serializers.Serializer):
    """Serializer for shipping cost calculation.
    
    Calculates shipping based on zone and cart total.
    """
    
    shipping_zone_id = serializers.IntegerField(required=True)
    cart_total = serializers.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.00')
    )
    
    def validate_shipping_zone_id(self, value):
        """Validate shipping zone exists.
        
        Args:
            value (int): Zone ID
        
        Returns:
            int: Validated zone ID
        
        Raises:
            ValidationError: If zone not found
        """
        try:
            ShippingZone.objects.get(id=value, is_active=True)
        except ShippingZone.DoesNotExist:
            raise serializers.ValidationError("Shipping zone not found.")
        
        return value


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout and order creation.
    
    Validates all order details and creates order with items.
    """
    
    # Customer information
    customer_name = serializers.CharField(required=True, max_length=200)
    customer_email = serializers.EmailField(required=True)
    customer_phone = serializers.CharField(required=True, max_length=20)
    
    # Shipping address
    shipping_address_line1 = serializers.CharField(required=True, max_length=255)
    shipping_address_line2 = serializers.CharField(required=False, allow_blank=True, max_length=255)
    shipping_city = serializers.CharField(required=True, max_length=100)
    shipping_area = serializers.CharField(required=True, max_length=100)
    shipping_postal_code = serializers.CharField(required=False, allow_blank=True, max_length=20)
    
    # Order details
    shipping_zone_id = serializers.IntegerField(required=True)
    payment_method = serializers.ChoiceField(
        choices=['cod', 'bkash', 'nagad', 'card'],
        required=True
    )
    coupon_code = serializers.CharField(required=False, allow_blank=True, max_length=50)
    customer_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_shipping_zone_id(self, value):
        """Validate shipping zone.
        
        Args:
            value (int): Zone ID
        
        Returns:
            int: Validated zone ID
        
        Raises:
            ValidationError: If zone invalid
        """
        try:
            ShippingZone.objects.get(id=value, is_active=True)
        except ShippingZone.DoesNotExist:
            raise serializers.ValidationError("Invalid shipping zone.")
        
        return value
    
    def validate(self, data):
        """Validate cart has items and coupon if provided.
        
        Args:
            data (dict): Validated data
        
        Returns:
            dict: Validated data
        
        Raises:
            ValidationError: If validation fails
        """
        # Get cart from context
        cart = self.context.get('cart')
        if not cart:
            raise serializers.ValidationError("Cart not found.")
        
        # Check cart has items
        if not cart.items.exists():
            raise serializers.ValidationError("Cart is empty.")
        
        # Validate stock availability for all items
        for item in cart.items.select_related('variant__product'):
            variant = item.variant
            if variant.product.track_inventory:
                if item.quantity > variant.stock_quantity:
                    raise serializers.ValidationError({
                        'cart': f"Insufficient stock for {variant.product.name} - {variant.name}. "
                                f"Only {variant.stock_quantity} available."
                    })
        
        # Validate coupon if provided
        if data.get('coupon_code'):
            try:
                coupon = Coupon.objects.get(
                    code=data['coupon_code'].upper(),
                    is_active=True,
                    is_deleted=False
                )
                
                # Additional coupon validation using CouponService
                coupon_service = CouponService()
                result = coupon_service.validate_coupon(
                    code=data['coupon_code'].upper(),
                    cart=cart,
                    user=self.context['request'].user if self.context['request'].user.is_authenticated else None
                )
                
                if not result['valid']:
                    raise serializers.ValidationError({'coupon_code': ', '.join(result['errors'])})
                
                data['coupon_code'] = data['coupon_code'].upper()
                
            except Coupon.DoesNotExist:
                raise serializers.ValidationError({'coupon_code': "Invalid coupon code."})
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """Create order from cart.
        
        Args:
            validated_data (dict): Validated checkout data
        
        Returns:
            Order: Created order instance
        """
        cart = self.context['cart']
        request = self.context['request']
        user = request.user if request.user.is_authenticated else None
        
        # Get coupon if provided
        coupon = None
        if validated_data.get('coupon_code'):
            coupon = Coupon.objects.get(code=validated_data['coupon_code'])
        
        # Prepare shipping data
        shipping_data = {
            'customer_name': validated_data['customer_name'],
            'customer_email': validated_data['customer_email'],
            'customer_phone': validated_data['customer_phone'],
            'address_line1': validated_data['shipping_address_line1'],
            'address_line2': validated_data.get('shipping_address_line2', ''),
            'city': validated_data['shipping_city'],
            'area': validated_data['shipping_area'],
            'postal_code': validated_data.get('shipping_postal_code', ''),
        }
        
        # Create order using OrderService
        order_service = OrderService()
        order = order_service.create_from_cart(
            cart=cart,
            shipping_data=shipping_data,
            payment_method=validated_data['payment_method'],
            user=user,
            coupon=coupon,
            ip_address=request.META.get('REMOTE_ADDR', '')
        )
        
        return order


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items (read-only).
    
    Displays order item details.
    """
    
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product_name',
            'variant_name',
            'sku',
            'unit_price',
            'quantity',
            'line_total',
            'attributes_snapshot',
        ]
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders (read-only).
    
    Displays complete order information.
    """
    
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'public_id',
            'order_number',
            'customer_name',
            'customer_email',
            'customer_phone',
            'shipping_address_line1',
            'shipping_address_line2',
            'shipping_city',
            'shipping_area',
            'shipping_postal_code',
            'status',
            'subtotal',
            'discount_amount',
            'shipping_cost',
            'tax_amount',
            'total',
            'payment_method',
            'payment_status',
            'coupon_code',
            'customer_notes',
            'tracking_number',
            'courier_name',
            'estimated_delivery',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['public_id', 'order_number', 'created_at', 'updated_at']
