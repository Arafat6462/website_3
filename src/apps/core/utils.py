"""
Core Utility Functions.

This module provides utility functions used across the application:
- Slug generation with uniqueness guarantee
- SKU generation for product variants
- Other common helper functions

Usage:
    from apps.core.utils import generate_unique_slug, generate_sku

    slug = generate_unique_slug(Product, "Cotton T-Shirt")
    # Returns: "cotton-t-shirt" or "cotton-t-shirt-2" if exists

    sku = generate_sku("TEE", {"size": "M", "color": "Red"})
    # Returns: "TEE-M-RED"
"""

import random
import string
import uuid
from typing import TYPE_CHECKING, Any

from django.db import models
from django.utils.text import slugify

if TYPE_CHECKING:
    from django.db.models import Model


def generate_unique_slug(
    model_class: type["Model"],
    value: str,
    slug_field: str = "slug",
    instance: "Model | None" = None,
    max_length: int = 255,
) -> str:
    """
    Generate a unique slug for a model instance.

    Creates a slug from the given value, then checks if it exists in the
    database. If it does, appends a number suffix until unique.

    Args:
        model_class: The Django model class to check uniqueness against.
        value: The string to slugify (usually the name/title).
        slug_field: The name of the slug field in the model.
        instance: If updating, the current instance to exclude from check.
        max_length: Maximum length of the generated slug.

    Returns:
        A unique slug string.

    Example:
        # For new product
        slug = generate_unique_slug(Product, "Cotton T-Shirt")

        # For updating (exclude self from uniqueness check)
        slug = generate_unique_slug(Product, "New Name", instance=product)
    """
    # Create base slug
    base_slug = slugify(value)[:max_length]

    if not base_slug:
        # If slugify returns empty (e.g., non-ASCII characters only)
        base_slug = f"item-{uuid.uuid4().hex[:8]}"

    slug = base_slug
    counter = 1

    # Build queryset for checking existence
    queryset = model_class.objects.all()

    # If updating existing instance, exclude it from uniqueness check
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    # Keep trying until we find a unique slug
    while queryset.filter(**{slug_field: slug}).exists():
        # Calculate available space for counter suffix
        suffix = f"-{counter}"
        max_base_length = max_length - len(suffix)
        slug = f"{base_slug[:max_base_length]}{suffix}"
        counter += 1

        # Safety limit to prevent infinite loops
        if counter > 1000:
            # Fallback to UUID-based slug
            slug = f"{base_slug[:max_length - 9]}-{uuid.uuid4().hex[:8]}"
            break

    return slug


def generate_sku(
    prefix: str,
    attributes: dict[str, str] | None = None,
    random_suffix: bool = True,
) -> str:
    """
    Generate a SKU (Stock Keeping Unit) for a product variant.

    Creates a structured SKU from a prefix and attribute values.
    Format: PREFIX-ATTR1-ATTR2-RANDOM (e.g., "TEE-M-RED-A1B2")

    Args:
        prefix: Product prefix/code (e.g., "TEE", "JEAN", "PHONE").
        attributes: Dictionary of variant attributes (e.g., {"size": "M"}).
        random_suffix: Whether to append random characters for uniqueness.

    Returns:
        Generated SKU string, uppercase.

    Example:
        sku = generate_sku("TEE", {"size": "M", "color": "Red"})
        # Returns: "TEE-M-RED-A1B2"

        sku = generate_sku("PHONE", {"storage": "128GB"}, random_suffix=False)
        # Returns: "PHONE-128GB"
    """
    parts = [prefix.upper()]

    if attributes:
        for value in attributes.values():
            # Clean and format attribute value
            cleaned = str(value).upper().replace(" ", "").replace("-", "")[:10]
            if cleaned:
                parts.append(cleaned)

    if random_suffix:
        # Add 4 random alphanumeric characters
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(suffix)

    return "-".join(parts)


def generate_order_number(prefix: str = "ORD") -> str:
    """
    Generate a unique order number.

    Format: PREFIX-YYYY-XXXXXXXX (e.g., "ORD-2026-A1B2C3D4")

    Args:
        prefix: Order number prefix. Defaults to "ORD".

    Returns:
        Generated order number string.

    Example:
        order_number = generate_order_number()
        # Returns: "ORD-2026-A1B2C3D4"
    """
    from django.utils import timezone

    year = timezone.now().year
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    return f"{prefix}-{year}-{random_part}"


def generate_public_id() -> str:
    """
    Generate a public-facing UUID for resources.

    Uses UUID4 for randomness. This ID is exposed in APIs
    instead of sequential integer IDs for security.

    Returns:
        UUID string (e.g., "f47ac10b-58cc-4372-a567-0e02b2c3d479").

    Example:
        public_id = generate_public_id()
        # Use in models: public_id = models.UUIDField(default=generate_public_id)
    """
    return str(uuid.uuid4())


def truncate_string(value: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to maximum length with suffix.

    Args:
        value: String to truncate.
        max_length: Maximum total length including suffix.
        suffix: String to append if truncated. Defaults to "...".

    Returns:
        Truncated string or original if within limit.

    Example:
        truncate_string("Hello World", 8)
        # Returns: "Hello..."
    """
    if len(value) <= max_length:
        return value

    return value[: max_length - len(suffix)] + suffix


def normalize_phone_number(phone: str) -> str:
    """
    Normalize a Bangladeshi phone number.

    Removes spaces, dashes, and normalizes to a consistent format.
    Handles formats: 01712345678, +8801712345678, 8801712345678

    Args:
        phone: Phone number string to normalize.

    Returns:
        Normalized phone number (e.g., "01712345678").

    Example:
        normalize_phone_number("+880 171-234-5678")
        # Returns: "01712345678"
    """
    # Remove all non-digit characters
    digits_only = "".join(filter(str.isdigit, phone))

    # Handle Bangladesh country code
    if digits_only.startswith("880"):
        digits_only = "0" + digits_only[3:]
    elif digits_only.startswith("0088"):
        digits_only = "0" + digits_only[4:]

    return digits_only


def format_price(amount: Any, currency_symbol: str = "৳") -> str:
    """
    Format a price for display with currency symbol.

    Args:
        amount: Numeric amount to format.
        currency_symbol: Currency symbol. Defaults to "৳" (Taka).

    Returns:
        Formatted price string (e.g., "৳1,500.00").

    Example:
        format_price(1500)
        # Returns: "৳1,500.00"
    """
    from decimal import Decimal

    if amount is None:
        return f"{currency_symbol}0.00"

    amount = Decimal(str(amount))
    formatted = f"{amount:,.2f}"

    return f"{currency_symbol}{formatted}"


def generate_order_number() -> str:
    """
    Generate a unique order number.

    Format: ORD-YYYY-NNNNN
    Example: ORD-2026-00001

    Returns:
        Unique order number string

    Example:
        order_number = generate_order_number()
        # Returns: "ORD-2026-00001"
    """
    from datetime import datetime

    from apps.orders.models import Order

    year = datetime.now().year
    prefix = f"ORD-{year}-"

    # Get last order number for this year
    last_order = (
        Order.all_objects.filter(order_number__startswith=prefix)
        .order_by("-order_number")
        .first()
    )

    if last_order:
        # Extract number and increment
        last_number = int(last_order.order_number.split("-")[-1])
        next_number = last_number + 1
    else:
        next_number = 1

    # Format with 5 digits
    return f"{prefix}{next_number:05d}"

