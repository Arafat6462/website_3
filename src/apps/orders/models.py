"""
Orders Application Models - Phases 7-10: Complete Order Management.

This module contains models for complete e-commerce order flow:
- Cart: Shopping cart for users or guest sessions
- CartItem: Individual items in a cart
- Coupon: Promotional discount coupons
- CouponUsage: Tracking coupon usage
- ShippingZone: Area-based shipping costs
- TaxRule: Tax calculation rules
- Order: Customer orders
- OrderItem: Items in an order
- OrderStatusLog: Order status change history
- PaymentTransaction: Payment records
- ReturnRequest: Product return requests
"""

from datetime import timedelta
from typing import Any
import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import SoftDeleteModel, TimeStampedModel
from apps.core.managers import SoftDeleteManager, SoftDeleteAllManager


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
    order = models.ForeignKey(
        "Order",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="coupon_usages",
    )
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


class ShippingZone(TimeStampedModel):
    """
    Shipping zone with area-based delivery costs.

    Groups delivery areas by shipping cost and delivery time.
    Supports free shipping thresholds.

    Attributes:
        name: Zone name (e.g., "Dhaka City", "Outside Dhaka")
        areas: JSON list of areas/districts in this zone
        shipping_cost: Standard delivery cost for this zone
        free_shipping_threshold: Order amount for free shipping (None = no free shipping)
        estimated_days: Delivery time estimate (e.g., "1-2", "3-5")
        is_active: Enable/disable zone
        sort_order: Display order
    """

    name = models.CharField(max_length=200)
    areas = models.JSONField(
        default=list,
        help_text="List of areas/districts (e.g., ['Dhaka', 'Gazipur', 'Narayanganj'])",
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Delivery cost for this zone",
    )
    free_shipping_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Order amount for free shipping (blank = no free shipping)",
    )
    estimated_days = models.CharField(
        max_length=50,
        blank=True,
        help_text="Delivery estimate (e.g., '1-2 days', '3-5 business days')",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "orders_shipping_zone"
        verbose_name = "Shipping Zone"
        verbose_name_plural = "Shipping Zones"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} (৳{self.shipping_cost})"

    @property
    def has_free_shipping(self) -> bool:
        """Check if zone offers free shipping."""
        return self.free_shipping_threshold is not None

    def calculate_shipping_cost(self, order_amount: float) -> float:
        """
        Calculate shipping cost for given order amount.

        Args:
            order_amount: Order subtotal

        Returns:
            Shipping cost (0 if free shipping applies)

        Example:
            zone = ShippingZone.objects.get(name='Dhaka City')
            cost = zone.calculate_shipping_cost(500.00)  # Returns 0 if threshold is 500
        """
        if self.free_shipping_threshold and order_amount >= float(
            self.free_shipping_threshold
        ):
            return 0.0
        return float(self.shipping_cost)


class TaxRule(TimeStampedModel):
    """
    Tax rule for order tax calculation.

    Supports percentage and fixed tax types.
    Multiple rules can be applied based on priority.

    Attributes:
        name: Tax name (e.g., "VAT", "Service Charge")
        type: Tax type (percentage or fixed)
        rate: Tax rate (percentage 0-100 or fixed amount)
        is_active: Enable/disable rule
        priority: Application order (lower = applied first)
    """

    TAX_TYPE_CHOICES = [
        ("percentage", "Percentage"),
        ("fixed", "Fixed Amount"),
    ]

    name = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=TAX_TYPE_CHOICES)
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Percentage (0-100) or fixed amount",
    )
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(
        default=0, help_text="Lower priority applied first"
    )

    class Meta:
        db_table = "orders_tax_rule"
        verbose_name = "Tax Rule"
        verbose_name_plural = "Tax Rules"
        ordering = ["priority", "name"]
        indexes = [
            models.Index(fields=["is_active", "priority"]),
        ]

    def __str__(self) -> str:
        if self.type == "percentage":
            return f"{self.name} ({self.rate}%)"
        return f"{self.name} (৳{self.rate})"

    def calculate_tax(self, amount: float) -> float:
        """
        Calculate tax for given amount.

        Args:
            amount: Amount to calculate tax on

        Returns:
            Tax amount

        Example:
            vat = TaxRule.objects.get(name='VAT')
            tax = vat.calculate_tax(1000.00)  # Returns 150 if rate is 15%
        """
        if self.type == "percentage":
            return round(amount * (float(self.rate) / 100), 2)
        return float(self.rate)


class Order(SoftDeleteModel):
    """
    Customer order with complete transaction details.

    Stores customer information, items, pricing, payment, and shipping details.
    Supports both authenticated users and guest checkout.

    Attributes:
        public_id: UUID for external reference (hide sequential IDs)
        order_number: Human-readable order number (e.g., ORD-2026-00001)
        user: User who placed order (nullable for guest checkout)
        shipping_zone: Selected shipping zone
        
        Customer Info:
        customer_name, customer_email, customer_phone: Contact details
        shipping_address_*: Full delivery address
        
        Order Status:
        status: Current order status (pending, confirmed, shipped, etc.)
        payment_method: Payment method used (cod, bkash, card, etc.)
        payment_status: Payment state (pending, paid, failed, refunded)
        
        Pricing:
        subtotal: Cart items total
        discount_amount: Coupon discount applied
        shipping_cost: Delivery cost
        tax_amount: Tax total
        total: Final order total
        
        Coupon:
        coupon: Applied coupon (nullable)
        coupon_code: Stored code for reference
        
        Notes:
        customer_notes: Customer's delivery instructions
        admin_notes: Internal staff notes
        
        Shipping:
        tracking_number: Courier tracking number
        courier_name: Delivery service name
        estimated_delivery: Expected delivery date
        
        Timestamps:
        confirmed_at, shipped_at, delivered_at, cancelled_at: Status timestamps
        ip_address: Customer IP for fraud detection
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("cod", "Cash on Delivery"),
        ("bkash", "bKash"),
        ("nagad", "Nagad"),
        ("card", "Credit/Debit Card"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    # Identification
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    order_number = models.CharField(max_length=50, unique=True, db_index=True)

    # User (nullable for guest checkout)
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    # Shipping zone
    shipping_zone = models.ForeignKey(
        ShippingZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    # Customer information
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)

    # Shipping address
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_area = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20, blank=True)

    # Order status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    payment_reference = models.CharField(max_length=255, blank=True)

    # Coupon
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    coupon_code = models.CharField(max_length=50, blank=True)

    # Notes
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    # Shipping tracking
    tracking_number = models.CharField(max_length=100, blank=True)
    courier_name = models.CharField(max_length=100, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)

    # Status timestamps
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Managers
    objects = SoftDeleteManager()
    all_objects = SoftDeleteAllManager()

    class Meta:
        db_table = "orders_order"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["customer_email"]),
            models.Index(fields=["customer_phone"]),
        ]

    def __str__(self) -> str:
        return f"{self.order_number} - {self.customer_name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Generate order number on creation."""
        if not self.order_number:
            from apps.core.utils import generate_order_number

            self.order_number = generate_order_number()
        super().save(*args, **kwargs)

    @property
    def is_paid(self) -> bool:
        """Check if order is paid."""
        return self.payment_status == "paid"

    @property
    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled."""
        return self.status in ["pending", "confirmed"]

    @property
    def is_completed(self) -> bool:
        """Check if order is completed."""
        return self.status == "delivered"


class OrderItem(models.Model):
    """
    Individual item in an order.

    Stores snapshot of product/variant at time of purchase.
    Prices and attributes frozen to preserve order history.

    Attributes:
        order: Parent order
        variant: Product variant ordered
        product_name: Product name (snapshot)
        variant_name: Variant name (snapshot)
        sku: Variant SKU (snapshot)
        unit_price: Price at time of order
        quantity: Quantity ordered
        line_total: Total for this line (unit_price * quantity)
        attributes_snapshot: JSON of variant attributes at purchase time
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )

    # Snapshot data (preserved even if product deleted)
    product_name = models.CharField(max_length=255)
    variant_name = models.CharField(max_length=255, blank=True)
    sku = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    # Attributes at purchase time (for reference)
    attributes_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "orders_order_item"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.product_name} x{self.quantity}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Calculate line total on save."""
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusLog(models.Model):
    """
    Log of order status changes.

    Tracks who changed status, when, and why.
    Provides complete audit trail for orders.

    Attributes:
        order: Parent order
        from_status: Previous status
        to_status: New status
        changed_by: User who made the change
        notes: Reason for change
        created_at: When change occurred
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="status_logs"
    )
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_changes",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders_order_status_log"
        verbose_name = "Order Status Log"
        verbose_name_plural = "Order Status Logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.order.order_number}: {self.from_status} → {self.to_status}"


class PaymentTransaction(models.Model):
    """
    Payment transaction record.

    Logs all payment attempts for orders.
    Stores provider responses for debugging and reconciliation.

    Attributes:
        order: Parent order
        provider: Payment provider (cod, bkash, nagad, etc.)
        amount: Transaction amount
        status: Transaction status (pending, completed, failed, refunded)
        provider_reference: Provider's transaction ID
        raw_response: Full API response (JSON)
        created_at: Transaction timestamp
    """

    PROVIDER_CHOICES = [
        ("cod", "Cash on Delivery"),
        ("bkash", "bKash"),
        ("nagad", "Nagad"),
        ("sslcommerz", "SSLCommerz"),
        ("card", "Credit/Debit Card"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="payment_transactions"
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    provider_reference = models.CharField(max_length=255, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders_payment_transaction"
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "-created_at"]),
            models.Index(fields=["provider", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.order.order_number} - {self.provider} (৳{self.amount})"


class ReturnRequest(models.Model):
    """
    Product return request.

    Handles customer return requests with approval workflow.

    Attributes:
        order: Parent order
        user: User requesting return
        status: Return status (requested, approved, rejected, completed, refunded)
        reason: Return reason
        customer_notes: Customer's explanation
        admin_notes: Internal processing notes
        items_snapshot: JSON of items being returned
        refund_amount: Amount to refund
        processed_by: Admin who processed request
        processed_at: Processing timestamp
    """

    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
        ("refunded", "Refunded"),
    ]

    REASON_CHOICES = [
        ("damaged", "Damaged Product"),
        ("wrong_item", "Wrong Item Delivered"),
        ("not_as_described", "Not as Described"),
        ("changed_mind", "Changed Mind"),
        ("other", "Other"),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="return_requests"
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="return_requests",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="requested", db_index=True
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    items_snapshot = models.JSONField(default=dict, blank=True)
    refund_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    processed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_returns",
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders_return_request"
        verbose_name = "Return Request"
        verbose_name_plural = "Return Requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["order"]),
        ]

    def __str__(self) -> str:
        return f"Return #{self.id} - {self.order.order_number}"

