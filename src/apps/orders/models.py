"""
Orders Application Models - Phase 7: Cart System.

This module contains models for shopping cart functionality:
- Cart: Shopping cart for users or guest sessions
- CartItem: Individual items in a cart

Future phases will add:
- Order, OrderItem, OrderStatusLog (Phase 10)
- ShippingZone, TaxRule (Phase 9)
"""

from datetime import timedelta
from typing import Any

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


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
