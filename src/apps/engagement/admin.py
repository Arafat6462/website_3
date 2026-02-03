"""
Engagement Application Admin - Phase 11: Review & Wishlist Management.

This module provides admin interfaces for:
- ProductReview: Approve/reject reviews, add admin replies
- Wishlist: View user wishlists (read-only)
- WishlistItem: View wishlist items (read-only)
"""

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from unfold.admin import ModelAdmin as BaseModelAdmin

from apps.core.admin import TimeStampedAdminMixin
from apps.engagement.models import ProductReview, Wishlist, WishlistItem


@admin.register(ProductReview)
class ProductReviewAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for ProductReview model.

    Features:
    - Approve/reject reviews
    - Add admin replies
    - Filter by approval status, rating
    - Search by user, product, comment
    """

    list_display = [
        "id",
        "user_email",
        "product_name",
        "rating_stars",
        "approval_badge",
        "has_reply_badge",
        "created_at",
    ]
    list_filter = ["is_approved", "rating", "created_at"]
    search_fields = [
        "user__email",
        "product__name",
        "comment",
    ]
    readonly_fields = [
        "user",
        "product",
        "rating",
        "comment",
        "images",
        "admin_replied_at",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        (
            "Review Information",
            {
                "fields": [
                    "user",
                    "product",
                    "rating",
                    "comment",
                    "images",
                ]
            },
        ),
        (
            "Approval",
            {
                "fields": ["is_approved"],
            },
        ),
        (
            "Admin Response",
            {
                "fields": [
                    "admin_reply",
                    "admin_replied_at",
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
    autocomplete_fields = ["user", "product"]

    @admin.display(description="User")
    def user_email(self, obj: ProductReview) -> str:
        """Display user email."""
        return obj.user.email

    @admin.display(description="Product")
    def product_name(self, obj: ProductReview) -> str:
        """Display product name."""
        return obj.product.name

    @admin.display(description="Rating")
    def rating_stars(self, obj: ProductReview) -> str:
        """Display rating as stars."""
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        return format_html(
            '<span style="color: #ffc107; font-size: 16px;">{}</span>', stars
        )

    @admin.display(description="Status")
    def approval_badge(self, obj: ProductReview) -> str:
        """Display approval status badge."""
        if obj.is_approved:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Approved</span>'
            )
        return format_html(
            '<span style="background-color: #ffc107; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Pending</span>'
        )

    @admin.display(description="Admin Reply", boolean=True)
    def has_reply_badge(self, obj: ProductReview) -> bool:
        """Show if admin has replied."""
        return obj.has_admin_reply

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Approve selected reviews."""
        count = queryset.filter(is_approved=False).update(is_approved=True)
        self.message_user(request, f"Approved {count} reviews.")

    @admin.action(description="Reject selected reviews")
    def reject_reviews(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Reject (unapprove) selected reviews."""
        count = queryset.filter(is_approved=True).update(is_approved=False)
        self.message_user(request, f"Rejected {count} reviews.")

    actions = ["approve_reviews", "reject_reviews"]


class WishlistItemInline(admin.TabularInline):
    """Inline admin for wishlist items."""

    model = WishlistItem
    extra = 0
    fields = ["variant", "created_at"]
    readonly_fields = ["variant", "created_at"]
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Disable manual addition."""
        return False


@admin.register(Wishlist)
class WishlistAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for Wishlist model.

    Read-only interface for viewing user wishlists.
    """

    list_display = [
        "id",
        "user_email",
        "item_count_display",
        "created_at",
    ]
    search_fields = ["user__email"]
    readonly_fields = [
        "public_id",
        "user",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        (
            "Wishlist Information",
            {
                "fields": [
                    "public_id",
                    "user",
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
    inlines = [WishlistItemInline]
    autocomplete_fields = ["user"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable manual creation (auto-created via service)."""
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Disable deletion."""
        return False

    @admin.display(description="User")
    def user_email(self, obj: Wishlist) -> str:
        """Display user email."""
        return obj.user.email

    @admin.display(description="Items")
    def item_count_display(self, obj: Wishlist) -> str:
        """Display item count."""
        count = obj.item_count
        return format_html(
            '<strong style="color: #007bff;">{}</strong>', count
        )


@admin.register(WishlistItem)
class WishlistItemAdmin(BaseModelAdmin):
    """Admin for individual wishlist items."""

    list_display = [
        "id",
        "user_email",
        "variant_name",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = [
        "wishlist__user__email",
        "variant__name",
        "variant__sku",
    ]
    readonly_fields = [
        "wishlist",
        "variant",
        "created_at",
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable manual addition."""
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Disable editing."""
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Disable deletion via admin."""
        return False

    @admin.display(description="User")
    def user_email(self, obj: WishlistItem) -> str:
        """Display user email."""
        return obj.wishlist.user.email

    @admin.display(description="Variant")
    def variant_name(self, obj: WishlistItem) -> str:
        """Display variant name."""
        return obj.variant.name
