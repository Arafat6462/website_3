"""
Users Application Admin Configuration.

This module provides admin interface for:
- User management (staff and customers separately)
- Customer addresses
- Staff permission groups

Provides separate views for staff users vs customers for clarity.
"""

from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from apps.core.admin import BaseModelAdmin, TimeStampedAdminMixin
from apps.users.models import CustomerAddress, User


@admin.register(User)
class UserAdmin(TimeStampedAdminMixin, BaseUserAdmin, ModelAdmin):
    """
    Admin interface for User model.

    Provides separate list views for staff vs customers,
    with appropriate fields and actions for each.
    """

    # List display
    list_display = [
        "email",
        "full_name_display",
        "phone",
        "user_type_badge",
        "status_badge",
        "total_orders",
        "total_spent_display",
        "date_joined",
    ]

    list_filter = [
        "is_staff",
        "is_superuser",
        "is_active",
        "is_blocked",
        "email_verified",
        "date_joined",
    ]

    search_fields = ["email", "first_name", "last_name", "phone"]

    ordering = ["-date_joined"]

    # Fieldsets for add/edit forms
    fieldsets = (
        (
            "Account Information",
            {
                "fields": (
                    "public_id",
                    "email",
                    "username",
                    "password",
                )
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone",
                )
            },
        ),
        (
            "Permissions & Access",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Security",
            {
                "fields": (
                    "email_verified",
                    "is_blocked",
                    "block_reason",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": (
                    "total_orders",
                    "total_spent",
                )
            },
        ),
        (
            "Internal Notes",
            {
                "classes": ("collapse",),
                "fields": ("admin_notes",),
            },
        ),
        (
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": (
                    "date_joined",
                    "last_login",
                ),
            },
        ),
    )

    # Fieldsets for creating new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "phone",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    readonly_fields = [
        "public_id",
        "date_joined",
        "last_login",
        "total_orders",
        "total_spent",
    ]

    filter_horizontal = ["groups", "user_permissions"]

    # Custom methods for list display
    @admin.display(description="Full Name")
    def full_name_display(self, obj: User) -> str:
        """Display full name or email prefix."""
        return obj.get_full_name()

    @admin.display(description="Type")
    def user_type_badge(self, obj: User) -> str:
        """Display user type with color badge."""
        if obj.is_superuser:
            return format_html(
                '<span style="background: #e74c3c; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">SUPERUSER</span>'
            )
        elif obj.is_staff:
            return format_html(
                '<span style="background: #3498db; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">STAFF</span>'
            )
        else:
            return format_html(
                '<span style="background: #95a5a6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">CUSTOMER</span>'
            )

    @admin.display(description="Status")
    def status_badge(self, obj: User) -> str:
        """Display user status with color badge."""
        if obj.is_blocked:
            return format_html(
                '<span style="background: #e74c3c; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">BLOCKED</span>'
            )
        elif not obj.is_active:
            return format_html(
                '<span style="background: #95a5a6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">INACTIVE</span>'
            )
        else:
            return format_html(
                '<span style="background: #27ae60; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">ACTIVE</span>'
            )

    @admin.display(description="Total Spent")
    def total_spent_display(self, obj: User) -> str:
        """Display total spent with currency."""
        return f"৳{obj.total_spent:,.2f}"

    # Actions
    @admin.action(description="Block selected users")
    def block_users(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Block selected users from accessing the platform."""
        count = queryset.update(is_blocked=True)
        self.message_user(request, f"Successfully blocked {count} users.")

    @admin.action(description="Unblock selected users")
    def unblock_users(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Unblock selected users."""
        count = queryset.update(is_blocked=False, block_reason="")
        self.message_user(request, f"Successfully unblocked {count} users.")

    @admin.action(description="Mark email as verified")
    def verify_emails(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Mark selected users' emails as verified."""
        count = queryset.update(email_verified=True)
        self.message_user(request, f"Verified emails for {count} users.")

    actions = ["block_users", "unblock_users", "verify_emails"]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related()


@admin.register(CustomerAddress)
class CustomerAddressAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for CustomerAddress model.

    Provides address management with search and filtering.
    """

    list_display = [
        "user_email",
        "label",
        "recipient_name",
        "short_address_display",
        "phone",
        "is_default",
        "created_at",
    ]

    list_filter = [
        "is_default",
        "city",
        "created_at",
    ]

    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "recipient_name",
        "phone",
        "city",
        "area",
    ]

    ordering = ["-created_at"]

    fieldsets = (
        (
            "User",
            {
                "fields": ("user",)
            },
        ),
        (
            "Address Details",
            {
                "fields": (
                    "label",
                    "recipient_name",
                    "phone",
                    "address_line1",
                    "address_line2",
                    "city",
                    "area",
                    "postal_code",
                    "is_default",
                )
            },
        ),
    )

    autocomplete_fields = ["user"]

    # Custom methods for list display
    @admin.display(description="User")
    def user_email(self, obj: CustomerAddress) -> str:
        """Display user's email."""
        return obj.user.email

    @admin.display(description="Address")
    def short_address_display(self, obj: CustomerAddress) -> str:
        """Display short address."""
        return obj.short_address

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related("user")


# Customize Group admin (for permission groups)
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    """
    Customized admin for permission groups.

    Used for staff role management (order_managers, product_managers, etc.).
    """

    list_display = ["name", "user_count"]
    search_fields = ["name"]
    filter_horizontal = ["permissions"]

    @admin.display(description="Users")
    def user_count(self, obj: Group) -> int:
        """Display count of users in this group."""
        return obj.user_set.count()
