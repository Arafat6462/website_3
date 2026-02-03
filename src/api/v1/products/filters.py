"""Product API filters.

This module provides django-filter FilterSets for:
- Products (category, price, attributes, stock)
"""

import django_filters
from apps.products.models import Product, ProductVariant


class ProductFilter(django_filters.FilterSet):
    """FilterSet for Product queryset.
    
    Filters:
        - category: Filter by category slug
        - price_min: Minimum price
        - price_max: Maximum price
        - in_stock: Only products with available stock
        - is_featured: Featured products
        - is_new: New arrival products
    """
    
    category = django_filters.CharFilter(
        field_name='category__slug',
        lookup_expr='iexact',
        help_text='Filter by category slug'
    )
    
    price_min = django_filters.NumberFilter(
        field_name='base_price',
        lookup_expr='gte',
        help_text='Minimum price'
    )
    
    price_max = django_filters.NumberFilter(
        field_name='base_price',
        lookup_expr='lte',
        help_text='Maximum price'
    )
    
    in_stock = django_filters.BooleanFilter(
        method='filter_in_stock',
        help_text='Filter products with available stock'
    )
    
    is_featured = django_filters.BooleanFilter(
        field_name='is_featured',
        help_text='Filter featured products'
    )
    
    is_new = django_filters.BooleanFilter(
        field_name='is_new',
        help_text='Filter new arrival products'
    )
    
    product_type = django_filters.CharFilter(
        field_name='product_type__slug',
        lookup_expr='iexact',
        help_text='Filter by product type slug'
    )
    
    class Meta:
        model = Product
        fields = [
            'category',
            'price_min',
            'price_max',
            'in_stock',
            'is_featured',
            'is_new',
            'product_type',
        ]
    
    def filter_in_stock(self, queryset, name, value):
        """Filter products with available stock.
        
        Args:
            queryset: Product queryset
            name: Filter name
            value (bool): True to filter in-stock products
        
        Returns:
            QuerySet: Filtered queryset
        """
        if value:
            # Products with at least one variant in stock
            return queryset.filter(
                variants__is_active=True,
                variants__stock_quantity__gt=0
            ).distinct()
        return queryset
