"""
Products Application Package.

This package contains all product-related functionality:
- Product catalog with EAV pattern
- Categories with hierarchical structure
- Product types and attributes (flexible schema)
- Variants and inventory management
- Product images

The EAV (Entity-Attribute-Value) pattern allows selling any product type
without code changes - just define attributes in the admin.

Usage:
    from apps.products.models import Product, ProductType, Category
"""

default_app_config = "apps.products.apps.ProductsConfig"
