"""
Core Application Admin Configuration.

This module provides base admin classes and mixins that can be used
by other apps to reduce boilerplate and maintain consistency.

Available Mixins:
    - TimeStampedAdminMixin: Display created_at/updated_at in admin
    - SoftDeleteAdminMixin: Handle soft-deleted records
    - SEOAdminMixin: Group SEO fields in admin
    - SortableAdminMixin: Enable drag-drop reordering

Usage:
    from apps.core.admin import BaseModelAdmin, SoftDeleteAdminMixin

    @admin.register(Product)
    class ProductAdmin(SoftDeleteAdminMixin, BaseModelAdmin):
        list_display = ['name', 'price', 'created_at']
"""

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from unfold.admin import ModelAdmin


class BaseModelAdmin(ModelAdmin):
    """
    Base admin class with common configurations.

    Provides sensible defaults for all model admins including:
    - Read-only timestamp fields
    - Optimized list display
    - Search and filter defaults

    Inherit from this class for all model admins.

    Example:
        @admin.register(Product)
        class ProductAdmin(BaseModelAdmin):
            list_display = ['name', 'price']
    """

    # Fields that should always be read-only
    readonly_fields_base = ("created_at", "updated_at")

    # Pagination for large datasets
    list_per_page = 25
    list_max_show_all = 100

    # Show "Save and continue" by default
    save_on_top = True

    def get_readonly_fields(
        self, request: HttpRequest, obj: Any | None = None
    ) -> tuple[str, ...]:
        """
        Combine base readonly fields with class-specific ones.

        Args:
            request: The current request.
            obj: The object being edited, or None for add.

        Returns:
            Tuple of readonly field names.
        """
        readonly = list(super().get_readonly_fields(request, obj))
        readonly.extend(self.readonly_fields_base)
        return tuple(set(readonly))  # Remove duplicates


class TimeStampedAdminMixin:
    """
    Admin mixin for models with created_at/updated_at fields.

    Adds timestamp fields to list display and makes them read-only.

    Usage:
        class ProductAdmin(TimeStampedAdminMixin, BaseModelAdmin):
            list_display = ['name', 'created_at', 'updated_at']
    """

    readonly_fields_timestamps = ("created_at", "updated_at")

    def get_readonly_fields(
        self, request: HttpRequest, obj: Any | None = None
    ) -> tuple[str, ...]:
        """Add timestamp fields to readonly list."""
        readonly = list(super().get_readonly_fields(request, obj))
        readonly.extend(self.readonly_fields_timestamps)
        return tuple(set(readonly))


class SoftDeleteAdminMixin:
    """
    Admin mixin for models with soft-delete functionality.

    Provides:
    - Filter to show/hide deleted records
    - Actions to delete and restore
    - Visual indication of deleted items

    Usage:
        class ProductAdmin(SoftDeleteAdminMixin, BaseModelAdmin):
            list_display = ['name', 'is_deleted']
    """

    # Add delete filter by default
    list_filter_soft_delete = ("is_deleted",)

    def get_list_filter(self, request: HttpRequest) -> tuple[str, ...]:
        """Add is_deleted to list filters."""
        filters = list(super().get_list_filter(request))
        filters.extend(self.list_filter_soft_delete)
        return tuple(set(filters))

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """
        Include deleted records in admin by default.

        Uses all_objects manager if available to show deleted items.

        Args:
            request: The current request.

        Returns:
            QuerySet including soft-deleted records.
        """
        qs = super().get_queryset(request)

        # If model has all_objects manager, use it
        if hasattr(self.model, "all_objects"):
            qs = self.model.all_objects.all()

        return qs

    @admin.action(description="Soft delete selected items")
    def soft_delete_selected(self, request: HttpRequest, queryset: QuerySet) -> None:
        """
        Soft-delete selected records.

        Args:
            request: The current request.
            queryset: QuerySet of selected records.
        """
        count = 0
        for obj in queryset:
            obj.delete()
            count += 1

        self.message_user(request, f"Successfully soft-deleted {count} items.")

    @admin.action(description="Restore selected items")
    def restore_selected(self, request: HttpRequest, queryset: QuerySet) -> None:
        """
        Restore soft-deleted records.

        Args:
            request: The current request.
            queryset: QuerySet of selected records.
        """
        count = queryset.filter(is_deleted=True).count()
        queryset.update(is_deleted=False, deleted_at=None)

        self.message_user(request, f"Successfully restored {count} items.")

    @admin.action(description="Permanently delete selected items")
    def hard_delete_selected(self, request: HttpRequest, queryset: QuerySet) -> None:
        """
        Permanently delete selected records.

        WARNING: This cannot be undone.

        Args:
            request: The current request.
            queryset: QuerySet of selected records.
        """
        count, _ = queryset.delete()
        self.message_user(request, f"Permanently deleted {count} items.")

    actions = ["soft_delete_selected", "restore_selected", "hard_delete_selected"]


class SEOAdminMixin:
    """
    Admin mixin for models with SEO fields.

    Groups SEO fields (slug, meta_title, meta_description) in a
    collapsible fieldset for cleaner admin interface.

    Usage:
        class ProductAdmin(SEOAdminMixin, BaseModelAdmin):
            fieldsets = [
                (None, {'fields': ['name', 'description']}),
                SEOAdminMixin.seo_fieldset,
            ]
    """

    seo_fieldset = (
        "SEO Settings",
        {
            "classes": ("collapse",),
            "fields": ("slug", "meta_title", "meta_description"),
            "description": "Search engine optimization settings",
        },
    )

    prepopulated_fields_seo = {"slug": ("name",)}

    def get_prepopulated_fields(
        self, request: HttpRequest, obj: Any | None = None
    ) -> dict[str, tuple[str, ...]]:
        """
        Auto-populate slug from name field.

        Only applies when creating new objects (not editing).

        Args:
            request: The current request.
            obj: The object being edited, or None for add.

        Returns:
            Dictionary of prepopulated field mappings.
        """
        prepopulated = dict(super().get_prepopulated_fields(request, obj))

        # Only prepopulate for new objects
        if obj is None:
            prepopulated.update(self.prepopulated_fields_seo)

        return prepopulated


class SortableAdminMixin:
    """
    Admin mixin for models with sort_order field.

    Adds sort_order to list display and enables ordering.

    For drag-drop reordering, consider using django-admin-sortable2
    or similar packages.

    Usage:
        class CategoryAdmin(SortableAdminMixin, BaseModelAdmin):
            list_display = ['name', 'sort_order']
    """

    ordering = ("sort_order",)

    sortable_field = "sort_order"

    def get_list_editable(self, request: HttpRequest) -> tuple[str, ...]:
        """Make sort_order editable in list view."""
        editable = list(super().get_list_editable(request) if hasattr(super(), 'get_list_editable') else [])
        if self.sortable_field not in editable:
            editable.append(self.sortable_field)
        return tuple(editable)
