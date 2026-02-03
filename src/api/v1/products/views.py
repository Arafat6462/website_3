"""Product API views.

This module provides viewsets for:
- Products (list, detail, featured, new)
- Categories (list, tree)
- Product search and filtering
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Prefetch
from django_filters.rest_framework import DjangoFilterBackend

from apps.products.models import (
    Product, ProductVariant, Category, ProductType, ProductImage
)
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    CategorySerializer,
    CategoryTreeSerializer,
    ProductTypeSerializer,
)
from .filters import ProductFilter


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for categories.
    
    Endpoints:
        GET /api/v1/categories/ - List all categories
        GET /api/v1/categories/{id}/ - Category detail
        GET /api/v1/categories/tree/ - Hierarchical tree
        GET /api/v1/categories/{id}/products/ - Products in category
    """
    
    queryset = Category.objects.filter(status='active').select_related('parent')
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Optimize queryset based on action."""
        qs = super().get_queryset()
        
        if self.action == 'list':
            # Only root categories for list view
            qs = qs.filter(parent__isnull=True)
        
        return qs.order_by('sort_order', 'name')
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get complete category tree.
        
        Returns hierarchical category structure for navigation.
        
        Returns:
            Response: Nested category data
        """
        root_categories = Category.objects.filter(
            status='active',
            parent__isnull=True
        ).prefetch_related('children').order_by('sort_order')
        
        serializer = CategoryTreeSerializer(root_categories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get products in this category.
        
        Args:
            slug (str): Category slug
        
        Returns:
            Response: Paginated product list
        """
        category = self.get_object()
        
        # Get products in this category and all descendant categories
        descendant_ids = self._get_descendant_category_ids(category)
        
        products = Product.objects.filter(
            category_id__in=descendant_ids,
            status='published'
        ).select_related('category', 'product_type').prefetch_related(
            'images',
            'variants',
            'reviews'
        ).order_by('-created_at')
        
        # Apply pagination
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    def _get_descendant_category_ids(self, category):
        """Get IDs of category and all descendants.
        
        Args:
            category (Category): Root category
        
        Returns:
            list: List of category IDs
        """
        ids = [category.id]
        children = Category.objects.filter(parent=category, status='active')
        
        for child in children:
            ids.extend(self._get_descendant_category_ids(child))
        
        return ids


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for products.
    
    Endpoints:
        GET /api/v1/products/ - List products (with filters)
        GET /api/v1/products/{slug}/ - Product detail
        GET /api/v1/products/featured/ - Featured products
        GET /api/v1/products/new/ - New products
        GET /api/v1/products/search/?q=query - Search products
    """
    
    queryset = Product.objects.filter(status='published').select_related(
        'category',
        'product_type'
    ).prefetch_related(
        'images',
        'variants',
        'attribute_values__attribute',
        'reviews'
    )
    
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'short_description', 'description']
    ordering_fields = ['created_at', 'base_price', 'sold_count', 'view_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer class.
        
        Returns:
            Serializer: List or detail serializer
        """
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve product and increment view count.
        
        Returns:
            Response: Product detail data
        """
        instance = self.get_object()
        
        # Increment view count
        Product.objects.filter(pk=instance.pk).update(view_count=instance.view_count + 1)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products.
        
        Returns:
            Response: Paginated featured products
        """
        products = self.get_queryset().filter(is_featured=True)
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def new(self, request):
        """Get new arrival products.
        
        Returns:
            Response: Paginated new products
        """
        products = self.get_queryset().filter(is_new=True)
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def filters(self, request):
        """Get available filter options.
        
        Returns filter metadata for building filter UI.
        
        Returns:
            Response: Filter options
        """
        # Get categories with product counts
        categories = Category.objects.filter(
            status='active',
            product_count__gt=0
        ).values('id', 'name', 'slug', 'product_count')
        
        # Get price range
        products = self.get_queryset()
        if products.exists():
            prices = [p.base_price for p in products]
            price_range = {
                'min': float(min(prices)),
                'max': float(max(prices))
            }
        else:
            price_range = {'min': 0, 'max': 0}
        
        # Get product types
        product_types = ProductType.objects.filter(
            is_active=True
        ).values('id', 'name', 'slug')
        
        return Response({
            'categories': list(categories),
            'price_range': price_range,
            'product_types': list(product_types),
        })


class ProductTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for product types.
    
    Endpoints:
        GET /api/v1/product-types/ - List product types
        GET /api/v1/product-types/{slug}/ - Product type detail with attributes
    """
    
    queryset = ProductType.objects.filter(is_active=True).prefetch_related(
        'product_type_attributes__attribute'
    )
    serializer_class = ProductTypeSerializer
    lookup_field = 'slug'
