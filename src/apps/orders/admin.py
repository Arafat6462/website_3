"""
Orders Application Admin Configuration - Complete Order Management (Phases 7-10).
"""

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.core.admin import BaseModelAdmin, TimeStampedAdminMixin
from apps.orders.models import (
    Cart,
    CartItem,
    Coupon,
    CouponUsage,
    Order,
    OrderItem,
    OrderStatusLog,
    PaymentTransaction,
    ReturnRequest,
    ShippingZone,
    TaxRule,
)


class CartItemInline(admin.TabularInline):
    """
    Inline admin for cart items.

    Shows items directly in cart admin.
    """

    model = CartItem
    extra = 0
    fields = ["variant", "quantity", "unit_price", "line_total_display"]
    readonly_fields = ["line_total_display", "unit_price"]
    autocomplete_fields = ["variant"]

    @admin.display(description="Line Total")
    def line_total_display(self, obj: CartItem) -> str:
        """Display line total."""
        if obj.pk:
            return format_html("<strong>৳{:.2f}</strong>", obj.line_total)
        return "-"


@admin.register(Cart)
class CartAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for Cart model.

    Features:
    - View all carts (user and guest)
    - Filter by user/guest, expiry
    - View cart contents inline
    - See totals and item counts
    """

    list_display = [
        "cart_id",
        "owner_display",
        "item_count_display",
        "subtotal_display",
        "status_badge",
        "created_at",
    ]
    list_filter = [
        "created_at",
        ("user", admin.EmptyFieldListFilter),
        ("expires_at", admin.EmptyFieldListFilter),
    ]
    search_fields = ["public_id", "user__email", "session_key"]
    readonly_fields = ["public_id", "item_count_display", "subtotal_display", "created_at", "updated_at"]
    fieldsets = [
        (
            "Cart Information",
            {
                "fields": [
                    "public_id",
                    "user",
                    "session_key",
                    "expires_at",
                ]
            },
        ),
        (
            "Statistics",
            {
                "fields": [
                    "item_count_display",
                    "subtotal_display",
                ]
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]
    inlines = [CartItemInline]
    autocomplete_fields = ["user"]

    @admin.display(description="Cart ID")
    def cart_id(self, obj: Cart) -> str:
        """Display cart ID."""
        return str(obj.public_id)[:8]

    @admin.display(description="Owner")
    def owner_display(self, obj: Cart) -> str:
        """Display cart owner."""
        if obj.user:
            return format_html(
                '<a href="/admin/users/user/{}/change/">{}</a>',
                obj.user.pk,
                obj.user.email,
            )
        return format_html(
            '<span style="color: gray;">Guest ({}...)</span>',
            obj.session_key[:8] if obj.session_key else "unknown",
        )

    @admin.display(description="Items")
    def item_count_display(self, obj: Cart) -> str:
        """Display item count."""
        count = obj.item_count
        if count == 0:
            return format_html('<span style="color: gray;">Empty</span>')
        return format_html('<strong>{}</strong> items', count)

    @admin.display(description="Subtotal")
    def subtotal_display(self, obj: Cart) -> str:
        """Display cart subtotal."""
        subtotal = obj.subtotal
        if subtotal == 0:
            return format_html('<span style="color: gray;">৳0.00</span>')
        return format_html('<strong>৳{:.2f}</strong>', subtotal)

    @admin.display(description="Status")
    def status_badge(self, obj: Cart) -> str:
        """Display cart status."""
        if obj.user:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">User Cart</span>'
            )
        elif obj.is_expired:
            return format_html(
                '<span style="background-color: #dc3545; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Expired</span>'
            )
        else:
            days_left = (obj.expires_at - obj.created_at).days if obj.expires_at else 0
            color = "#ffc107" if days_left < 7 else "#17a2b8"
            return format_html(
                '<span style="background-color: {}; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Guest ({} days)</span>',
                color,
                days_left,
            )

    @admin.action(description="Clear selected carts")
    def clear_carts(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Clear all items from selected carts."""
        count = 0
        for cart in queryset:
            count += cart.items.count()
            cart.items.all().delete()
        self.message_user(request, f"Cleared {count} items from {queryset.count()} carts.")

    @admin.action(description="Delete expired guest carts")
    def delete_expired(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Delete expired guest carts."""
        from django.utils import timezone

        expired = queryset.filter(user__isnull=True, expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        self.message_user(request, f"Deleted {count} expired guest carts.")

    actions = ["clear_carts", "delete_expired"]


@admin.register(CartItem)
class CartItemAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for CartItem model.

    View individual cart items across all carts.
    """

    list_display = [
        "cart_owner",
        "variant",
        "quantity",
        "unit_price",
        "line_total_display",
        "created_at",
    ]
    list_filter = [
        "created_at",
        "variant__product__category",
    ]
    search_fields = [
        "cart__user__email",
        "cart__session_key",
        "variant__sku",
        "variant__name",
    ]
    readonly_fields = ["line_total_display", "created_at", "updated_at"]
    autocomplete_fields = ["cart", "variant"]

    @admin.display(description="Cart Owner")
    def cart_owner(self, obj: CartItem) -> str:
        """Display cart owner."""
        if obj.cart.user:
            return obj.cart.user.email
        return f"Guest ({obj.cart.session_key[:8]}...)"

    @admin.display(description="Line Total")
    def line_total_display(self, obj: CartItem) -> str:
        """Display line total."""
        return format_html("<strong>৳{:.2f}</strong>", obj.line_total)


class CouponUsageInline(admin.TabularInline):
    """
    Inline admin for coupon usage.

    Shows usage history directly in coupon admin.
    """

    model = CouponUsage
    extra = 0
    fields = ["user", "guest_identifier", "discount_amount", "created_at"]
    readonly_fields = ["user", "guest_identifier", "discount_amount", "created_at"]
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Disable manual addition."""
        return False


@admin.register(Coupon)
class CouponAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for Coupon model.

    Features:
    - Create/edit coupons
    - View usage statistics
    - Filter by status, type, validity
    - Quick activate/deactivate
    - View usage history inline
    """

    list_display = [
        "code",
        "name",
        "discount_badge",
        "usage_display",
        "validity_badge",
        "status_badge",
        "created_at",
    ]
    list_filter = [
        "discount_type",
        "is_active",
        "first_order_only",
        "created_at",
        "valid_from",
        "valid_to",
    ]
    search_fields = ["code", "name", "description"]
    readonly_fields = [
        "times_used",
        "usage_display",
        "usage_remaining_display",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        (
            "Basic Information",
            {
                "fields": [
                    "code",
                    "name",
                    "description",
                    "is_active",
                ]
            },
        ),
        (
            "Discount Configuration",
            {
                "fields": [
                    "discount_type",
                    "discount_value",
                    "minimum_order",
                    "maximum_discount",
                ]
            },
        ),
        (
            "Usage Limits",
            {
                "fields": [
                    "usage_limit",
                    "usage_limit_per_user",
                    "times_used",
                    "usage_remaining_display",
                ]
            },
        ),
        (
            "Validity Period",
            {
                "fields": [
                    "valid_from",
                    "valid_to",
                ]
            },
        ),
        (
            "Restrictions",
            {
                "fields": [
                    "first_order_only",
                    "applicable_categories",
                    "applicable_products",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]
    inlines = [CouponUsageInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Include soft-deleted coupons."""
        return Coupon.all_objects.all()

    @admin.display(description="Discount")
    def discount_badge(self, obj: Coupon) -> str:
        """Display discount value."""
        if obj.discount_type == "percentage":
            return format_html(
                '<span style="background-color: #007bff; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                '{}% OFF</span>',
                obj.discount_value,
            )
        else:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                '৳{} OFF</span>',
                obj.discount_value,
            )

    @admin.display(description="Usage")
    def usage_display(self, obj: Coupon) -> str:
        """Display usage count."""
        if obj.usage_limit is None:
            return format_html(
                '<span style="color: green;">{} / Unlimited</span>',
                obj.times_used,
            )
        
        percentage = (obj.times_used / obj.usage_limit * 100) if obj.usage_limit > 0 else 0
        color = "#dc3545" if percentage >= 90 else "#ffc107" if percentage >= 70 else "#28a745"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} / {}</span>',
            color,
            obj.times_used,
            obj.usage_limit,
        )

    @admin.display(description="Usage Remaining")
    def usage_remaining_display(self, obj: Coupon) -> str:
        """Display remaining uses."""
        if obj.usage_limit is None:
            return format_html('<span style="color: green;">Unlimited</span>')
        
        remaining = obj.usage_remaining
        if remaining == 0:
            return format_html('<span style="color: red; font-weight: bold;">Exhausted</span>')
        
        return format_html('<span style="color: green;">{} remaining</span>', remaining)

    @admin.display(description="Validity")
    def validity_badge(self, obj: Coupon) -> str:
        """Display validity status."""
        from django.utils import timezone

        now = timezone.now()
        
        if now < obj.valid_from:
            days_until = (obj.valid_from - now).days
            return format_html(
                '<span style="background-color: #6c757d; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Starts in {} days</span>',
                days_until,
            )
        elif now > obj.valid_to:
            return format_html(
                '<span style="background-color: #dc3545; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Expired</span>'
            )
        else:
            days_left = (obj.valid_to - now).days
            color = "#ffc107" if days_left < 7 else "#28a745"
            return format_html(
                '<span style="background-color: {}; color: white; '
                'padding: 3px 10px; border-radius: 3px;">{} days left</span>',
                color,
                days_left,
            )

    @admin.display(description="Status")
    def status_badge(self, obj: Coupon) -> str:
        """Display status badge."""
        if obj.is_deleted:
            return format_html(
                '<span style="background-color: #dc3545; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Deleted</span>'
            )
        elif not obj.is_active:
            return format_html(
                '<span style="background-color: #6c757d; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Inactive</span>'
            )
        elif obj.is_exhausted:
            return format_html(
                '<span style="background-color: #ffc107; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Exhausted</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Active</span>'
            )

    @admin.action(description="Activate selected coupons")
    def activate_coupons(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Activate selected coupons."""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} coupons.")

    @admin.action(description="Deactivate selected coupons")
    def deactivate_coupons(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Deactivate selected coupons."""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} coupons.")

    @admin.action(description="Soft delete selected coupons")
    def soft_delete_coupons(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Soft delete selected coupons."""
        count = 0
        for coupon in queryset:
            if not coupon.is_deleted:
                coupon.delete()
                count += 1
        self.message_user(request, f"Deleted {count} coupons.")

    actions = ["activate_coupons", "deactivate_coupons", "soft_delete_coupons"]


@admin.register(CouponUsage)
class CouponUsageAdmin(BaseModelAdmin):
    """
    Admin interface for CouponUsage model.

    Read-only view of all coupon usage history.
    """

    list_display = [
        "coupon_code",
        "user_display",
        "discount_amount_display",
        # "order_link",  # Will be added in Phase 10
        "created_at",
    ]
    list_filter = [
        "created_at",
        "coupon__discount_type",
    ]
    search_fields = [
        "coupon__code",
        "user__email",
        "guest_identifier",
    ]
    readonly_fields = [
        "coupon",
        "user",
        # "order",  # Will be added in Phase 10
        "guest_identifier",
        "discount_amount",
        "created_at",
    ]
    autocomplete_fields = []

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable manual addition."""
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Disable deletion."""
        return False

    @admin.display(description="Coupon")
    def coupon_code(self, obj: CouponUsage) -> str:
        """Display coupon code."""
        return format_html(
            '<a href="/admin/orders/coupon/{}/change/"><strong>{}</strong></a>',
            obj.coupon.pk,
            obj.coupon.code,
        )

    @admin.display(description="User")
    def user_display(self, obj: CouponUsage) -> str:
        """Display user or guest."""
        if obj.user:
            return format_html(
                '<a href="/admin/users/user/{}/change/">{}</a>',
                obj.user.pk,
                obj.user.email,
            )
        return format_html(
            '<span style="color: gray;">Guest: {}</span>',
            obj.guest_identifier or "Unknown",
        )

    @admin.display(description="Discount")
    def discount_amount_display(self, obj: CouponUsage) -> str:
        """Display discount amount."""
        return format_html(
            '<strong style="color: green;">৳{:.2f}</strong>',
            obj.discount_amount,
        )

    # order_link method will be added in Phase 10 when Order model exists
    # @admin.display(description="Order")
    # def order_link(self, obj: CouponUsage) -> str:
    #     """Display order link."""
    #     if obj.order:
    #         return format_html(
    #             '<a href="/admin/orders/order/{}/change/">{}</a>',
    #             obj.order.pk,
    #             obj.order.order_number,
    #         )
    #     return format_html('<span style="color: gray;">Pending</span>')


@admin.register(ShippingZone)
class ShippingZoneAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for ShippingZone model.

    Features:
    - Manage shipping zones and costs
    - Configure free shipping thresholds
    - Set delivery estimates
    - Drag-drop zone ordering
    """

    list_display = [
        "name",
        "shipping_cost_display",
        "free_shipping_display",
        "areas_display",
        "estimated_days",
        "status_badge",
        "sort_order",
    ]
    list_filter = [
        "is_active",
        "created_at",
    ]
    search_fields = ["name", "areas"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (
            "Zone Information",
            {
                "fields": [
                    "name",
                    "areas",
                    "is_active",
                    "sort_order",
                ]
            },
        ),
        (
            "Shipping Configuration",
            {
                "fields": [
                    "shipping_cost",
                    "free_shipping_threshold",
                    "estimated_days",
                ]
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Shipping Cost")
    def shipping_cost_display(self, obj: ShippingZone) -> str:
        """Display shipping cost."""
        return format_html(
            '<strong style="color: #007bff;">৳{:.2f}</strong>',
            obj.shipping_cost,
        )

    @admin.display(description="Free Shipping")
    def free_shipping_display(self, obj: ShippingZone) -> str:
        """Display free shipping threshold."""
        if obj.free_shipping_threshold:
            return format_html(
                '<span style="color: green;">Above ৳{:.2f}</span>',
                obj.free_shipping_threshold,
            )
        return format_html('<span style="color: gray;">Not available</span>')

    @admin.display(description="Areas")
    def areas_display(self, obj: ShippingZone) -> str:
        """Display areas count."""
        count = len(obj.areas) if obj.areas else 0
        if count == 0:
            return format_html('<span style="color: red;">No areas</span>')
        
        areas_preview = ", ".join(obj.areas[:3])
        if count > 3:
            areas_preview += f"... (+{count - 3} more)"
        
        return format_html(
            '<span title="{}">{} areas</span>',
            ", ".join(obj.areas),
            count,
        )

    @admin.display(description="Status")
    def status_badge(self, obj: ShippingZone) -> str:
        """Display status badge."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )

    @admin.action(description="Activate selected zones")
    def activate_zones(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Activate selected zones."""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} shipping zones.")

    @admin.action(description="Deactivate selected zones")
    def deactivate_zones(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Deactivate selected zones."""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} shipping zones.")

    actions = ["activate_zones", "deactivate_zones"]


@admin.register(TaxRule)
class TaxRuleAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for TaxRule model.

    Features:
    - Manage tax rules
    - Set priority order
    - Percentage or fixed taxes
    - Quick activate/deactivate
    """

    list_display = [
        "name",
        "tax_badge",
        "priority",
        "status_badge",
        "created_at",
    ]
    list_filter = [
        "type",
        "is_active",
        "created_at",
    ]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (
            "Tax Information",
            {
                "fields": [
                    "name",
                    "type",
                    "rate",
                    "is_active",
                    "priority",
                ]
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Tax")
    def tax_badge(self, obj: TaxRule) -> str:
        """Display tax rate badge."""
        if obj.type == "percentage":
            return format_html(
                '<span style="background-color: #007bff; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                '{}% Tax</span>',
                obj.rate,
            )
        else:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                '৳{} Tax</span>',
                obj.rate,
            )

    @admin.display(description="Status")
    def status_badge(self, obj: TaxRule) -> str:
        """Display status badge."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )

    @admin.action(description="Activate selected tax rules")
    def activate_rules(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Activate selected tax rules."""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} tax rules.")

    @admin.action(description="Deactivate selected tax rules")
    def deactivate_rules(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Deactivate selected tax rules."""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} tax rules.")

    actions = ["activate_rules", "deactivate_rules"]


class OrderItemInline(admin.TabularInline):
    """Inline admin for order items."""

    model = OrderItem
    extra = 0
    fields = ["product_name", "variant_name", "sku", "unit_price", "quantity", "line_total"]
    readonly_fields = ["product_name", "variant_name", "sku", "unit_price", "quantity", "line_total"]
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Disable manual addition."""
        return False


class OrderStatusLogInline(admin.TabularInline):
    """Inline admin for order status logs."""

    model = OrderStatusLog
    extra = 0
    fields = ["from_status", "to_status", "changed_by", "notes", "created_at"]
    readonly_fields = ["from_status", "to_status", "changed_by", "notes", "created_at"]
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Disable manual addition."""
        return False


class PaymentTransactionInline(admin.TabularInline):
    """Inline admin for payment transactions."""

    model = PaymentTransaction
    extra = 0
    fields = ["provider", "amount", "status", "provider_reference", "created_at"]
    readonly_fields = ["provider", "amount", "status", "provider_reference", "created_at"]
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Disable manual addition."""
        return False


@admin.register(Order)
class OrderAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for Order model.

    Features:
    - Complete order management
    - Status workflow with buttons
    - Payment tracking
    - Shipping management
    - Order search and filtering
    """

    list_display = [
        "order_number",
        "customer_info",
        "status_badge",
        "payment_badge",
        "total_display",
        "created_at",
    ]
    list_filter = [
        "status",
        "payment_status",
        "payment_method",
        "created_at",
        "is_deleted",
    ]
    search_fields = [
        "order_number",
        "customer_name",
        "customer_email",
        "customer_phone",
    ]
    readonly_fields = [
        "public_id",
        "order_number",
        "total_display",
        "confirmed_at",
        "shipped_at",
        "delivered_at",
        "cancelled_at",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        (
            "Order Information",
            {
                "fields": [
                    "public_id",
                    "order_number",
                    "user",
                    "status",
                    "payment_status",
                ]
            },
        ),
        (
            "Customer Details",
            {
                "fields": [
                    "customer_name",
                    "customer_email",
                    "customer_phone",
                ]
            },
        ),
        (
            "Shipping Address",
            {
                "fields": [
                    "shipping_zone",
                    "shipping_address_line1",
                    "shipping_address_line2",
                    "shipping_city",
                    "shipping_area",
                    "shipping_postal_code",
                ]
            },
        ),
        (
            "Pricing",
            {
                "fields": [
                    "subtotal",
                    "discount_amount",
                    "shipping_cost",
                    "tax_amount",
                    "total_display",
                ]
            },
        ),
        (
            "Payment",
            {
                "fields": [
                    "payment_method",
                    "payment_reference",
                ]
            },
        ),
        (
            "Coupon",
            {
                "fields": ["coupon", "coupon_code"],
                "classes": ["collapse"],
            },
        ),
        (
            "Shipping Details",
            {
                "fields": [
                    "tracking_number",
                    "courier_name",
                    "estimated_delivery",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Notes",
            {
                "fields": ["customer_notes", "admin_notes"],
                "classes": ["collapse"],
            },
        ),
        (
            "Timestamps",
            {
                "fields": [
                    "confirmed_at",
                    "shipped_at",
                    "delivered_at",
                    "cancelled_at",
                    "created_at",
                    "updated_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]
    inlines = [OrderItemInline, OrderStatusLogInline, PaymentTransactionInline]
    autocomplete_fields = ["user", "shipping_zone", "coupon"]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Include soft-deleted orders."""
        return Order.all_objects.all()

    @admin.display(description="Customer")
    def customer_info(self, obj: Order) -> str:
        """Display customer information."""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.customer_name,
            obj.customer_phone,
        )

    @admin.display(description="Status")
    def status_badge(self, obj: Order) -> str:
        """Display status badge."""
        colors = {
            "pending": "#ffc107",
            "confirmed": "#17a2b8",
            "processing": "#007bff",
            "shipped": "#6f42c1",
            "delivered": "#28a745",
            "cancelled": "#dc3545",
            "refunded": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Payment")
    def payment_badge(self, obj: Order) -> str:
        """Display payment status."""
        colors = {
            "pending": "#ffc107",
            "paid": "#28a745",
            "failed": "#dc3545",
            "refunded": "#6c757d",
        }
        color = colors.get(obj.payment_status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_payment_status_display(),
        )

    @admin.display(description="Total")
    def total_display(self, obj: Order) -> str:
        """Display order total."""
        return format_html(
            '<strong style="color: #28a745; font-size: 14px;">৳{:.2f}</strong>',
            obj.total,
        )

    @admin.action(description="Mark as Confirmed")
    def confirm_orders(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Confirm selected orders."""
        from apps.orders.services import OrderService

        count = 0
        for order in queryset.filter(status="pending"):
            OrderService.change_status(
                order, "confirmed", request.user, "Bulk confirmed by admin"
            )
            count += 1
        self.message_user(request, f"Confirmed {count} orders.")

    @admin.action(description="Mark as Shipped")
    def ship_orders(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Mark orders as shipped."""
        from apps.orders.services import OrderService

        count = 0
        for order in queryset.filter(status__in=["confirmed", "processing"]):
            OrderService.change_status(
                order, "shipped", request.user, "Bulk shipped by admin"
            )
            count += 1
        self.message_user(request, f"Shipped {count} orders.")

    actions = ["confirm_orders", "ship_orders"]


@admin.register(OrderItem)
class OrderItemAdmin(BaseModelAdmin):
    """Admin for individual order items."""

    list_display = [
        "order",
        "product_name",
        "variant_name",
        "sku",
        "unit_price",
        "quantity",
        "line_total",
    ]
    list_filter = ["order__status", "order__created_at"]
    search_fields = ["product_name", "sku", "order__order_number"]
    readonly_fields = [
        "order",
        "variant",
        "product_name",
        "variant_name",
        "sku",
        "unit_price",
        "quantity",
        "line_total",
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable manual addition."""
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Disable deletion."""
        return False


@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(BaseModelAdmin):
    """Admin for order status change logs."""

    list_display = [
        "order",
        "from_status",
        "to_status",
        "changed_by",
        "created_at",
    ]
    list_filter = ["from_status", "to_status", "created_at"]
    search_fields = ["order__order_number", "notes"]
    readonly_fields = [
        "order",
        "from_status",
        "to_status",
        "changed_by",
        "notes",
        "created_at",
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable manual addition."""
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Disable deletion."""
        return False


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(BaseModelAdmin):
    """Admin for payment transactions."""

    list_display = [
        "order",
        "provider",
        "amount_display",
        "status_badge",
        "provider_reference",
        "created_at",
    ]
    list_filter = ["provider", "status", "created_at"]
    search_fields = [
        "order__order_number",
        "provider_reference",
    ]
    readonly_fields = [
        "order",
        "provider",
        "amount",
        "status",
        "provider_reference",
        "raw_response",
        "created_at",
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable manual addition."""
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Disable deletion."""
        return False

    @admin.display(description="Amount")
    def amount_display(self, obj: PaymentTransaction) -> str:
        """Display transaction amount."""
        return format_html('<strong>৳{:.2f}</strong>', obj.amount)

    @admin.display(description="Status")
    def status_badge(self, obj: PaymentTransaction) -> str:
        """Display status badge."""
        colors = {
            "pending": "#ffc107",
            "completed": "#28a745",
            "failed": "#dc3545",
            "refunded": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )


@admin.register(ReturnRequest)
class ReturnRequestAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """Admin for return requests."""

    list_display = [
        "id",
        "order",
        "status_badge",
        "reason",
        "refund_amount_display",
        "created_at",
    ]
    list_filter = ["status", "reason", "created_at"]
    search_fields = ["order__order_number", "customer_notes"]
    readonly_fields = [
        "order",
        "user",
        "items_snapshot",
        "created_at",
        "updated_at",
        "processed_at",
    ]
    fieldsets = [
        (
            "Return Information",
            {
                "fields": [
                    "order",
                    "user",
                    "status",
                    "reason",
                ]
            },
        ),
        (
            "Details",
            {
                "fields": [
                    "customer_notes",
                    "admin_notes",
                    "items_snapshot",
                    "refund_amount",
                ]
            },
        ),
        (
            "Processing",
            {
                "fields": [
                    "processed_by",
                    "processed_at",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]
    autocomplete_fields = ["order", "user", "processed_by"]

    @admin.display(description="Status")
    def status_badge(self, obj: ReturnRequest) -> str:
        """Display status badge."""
        colors = {
            "requested": "#ffc107",
            "approved": "#28a745",
            "rejected": "#dc3545",
            "completed": "#007bff",
            "refunded": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Refund Amount")
    def refund_amount_display(self, obj: ReturnRequest) -> str:
        """Display refund amount."""
        if obj.refund_amount:
            return format_html(
                '<strong style="color: #28a745;">৳{:.2f}</strong>',
                obj.refund_amount,
            )
        return format_html('<span style="color: gray;">Not set</span>')

    @admin.action(description="Approve selected returns")
    def approve_returns(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Approve selected return requests."""
        from apps.orders.services import OrderService

        count = 0
        for return_req in queryset.filter(status="requested"):
            OrderService.process_return_request(
                return_req.id,
                approved=True,
                processed_by=request.user,
                admin_notes="Bulk approved by admin",
            )
            count += 1
        self.message_user(request, f"Approved {count} return requests.")

    @admin.action(description="Reject selected returns")
    def reject_returns(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Reject selected return requests."""
        from apps.orders.services import OrderService

        count = 0
        for return_req in queryset.filter(status="requested"):
            OrderService.process_return_request(
                return_req.id,
                approved=False,
                processed_by=request.user,
                admin_notes="Bulk rejected by admin",
            )
            count += 1
        self.message_user(request, f"Rejected {count} return requests.")

    actions = ["approve_returns", "reject_returns"]




