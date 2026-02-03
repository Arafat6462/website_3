"""Serializers for user management API.

Handles user profiles, addresses, orders, wishlist, and reviews.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.users.models import CustomerAddress
from apps.orders.models import Order, OrderItem
from apps.engagement.models import Wishlist, WishlistItem, ProductReview
from apps.products.models import Product, ProductVariant

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile (read-only).
    
    Displays user account information and statistics.
    """
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'public_id',
            'email',
            'phone',
            'first_name',
            'last_name',
            'full_name',
            'total_orders',
            'total_spent',
            'email_verified',
            'date_joined',
        ]
        read_only_fields = fields
    
    def get_full_name(self, obj):
        """Get user's full name.
        
        Args:
            obj (User): User instance
        
        Returns:
            str: Full name
        """
        return obj.get_full_name()


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile.
    
    Allows updating personal information.
    """
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone',
        ]
    
    def validate_phone(self, value):
        """Validate phone is unique (if changed).
        
        Args:
            value (str): Phone number
        
        Returns:
            str: Validated phone
        
        Raises:
            ValidationError: If phone already exists
        """
        user = self.instance
        if User.objects.filter(phone=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value


class CustomerAddressSerializer(serializers.ModelSerializer):
    """Serializer for customer addresses.
    
    Handles address CRUD operations.
    """
    
    class Meta:
        model = CustomerAddress
        fields = [
            'id',
            'label',
            'recipient_name',
            'phone',
            'address_line1',
            'address_line2',
            'city',
            'area',
            'postal_code',
            'is_default',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create new address for user.
        
        Args:
            validated_data (dict): Validated data
        
        Returns:
            CustomerAddress: Created address instance
        """
        user = self.context['request'].user
        address = CustomerAddress.objects.create(user=user, **validated_data)
        
        # If this is marked as default, unset other defaults
        if address.is_default:
            CustomerAddress.objects.filter(user=user).exclude(pk=address.pk).update(is_default=False)
        
        return address
    
    def update(self, instance, validated_data):
        """Update address.
        
        Args:
            instance (CustomerAddress): Address instance
            validated_data (dict): Validated data
        
        Returns:
            CustomerAddress: Updated address instance
        """
        # If setting as default, unset other defaults
        if validated_data.get('is_default', False):
            CustomerAddress.objects.filter(user=instance.user).exclude(pk=instance.pk).update(is_default=False)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items in user order list.
    
    Displays ordered products.
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
        ]


class UserOrderSerializer(serializers.ModelSerializer):
    """Serializer for user orders.
    
    Displays order history with items.
    """
    
    items = OrderItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'public_id',
            'order_number',
            'status',
            'payment_method',
            'payment_status',
            'subtotal',
            'discount_amount',
            'shipping_cost',
            'tax_amount',
            'total',
            'items',
            'items_count',
            'customer_name',
            'shipping_city',
            'shipping_area',
            'tracking_number',
            'courier_name',
            'estimated_delivery',
            'created_at',
            'confirmed_at',
            'shipped_at',
            'delivered_at',
        ]
        read_only_fields = fields
    
    def get_items_count(self, obj):
        """Get total item count.
        
        Args:
            obj (Order): Order instance
        
        Returns:
            int: Sum of quantities
        """
        return sum(item.quantity for item in obj.items.all())


class WishlistItemVariantSerializer(serializers.ModelSerializer):
    """Lightweight serializer for wishlist item variants.
    
    Displays variant info in wishlist.
    """
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_image = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'public_id',
            'name',
            'sku',
            'price',
            'compare_price',
            'product_name',
            'product_slug',
            'product_image',
            'in_stock',
        ]
    
    def get_product_image(self, obj):
        """Get variant or product image.
        
        Args:
            obj (ProductVariant): Variant instance
        
        Returns:
            str: Image URL or None
        """
        request = self.context.get('request')
        
        # Check variant-specific image
        variant_image = obj.images.filter(is_primary=True).first()
        if variant_image and variant_image.image:
            return request.build_absolute_uri(variant_image.image.url) if request else variant_image.image.url
        
        # Fallback to product image
        product_image = obj.product.images.filter(is_primary=True).first()
        if product_image and product_image.image:
            return request.build_absolute_uri(product_image.image.url) if request else product_image.image.url
        
        return None
    
    def get_in_stock(self, obj):
        """Check if variant is in stock.
        
        Args:
            obj (ProductVariant): Variant instance
        
        Returns:
            bool: True if in stock
        """
        return obj.stock_quantity > 0 if obj.product.track_inventory else True


class WishlistItemSerializer(serializers.ModelSerializer):
    """Serializer for wishlist items.
    
    Displays wishlist with product details.
    """
    
    variant = WishlistItemVariantSerializer(read_only=True)
    
    class Meta:
        model = WishlistItem
        fields = [
            'id',
            'variant',
            'created_at',
        ]
        read_only_fields = fields


class WishlistToggleSerializer(serializers.Serializer):
    """Serializer for toggling wishlist items.
    
    Adds or removes items from wishlist.
    """
    
    variant_id = serializers.IntegerField(required=True)
    
    def validate_variant_id(self, value):
        """Validate variant exists and is available.
        
        Args:
            value (int): Variant ID
        
        Returns:
            int: Validated variant ID
        
        Raises:
            ValidationError: If variant not found
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


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for product reviews.
    
    Allows users to submit reviews.
    """
    
    user_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ProductReview
        fields = [
            'id',
            'product',
            'rating',
            'comment',
            'images',
            'user_name',
            'is_approved',
            'admin_reply',
            'admin_replied_at',
            'created_at',
        ]
        read_only_fields = ['id', 'user_name', 'is_approved', 'admin_reply', 'admin_replied_at', 'created_at']
    
    def get_user_name(self, obj):
        """Get reviewer name.
        
        Args:
            obj (ProductReview): Review instance
        
        Returns:
            str: User's full name
        """
        return obj.user.get_full_name()
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5.
        
        Args:
            value (int): Rating
        
        Returns:
            int: Validated rating
        
        Raises:
            ValidationError: If rating out of range
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate_product(self, value):
        """Validate product exists and user hasn't reviewed it.
        
        Args:
            value (Product): Product instance
        
        Returns:
            Product: Validated product
        
        Raises:
            ValidationError: If already reviewed
        """
        user = self.context['request'].user
        if ProductReview.objects.filter(user=user, product=value).exists():
            raise serializers.ValidationError("You have already reviewed this product.")
        return value
    
    def create(self, validated_data):
        """Create product review.
        
        Args:
            validated_data (dict): Validated data
        
        Returns:
            ProductReview: Created review instance
        """
        user = self.context['request'].user
        review = ProductReview.objects.create(user=user, **validated_data)
        return review
