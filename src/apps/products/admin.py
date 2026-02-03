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


# ============================================================================
# PHASE 5: PRODUCTS & VARIANTS ADMIN
# ============================================================================

from apps.products.models import (
    Product,
    ProductAttributeValue,
    ProductImage,
    ProductVariant,
    VariantAttributeValue,
    VariantPriceHistory,
)


class ProductVariantInline(admin.TabularInline):
    """
    Inline admin for product variants.

    Shows variants directly in product admin for quick editing.
    """

    model = ProductVariant
    extra = 0
    fields = [
        "sku",
        "name",
        "price",
        "stock_quantity",
        "is_active",
        "is_default",
        "sort_order",
    ]
    readonly_fields = ["sku"]


class ProductImageInline(admin.TabularInline):
    """
    Inline admin for product images.

    Allows uploading/ordering images directly in product admin.
    """

    model = ProductImage
    extra = 1
    fields = ["image", "alt_text", "variant", "is_primary", "sort_order"]
    autocomplete_fields = ["variant"]


class ProductAttributeValueInline(admin.TabularInline):
    """
    Inline admin for product attribute values.

    Shows non-variant attributes (Material, Brand, etc.).
    """

    model = ProductAttributeValue
    extra = 0
    fields = ["attribute", "value"]
    autocomplete_fields = ["attribute"]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Only show non-variant attributes."""
        qs = super().get_queryset(request)
        return qs.filter(attribute__is_variant=False)


@admin.register(Product)
class ProductAdmin(SEOAdminMixin, SoftDeleteAdminMixin, TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for Product model.

    Features:
    - Inline variant editing
    - Inline image management
    - Attribute value editing
    - Status workflow actions
    - Search and filters
    """

    list_display = [
        "name",
        "product_type",
        "category",
        "status_badge",
        "base_price",
        "variant_count",
        "stock_status",
        "is_featured",
        "is_new",
        "created_at",
    ]
    list_filter = [
        "status",
        "is_featured",
        "is_new",
        "product_type",
        "category",
        "track_inventory",
        "created_at",
    ]
    search_fields = ["name", "slug", "description", "public_id"]
    prepopulated_fields = {"slug": ["name"]}
    readonly_fields = [
        "public_id",
        "view_count",
        "sold_count",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        (
            "Basic Information",
            {
                "fields": [
                    "public_id",
                    "product_type",
                    "category",
                    "name",
                    "slug",
                    "short_description",
                    "description",
                ]
            },
        ),
        (
            "Pricing",
            {
                "fields": [
                    "base_price",
                    "compare_price",
                    "cost_price",
                ]
            },
        ),
        (
            "Status & Visibility",
            {
                "fields": [
                    "status",
                    "is_featured",
                    "is_new",
                ]
            },
        ),
        (
            "Inventory",
            {
                "fields": [
                    "track_inventory",
                    "allow_backorder",
                ]
            },
        ),
        (
            "SEO",
            {
                "fields": ["meta_title", "meta_description"],
                "classes": ["collapse"],
            },
        ),
        (
            "Statistics",
            {
                "fields": ["view_count", "sold_count"],
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
    inlines = [ProductImageInline, ProductVariantInline, ProductAttributeValueInline]
    autocomplete_fields = ["product_type", "category"]

    @admin.display(description="Status")
    def status_badge(self, obj: Product) -> str:
        """Display status with colored badge."""
        colors = {
            "draft": "gray",
            "published": "green",
            "hidden": "orange",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Variants")
    def variant_count(self, obj: Product) -> int:
        """Display number of variants."""
        return obj.variants.filter(is_deleted=False).count()

    @admin.display(description="Stock")
    def stock_status(self, obj: Product) -> str:
        """Display stock status."""
        if not obj.track_inventory:
            return format_html('<span style="color: gray;">Not tracked</span>')

        total_stock = sum(
            v.stock_quantity for v in obj.variants.filter(is_deleted=False, is_active=True)
        )

        if total_stock == 0:
            return format_html('<span style="color: red;">Out of stock</span>')
        elif total_stock < 50:
            return format_html(
                '<span style="color: orange;">Low ({} units)</span>', total_stock
            )
        else:
            return format_html('<span style="color: green;">{} units</span>', total_stock)

    @admin.action(description="Publish selected products")
    def publish_products(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Publish selected products."""
        count = queryset.update(status=Product.Status.PUBLISHED)
        self.message_user(request, f"Published {count} products.")

    @admin.action(description="Unpublish selected products")
    def unpublish_products(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Unpublish selected products."""
        count = queryset.update(status=Product.Status.DRAFT)
        self.message_user(request, f"Unpublished {count} products.")

    @admin.action(description="Mark as featured")
    def mark_featured(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Mark products as featured."""
        count = queryset.update(is_featured=True)
        self.message_user(request, f"Marked {count} products as featured.")

    @admin.action(description="Mark as new arrival")
    def mark_new(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Mark products as new arrival."""
        count = queryset.update(is_new=True)
        self.message_user(request, f"Marked {count} products as new.")

    actions = [
        "publish_products",
        "unpublish_products",
        "mark_featured",
        "mark_new",
    ] + SoftDeleteAdminMixin.actions


class VariantAttributeValueInline(admin.TabularInline):
    """
    Inline admin for variant attribute values.

    Shows variant-defining attributes (Size, Color, etc.).
    """

    model = VariantAttributeValue
    extra = 0
    fields = ["attribute", "value"]
    autocomplete_fields = ["attribute"]


class VariantPriceHistoryInline(admin.TabularInline):
    """
    Inline admin for variant price history.

    Shows price change log for auditing.
    """

    model = VariantPriceHistory
    extra = 0
    fields = ["old_price", "new_price", "changed_by", "created_at"]
    readonly_fields = ["old_price", "new_price", "changed_by", "created_at"]
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Disable manual creation (auto-created via signals)."""
        return False


@admin.register(ProductVariant)
class ProductVariantAdmin(SoftDeleteAdminMixin, TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for ProductVariant model.

    Features:
    - View all variants across products
    - Bulk stock/price updates
    - Attribute value editing
    - Price history tracking
    """

    list_display = [
        "sku",
        "product",
        "name",
        "effective_price_display",
        "stock_display",
        "is_active",
        "is_default",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "is_default",
        "product__product_type",
        "product__category",
        "created_at",
    ]
    search_fields = ["sku", "name", "barcode", "product__name"]
    readonly_fields = [
        "public_id",
        "effective_price_display",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        (
            "Basic Information",
            {
                "fields": [
                    "public_id",
                    "product",
                    "sku",
                    "name",
                ]
            },
        ),
        (
            "Pricing",
            {
                "fields": [
                    "price",
                    "compare_price",
                    "cost_price",
                    "effective_price_display",
                ]
            },
        ),
        (
            "Inventory",
            {
                "fields": [
                    "stock_quantity",
                    "low_stock_threshold",
                ]
            },
        ),
        (
            "Shipping",
            {
                "fields": ["weight", "barcode"],
                "classes": ["collapse"],
            },
        ),
        (
            "Display",
            {
                "fields": [
                    "is_active",
                    "is_default",
                    "sort_order",
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
    inlines = [VariantAttributeValueInline, VariantPriceHistoryInline]
    autocomplete_fields = ["product"]

    @admin.display(description="Effective Price")
    def effective_price_display(self, obj: ProductVariant) -> str:
        """Display effective price with source."""
        if obj.price is not None:
            return format_html('<strong>৳{}</strong> (variant)', obj.price)
        return format_html('৳{} (from product)', obj.product.base_price)

    @admin.display(description="Stock")
    def stock_display(self, obj: ProductVariant) -> str:
        """Display stock with color coding."""
        if obj.stock_quantity == 0:
            return format_html('<span style="color: red;">Out of stock</span>')
        elif obj.is_low_stock:
            return format_html(
                '<span style="color: orange;">{} (Low)</span>', obj.stock_quantity
            )
        else:
            return format_html(
                '<span style="color: green;">{}</span>', obj.stock_quantity
            )

    @admin.action(description="Activate selected variants")
    def activate_variants(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Activate selected variants."""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} variants.")

    @admin.action(description="Deactivate selected variants")
    def deactivate_variants(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Deactivate selected variants."""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} variants.")

    actions = [
        "activate_variants",
        "deactivate_variants",
    ] + SoftDeleteAdminMixin.actions


@admin.register(ProductImage)
class ProductImageAdmin(TimeStampedAdminMixin, BaseModelAdmin):
    """
    Admin interface for ProductImage model.

    Manage product and variant images.
    """

    list_display = [
        "image_preview",
        "product",
        "variant",
        "alt_text",
        "is_primary",
        "sort_order",
        "created_at",
    ]
    list_filter = ["is_primary", "created_at"]
    search_fields = ["product__name", "variant__name", "alt_text"]
    readonly_fields = ["image_preview", "created_at", "updated_at"]
    autocomplete_fields = ["product", "variant"]

    @admin.display(description="Preview")
    def image_preview(self, obj: ProductImage) -> str:
        """Display image thumbnail."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image.url,
            )
        return "-"
