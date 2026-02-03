"""Product API serializers.

This module provides DRF serializers for:
- Categories (hierarchical)
- Product Types and Attributes
- Products with variants and attributes
- Product images
- Reviews (read-only for product display)
"""

from rest_framework import serializers
from apps.products.models import (
    Category, ProductType, Attribute, Product, ProductVariant,
    ProductAttributeValue, VariantAttributeValue, ProductImage
)
from apps.engagement.models import ProductReview


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category with parent information.
    
    Provides basic category data with parent reference.
    Used for nested category display in products.
    """
    
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    product_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'parent',
            'parent_name',
            'description',
            'image',
            'product_count',
        ]
        read_only_fields = ['id', 'product_count']


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Serializer for Category with nested children.
    
    Recursively includes child categories for building
    navigation menus and category trees.
    """
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'image',
            'product_count',
            'children',
        ]
        read_only_fields = ['id', 'product_count']
    
    def get_children(self, obj):
        """Get child categories recursively.
        
        Args:
            obj (Category): Category instance
        
        Returns:
            list: Serialized child categories
        """
        # Only get active children with products
        children = obj.children.filter(status='active').order_by('sort_order')
        return CategoryTreeSerializer(children, many=True).data


class AttributeSerializer(serializers.ModelSerializer):
    """Serializer for Attribute definition.
    
    Provides attribute metadata for filtering and display.
    """
    
    class Meta:
        model = Attribute
        fields = [
            'id',
            'name',
            'code',
            'field_type',
            'options',
            'is_variant',
            'is_filterable',
        ]
        read_only_fields = ['id']


class ProductTypeSerializer(serializers.ModelSerializer):
    """Serializer for ProductType with attributes.
    
    Includes all attributes assigned to this product type.
    """
    
    attributes = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductType
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'attributes',
        ]
        read_only_fields = ['id']
    
    def get_attributes(self, obj):
        """Get attributes for this product type.
        
        Args:
            obj (ProductType): ProductType instance
        
        Returns:
            list: List of attributes
        """
        # Get attributes through product_type_attributes junction table
        attributes = [pta.attribute for pta in obj.product_type_attributes.all()]
        return AttributeSerializer(attributes, many=True).data


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    """Serializer for product-level attribute values.
    
    Used for non-variant attributes (e.g., Material, Brand).
    """
    
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    attribute_code = serializers.CharField(source='attribute.code', read_only=True)
    
    class Meta:
        model = ProductAttributeValue
        fields = [
            'attribute',
            'attribute_name',
            'attribute_code',
            'value',
        ]


class VariantAttributeValueSerializer(serializers.ModelSerializer):
    """Serializer for variant-level attribute values.
    
    Used for variant attributes (e.g., Size, Color).
    """
    
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    attribute_code = serializers.CharField(source='attribute.code', read_only=True)
    
    class Meta:
        model = VariantAttributeValue
        fields = [
            'attribute',
            'attribute_name',
            'attribute_code',
            'value',
        ]


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images.
    
    Provides image URLs and metadata.
    """
    
    class Meta:
        model = ProductImage
        fields = [
            'id',
            'image',
            'alt_text',
            'is_primary',
            'sort_order',
        ]
        read_only_fields = ['id']


class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for product variants.
    
    Includes variant-specific attributes, images, and stock info.
    """
    
    attributes = VariantAttributeValueSerializer(
        source='attribute_values',
        many=True,
        read_only=True
    )
    images = ProductImageSerializer(
        source='productimage_set',
        many=True,
        read_only=True
    )
    in_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'public_id',
            'sku',
            'name',
            'price',
            'compare_price',
            'stock_quantity',
            'in_stock',
            'is_active',
            'is_default',
            'attributes',
            'images',
            'weight',
            'barcode',
        ]
        read_only_fields = ['id', 'public_id', 'in_stock']
    
    def to_representation(self, instance):
        """Customize representation.
        
        Adds computed fields like in_stock.
        """
        data = super().to_representation(instance)
        data['in_stock'] = instance.stock_quantity > 0
        return data


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list view.
    
    Lightweight serializer for list endpoints.
    Includes essential data without heavy nested fields.
    """
    
    category = CategorySerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'public_id',
            'name',
            'slug',
            'short_description',
            'category',
            'base_price',
            'min_price',
            'max_price',
            'compare_price',
            'primary_image',
            'in_stock',
            'is_featured',
            'is_new',
            'average_rating',
            'review_count',
            'status',
        ]
        read_only_fields = ['id', 'public_id']
    
    def get_primary_image(self, obj):
        """Get primary product image.
        
        Args:
            obj (Product): Product instance
        
        Returns:
            str: Image URL or None
        """
        image = obj.images.filter(is_primary=True).first()
        if not image:
            image = obj.images.first()
        
        if image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.image.url)
            return image.image.url
        return None
    
    def get_min_price(self, obj):
        """Get minimum variant price.
        
        Args:
            obj (Product): Product instance
        
        Returns:
            Decimal: Minimum price
        """
        variants = obj.variants.filter(is_active=True)
        if variants.exists():
            return min(v.price for v in variants)
        return obj.base_price
    
    def get_max_price(self, obj):
        """Get maximum variant price.
        
        Args:
            obj (Product): Product instance
        
        Returns:
            Decimal: Maximum price
        """
        variants = obj.variants.filter(is_active=True)
        if variants.exists():
            return max(v.price for v in variants)
        return obj.base_price
    
    def get_in_stock(self, obj):
        """Check if any variant is in stock.
        
        Args:
            obj (Product): Product instance
        
        Returns:
            bool: True if any variant has stock
        """
        return obj.variants.filter(
            is_active=True,
            stock_quantity__gt=0
        ).exists()
    
    def get_average_rating(self, obj):
        """Get average product rating.
        
        Args:
            obj (Product): Product instance
        
        Returns:
            float: Average rating or None
        """
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return None
    
    def get_review_count(self, obj):
        """Get approved review count.
        
        Args:
            obj (Product): Product instance
        
        Returns:
            int: Number of approved reviews
        """
        return obj.reviews.filter(is_approved=True).count()


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for product reviews (read-only).
    
    Used to display reviews in product detail.
    """
    
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = [
            'id',
            'user_name',
            'rating',
            'comment',
            'images',
            'created_at',
            'admin_reply',
            'admin_replied_at',
        ]
        read_only_fields = fields
    
    def get_user_name(self, obj):
        """Get user's display name.
        
        Args:
            obj (ProductReview): Review instance
        
        Returns:
            str: User's full name or email
        """
        if obj.user.first_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.email.split('@')[0]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for product detail view.
    
    Complete product data with all nested relationships.
    """
    
    category = CategorySerializer(read_only=True)
    product_type = ProductTypeSerializer(read_only=True)
    attributes = ProductAttributeValueSerializer(
        source='attribute_values',
        many=True,
        read_only=True
    )
    variants = ProductVariantSerializer(
        many=True,
        read_only=True
    )
    images = ProductImageSerializer(
        many=True,
        read_only=True
    )
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'public_id',
            'name',
            'slug',
            'short_description',
            'description',
            'category',
            'product_type',
            'base_price',
            'compare_price',
            'cost_price',
            'attributes',
            'variants',
            'images',
            'status',
            'is_featured',
            'is_new',
            'track_inventory',
            'allow_backorder',
            'view_count',
            'sold_count',
            'meta_title',
            'meta_description',
            'average_rating',
            'review_count',
            'reviews',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'public_id',
            'view_count',
            'sold_count',
            'created_at',
            'updated_at',
        ]
    
    def get_reviews(self, obj):
        """Get approved reviews.
        
        Args:
            obj (Product): Product instance
        
        Returns:
            list: Serialized reviews
        """
        reviews = obj.reviews.filter(
            is_approved=True
        ).order_by('-created_at')[:10]  # Latest 10 reviews
        return ProductReviewSerializer(reviews, many=True).data
    
    def get_average_rating(self, obj):
        """Get average product rating.
        
        Args:
            obj (Product): Product instance
        
        Returns:
            float: Average rating or None
        """
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return None
    
    def get_review_count(self, obj):
        """Get approved review count.
        
        Args:
            obj (Product): Product instance
        
        Returns:
            int: Number of approved reviews
        """
        return obj.reviews.filter(is_approved=True).count()
