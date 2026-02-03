"""
Products Application Admin Configuration.

This module provides admin interfaces for:
- Product types with inline attribute assignment
- Attributes with field type configuration
- Categories with hierarchical tree view
"""

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.core.admin import (
    BaseModelAdmin,
    SEOAdminMixin,
    SoftDeleteAdminMixin,
    TimeStampedAdminMixin,
)
from apps.products.models import Attribute, Category, ProductType, ProductTypeAttribute


class ProductTypeAttributeInline(admin.TabularInline):
    """
    Inline admin for assigning attributes to product types.

    Allows editing attribute assignments directly in the ProductType admin.
    """

    model = ProductTypeAttribute
    extra = 1
    fields = ["attribute", "sort_order"]
    autocomplete_fields = ["attribute"]


@admin.register(ProductType)
class ProductTypeAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for ProductType model.

    Shows product types with inline attribute assignment.
    """

    list_display = [
        "name",
        "slug",
        "is_active",
        "attribute_count_display",
        "product_count_display",
        "created_at",
    ]

    list_filter = ["is_active", "created_at"]

    search_fields = ["name", "slug", "description"]

    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "is_active",
                )
            },
        ),
    )

    inlines = [ProductTypeAttributeInline]

    @admin.display(description="Attributes")
    def attribute_count_display(self, obj: ProductType) -> str:
        """Display attribute count."""
        count = obj.attribute_count
        return format_html(
            '<span style="background: #3498db; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{} attributes</span>',
            count
        )

    @admin.display(description="Products")
    def product_count_display(self, obj: ProductType) -> str:
        """Display product count."""
        count = obj.product_count
        color = "#27ae60" if count > 0 else "#95a5a6"
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{} products</span>',
            color, count
        )


@admin.register(Attribute)
class AttributeAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for Attribute model.

    Manages product attributes with field type configuration.
    """

    list_display = [
        "name",
        "code",
        "field_type",
        "is_variant_badge",
        "is_required",
        "is_filterable",
        "is_visible",
        "sort_order",
    ]

    list_filter = [
        "field_type",
        "is_variant",
        "is_required",
        "is_filterable",
        "is_visible",
    ]

    search_fields = ["name", "code"]

    prepopulated_fields = {"code": ("name",)}

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "code",
                    "field_type",
                    "options",
                )
            },
        ),
        (
            "Configuration",
            {
                "fields": (
                    "is_variant",
                    "is_required",
                    "is_filterable",
                    "is_visible",
                    "sort_order",
                )
            },
        ),
    )

    @admin.display(description="Variant", boolean=True)
    def is_variant_badge(self, obj: Attribute) -> bool:
        """Display variant indicator."""
        return obj.is_variant


@admin.register(Category)
class CategoryAdmin(SoftDeleteAdminMixin, SEOAdminMixin, TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for Category model.

    Provides hierarchical category management with tree view.
    """

    list_display = [
        "name_with_level",
        "status_badge",
        "product_count_display",
        "sort_order",
        "created_at",
    ]

    list_filter = ["status", "parent", "created_at"]

    search_fields = ["name", "slug", "description"]

    autocomplete_fields = ["parent"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "parent",
                    "description",
                    "image",
                    "status",
                    "sort_order",
                )
            },
        ),
        SEOAdminMixin.seo_fieldset,
    )

    @admin.display(description="Category")
    def name_with_level(self, obj: Category) -> str:
        """Display category name with indentation for hierarchy."""
        indent = "—" * obj.level
        prefix = f"{indent} " if indent else ""
        return f"{prefix}{obj.name}"

    @admin.display(description="Status")
    def status_badge(self, obj: Category) -> str:
        """Display status with color badge."""
        if obj.status == Category.Status.ACTIVE:
            return format_html(
                '<span style="background: #27ae60; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">ACTIVE</span>'
            )
        else:
            return format_html(
                '<span style="background: #95a5a6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">HIDDEN</span>'
            )

    @admin.display(description="Products")
    def product_count_display(self, obj: Category) -> str:
        """Display product count."""
        count = obj.product_count
        color = "#3498db" if count > 0 else "#95a5a6"
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, count
        )

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related("parent")

    @admin.action(description="Activate selected categories")
    def activate_categories(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Set selected categories to active status."""
        count = queryset.update(status=Category.Status.ACTIVE)
        self.message_user(request, f"Activated {count} categories.")

    @admin.action(description="Hide selected categories")
    def hide_categories(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Set selected categories to hidden status."""
        count = queryset.update(status=Category.Status.HIDDEN)
        self.message_user(request, f"Hidden {count} categories.")

    actions = ["activate_categories", "hide_categories"] + SoftDeleteAdminMixin.actions
