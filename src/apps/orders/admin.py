"""
Orders Application Admin Configuration - Phase 7: Cart, Phase 8: Coupons.
"""

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.core.admin import BaseModelAdmin, TimeStampedAdminMixin
from apps.orders.models import Cart, CartItem, Coupon, CouponUsage


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


