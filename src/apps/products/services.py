"""
Product services - business logic for product operations.

This module contains service classes for complex product operations:
- VariantGeneratorService: Automatically generate variants from attributes
"""

import itertools
from typing import Any

from django.db import transaction

from apps.core.utils import generate_sku
from apps.products.models import (
    Attribute,
    Product,
    ProductVariant,
    VariantAttributeValue,
)


class VariantGeneratorService:
    """
    Service for automatically generating product variants.

    This service creates ProductVariant instances based on variant attributes
    (attributes with is_variant=True) assigned to the product's ProductType.

    For example, if a product has:
    - Size attribute: S, M, L
    - Color attribute: Red, Blue

    It will generate 6 variants:
    - S-Red, S-Blue, M-Red, M-Blue, L-Red, L-Blue

    Usage:
        service = VariantGeneratorService(product)
        variants = service.generate_variants({
            'size': ['S', 'M', 'L'],
            'color': ['Red', 'Blue']
        })
    """

    def __init__(self, product: Product) -> None:
        """
        Initialize service for a product.

        Args:
            product: The product to generate variants for.
        """
        self.product = product

    def get_variant_attributes(self) -> list[Attribute]:
        """
        Get all variant attributes for this product's type.

        Returns:
            List of Attribute instances where is_variant=True.

        Example:
            attrs = service.get_variant_attributes()
            # [<Attribute: Size>, <Attribute: Color>]
        """
        return list(
            Attribute.objects.filter(
                product_type_attributes__product_type=self.product.product_type,
                is_variant=True,
            ).order_by("product_type_attributes__sort_order")
        )

    @transaction.atomic
    def generate_variants(
        self, attribute_values: dict[str, list[str]], base_price: float | None = None
    ) -> list[ProductVariant]:
        """
        Generate all variant combinations from attribute values.

        This creates a Cartesian product of all attribute value combinations
        and creates a ProductVariant + VariantAttributeValue for each.

        Args:
            attribute_values: Dict mapping attribute code to list of values.
                Example: {'size': ['S', 'M'], 'color': ['Red', 'Blue']}
            base_price: Optional base price for all variants (uses product.base_price if None).

        Returns:
            List of created ProductVariant instances.

        Raises:
            ValueError: If attribute_values is empty or attributes don't exist.

        Example:
            variants = service.generate_variants({
                'size': ['S', 'M', 'L'],
                'color': ['Red', 'Blue', 'Green']
            }, base_price=25.00)
            # Creates 9 variants (3 sizes × 3 colors)
        """
        if not attribute_values:
            raise ValueError("attribute_values cannot be empty")

        # Get attribute instances
        variant_attrs = self.get_variant_attributes()
        attr_codes = [attr.code for attr in variant_attrs]

        # Validate that all provided attributes exist
        for code in attribute_values.keys():
            if code not in attr_codes:
                raise ValueError(
                    f"Attribute '{code}' is not a variant attribute for this product type"
                )

        # Create mapping of code -> Attribute instance
        attr_map = {attr.code: attr for attr in variant_attrs}

        # Generate all combinations (Cartesian product)
        combinations = list(itertools.product(*attribute_values.values()))

        created_variants = []
        price = base_price if base_price is not None else self.product.base_price

        for combination in combinations:
            # Build variant name and SKU from combination
            variant_name_parts = []
            sku_attributes = {}

            # Map combination values to their attribute codes
            for idx, (attr_code, values) in enumerate(attribute_values.items()):
                value = combination[idx]
                variant_name_parts.append(value)
                sku_attributes[attr_code] = value

            variant_name = " - ".join(variant_name_parts)
            
            # Generate SKU with product prefix and variant attributes
            sku = generate_sku(
                prefix=self.product.slug[:4],
                attributes=sku_attributes,
                random_suffix=True
            )

            # Check if variant already exists
            if ProductVariant.objects.filter(sku=sku).exists():
                continue  # Skip duplicates

            # Create variant
            variant = ProductVariant.objects.create(
                product=self.product,
                sku=sku,
                name=variant_name,
                price=price,
                is_default=(len(created_variants) == 0),  # First variant is default
            )

            # Create attribute values for this variant
            for idx, (attr_code, values) in enumerate(attribute_values.items()):
                value = combination[idx]
                attribute = attr_map[attr_code]

                VariantAttributeValue.objects.create(
                    variant=variant, attribute=attribute, value=value
                )

            created_variants.append(variant)

        return created_variants

    @transaction.atomic
    def update_variant_stock(
        self, variant_updates: dict[str, dict[str, Any]]
    ) -> list[ProductVariant]:
        """
        Bulk update variant stock and prices.

        Args:
            variant_updates: Dict mapping SKU to update fields.
                Example: {
                    'CTEE-S-RED': {'stock_quantity': 100, 'price': 25.00},
                    'CTEE-M-BLU': {'stock_quantity': 50, 'price': 27.00}
                }

        Returns:
            List of updated ProductVariant instances.

        Raises:
            ValueError: If SKU doesn't exist.

        Example:
            updated = service.update_variant_stock({
                'CTEE-S-RED': {'stock_quantity': 100},
                'CTEE-M-BLU': {'stock_quantity': 50}
            })
        """
        updated_variants = []

        for sku, updates in variant_updates.items():
            try:
                variant = ProductVariant.objects.get(
                    sku=sku, product=self.product, is_deleted=False
                )
            except ProductVariant.DoesNotExist:
                raise ValueError(f"Variant with SKU '{sku}' not found")

            # Update allowed fields
            allowed_fields = ["stock_quantity", "price", "compare_price", "is_active"]
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(variant, field, value)

            variant.save()
            updated_variants.append(variant)

        return updated_variants

    def delete_all_variants(self) -> int:
        """
        Delete all variants for this product (soft delete).

        Returns:
            Number of variants deleted.

        Example:
            count = service.delete_all_variants()
            # Deleted 6 variants
        """
        count = self.product.variants.filter(is_deleted=False).count()
        self.product.variants.filter(is_deleted=False).update(is_deleted=True)
        return count
