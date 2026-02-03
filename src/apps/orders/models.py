"""
Orders Application Models - Phase 7: Cart System, Phase 8: Coupon System.

This module contains models for shopping cart and coupon functionality:
- Cart: Shopping cart for users or guest sessions
- CartItem: Individual items in a cart
- Coupon: Promotional discount coupons
- CouponUsage: Tracking coupon usage

Future phases will add:
- Order, OrderItem, OrderStatusLog (Phase 10)
- ShippingZone, TaxRule (Phase 9)
"""

from datetime import timedelta
from typing import Any

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Cart(TimeStampedModel):
    """
    Shopping cart model - stores items for users or guest sessions.

    A cart can belong to:
    - Authenticated user (user field set, session_key null)
    - Guest session (session_key set, user field null)

    Guest carts expire after 30 days. User carts never expire.
    When a guest logs in, their session cart is merged with user cart.

    Attributes:
        public_id: UUID for API access.
        user: Authenticated user who owns this cart (null for guests).
        session_key: Session identifier for guest carts (null for users).
        expires_at: Expiration date for guest carts (null for user carts).

    Example:
        # Create user cart
        cart = Cart.objects.create(user=user)

        # Create guest cart (30-day expiry)
        cart = Cart.objects.create(
            session_key='abc123xyz',
            expires_at=timezone.now() + timedelta(days=30)
        )
    """

    public_id = models.UUIDField(unique=True, editable=False)
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="cart",
        null=True,
        blank=True,
        help_text="Cart owner (null for guest carts)",
    )
    session_key = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        help_text="Session identifier for guest carts",
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Expiration date for guest carts (null for user carts)",
    )

    class Meta:
        db_table = "orders_cart"
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        indexes = [
            models.Index(fields=["session_key"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Guest Cart ({self.session_key[:8]}...)"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Generate public_id and set expiry for guest carts."""
        import uuid

        if not self.public_id:
            self.public_id = uuid.uuid4()

        # Set expiry for guest carts (30 days from now)
        if not self.user and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)

        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        """Check if cart has expired."""
        if not self.expires_at:
            return False  # User carts never expire
        return timezone.now() > self.expires_at

    @property
    def item_count(self) -> int:
        """Get total number of items in cart."""
        return self.items.aggregate(total=models.Sum("quantity"))["total"] or 0

    @property
    def subtotal(self) -> float:
        """Calculate cart subtotal."""
        total = 0.0
        for item in self.items.all():
            total += item.line_total
        return total


class CartItem(TimeStampedModel):
    """
    Cart item model - represents a single item in a shopping cart.

    Each item stores:
    - The variant being purchased
    - Quantity
    - Unit price at time of addition (snapshot for price stability)

    Attributes:
        cart: The cart this item belongs to.
        variant: The product variant being purchased.
        quantity: Number of units.
        unit_price: Price per unit (snapshot at time of addition).

    Example:
        CartItem.objects.create(
            cart=cart,
            variant=variant,
            quantity=2,
            unit_price=variant.effective_price
        )
    """

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "products.ProductVariant", on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)], help_text="Number of units"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price per unit (snapshot)",
    )

    class Meta:
        db_table = "orders_cartitem"
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        unique_together = [("cart", "variant")]
        indexes = [
            models.Index(fields=["cart"]),
            models.Index(fields=["variant"]),
        ]

    def __str__(self) -> str:
        return f"{self.variant.sku} x{self.quantity} in {self.cart}"

    @property
    def line_total(self) -> float:
        """Calculate total for this line item."""
        return float(self.unit_price) * self.quantity

    def update_price(self) -> None:
        """Update unit_price to current variant price."""
        self.unit_price = self.variant.effective_price
        self.save(update_fields=["unit_price", "updated_at"])


class Coupon(SoftDeleteModel):
    """
    Promotional coupon for discounts.

    Supports percentage and fixed discounts with various restrictions:
    - Usage limits (global and per-user)
    - Minimum order amount
    - Date range validity
    - First order only restriction
    - Product/category restrictions

    Attributes:
        code: Unique coupon code (e.g., "SAVE10", "WELCOME2026")
        name: Human-readable name for admin
        description: Details about the coupon
        discount_type: Either "percentage" or "fixed"
        discount_value: Percentage (0-100) or fixed amount
        minimum_order: Minimum cart value required
        maximum_discount: Cap for percentage discounts
        usage_limit: Total times coupon can be used (None = unlimited)
        usage_limit_per_user: Per-user limit (None = unlimited)
        times_used: Current usage count
        valid_from: Coupon activation date
        valid_to: Coupon expiry date
        is_active: Can be deactivated without deleting
        first_order_only: Only for customers with no previous orders
        applicable_categories: JSON list of category IDs
        applicable_products: JSON list of product IDs
    """

    DISCOUNT_TYPE_CHOICES = [
        ("percentage", "Percentage"),
        ("fixed", "Fixed Amount"),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Percentage (0-100) or fixed amount",
    )

    minimum_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Minimum cart value to apply coupon",
    )
    maximum_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum discount for percentage coupons",
    )

    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total times coupon can be used (blank = unlimited)",
    )
    usage_limit_per_user = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Per-user usage limit (blank = unlimited)",
    )
    times_used = models.PositiveIntegerField(default=0)

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    first_order_only = models.BooleanField(
        default=False, help_text="Only for customers with no previous orders"
    )

    applicable_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="List of category IDs (empty = all categories)",
    )
    applicable_products = models.JSONField(
        default=list,
        blank=True,
        help_text="List of product IDs (empty = all products)",
    )

    class Meta:
        db_table = "orders_coupon"
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active", "valid_from", "valid_to"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"

    @property
    def is_valid(self) -> bool:
        """Check if coupon is currently valid (not expired or inactive)."""
        from django.utils import timezone

        now = timezone.now()
        return (
            self.is_active
            and not self.is_deleted
            and self.valid_from <= now <= self.valid_to
        )

    @property
    def usage_remaining(self) -> int | None:
        """Get remaining uses (None if unlimited)."""
        if self.usage_limit is None:
            return None
        return max(0, self.usage_limit - self.times_used)

    @property
    def is_exhausted(self) -> bool:
        """Check if coupon has reached usage limit."""
        if self.usage_limit is None:
            return False
        return self.times_used >= self.usage_limit


class CouponUsage(models.Model):
    """
    Track coupon usage per customer/order.

    Stores who used which coupon, when, and the discount amount.
    Supports both authenticated users and guest checkout.

    Attributes:
        coupon: The coupon that was used
        user: User who used it (nullable for guests)
        order: Order it was applied to (nullable until checkout)
        guest_identifier: Email/phone for guest tracking
        discount_amount: Actual discount given
        created_at: When coupon was applied
    """

    coupon = models.ForeignKey(
        Coupon, on_delete=models.CASCADE, related_name="usages"
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupon_usages",
    )
    # order field will be added in Phase 10
    # order = models.ForeignKey(
    #     "Order",
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    #     related_name="coupon_usages",
    # )
    guest_identifier = models.CharField(
        max_length=255,
        blank=True,
        help_text="Email or phone for guest users",
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders_coupon_usage"
        verbose_name = "Coupon Usage"
        verbose_name_plural = "Coupon Usages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["coupon", "user"]),
            models.Index(fields=["coupon", "guest_identifier"]),
        ]

    def __str__(self) -> str:
        user_info = self.user.email if self.user else self.guest_identifier
        return f"{self.coupon.code} used by {user_info}"
