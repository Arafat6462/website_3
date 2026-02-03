"""
Orders Application Admin Configuration - Phase 7: Cart.
"""

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.core.admin import BaseModelAdmin, TimeStampedAdminMixin
from apps.orders.models import Cart, CartItem


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
