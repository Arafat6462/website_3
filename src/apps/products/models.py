"""
Products Application Models - Part 1: Foundation.

This module contains the foundation models for the EAV product system:
- ProductType: Templates for product categories
- Attribute: Reusable product attributes (Size, Color, RAM, etc.)
- ProductTypeAttribute: Links attributes to product types
- Category: Hierarchical category structure

These models form the foundation of the flexible product catalog.
Product, ProductVariant, and related models will be in separate files.
"""

from typing import Any

from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import SEOModel, SoftDeleteModel, SortableModel, TimeStampedModel
from apps.products.managers import CategoryManager


class ProductType(TimeStampedModel):
    """
    Product type model - templates for different product categories.

    Product types define what attributes a category of products should have.
    For example:
    - "Clothing" type might have: Size, Color, Material attributes
    - "Electronics" type might have: RAM, Storage, Screen Size attributes

    This allows creating any product type without changing code.

    Attributes:
        name: Unique name of the product type (e.g., "Clothing", "Electronics").
        slug: URL-friendly version of the name.
        description: Description of what this type is for.
        is_active: Whether this type can be used for new products.

    Example:
        clothing_type = ProductType.objects.create(
            name="Clothing",
            slug="clothing",
            description="Apparel and fashion items"
        )
        
        # Add attributes in ProductTypeAttribute model
    """

    name = models.CharField(
        verbose_name="Name",
        max_length=100,
        unique=True,
        help_text="Unique name for this product type (e.g., 'Clothing', 'Electronics').",
    )

    slug = models.SlugField(
        verbose_name="Slug",
        max_length=100,
        unique=True,
        help_text="URL-friendly version of the name.",
    )

    description = models.TextField(
        verbose_name="Description",
        blank=True,
        help_text="Description of this product type and what it's used for.",
    )

    is_active = models.BooleanField(
        verbose_name="Is Active",
        default=True,
        db_index=True,
        help_text="Whether this product type is active and can be used.",
    )

    class Meta:
        verbose_name = "Product Type"
        verbose_name_plural = "Product Types"
        ordering = ["name"]

    def __str__(self) -> str:
        """String representation of the product type."""
        return self.name

    @property
    def product_count(self) -> int:
        """
        Get count of products using this type.

        Returns:
            Number of products with this product type.
        """
        return self.products.count()

    @property
    def attribute_count(self) -> int:
        """
        Get count of attributes assigned to this type.

        Returns:
            Number of attributes linked via ProductTypeAttribute.
        """
        return self.product_type_attributes.count()


class Attribute(TimeStampedModel):
    """
    Product attribute model - reusable attributes for products.

    Attributes define what information can be captured about products.
    They are reusable across multiple product types.

    Attributes:
        name: Display name (e.g., "Size", "Color", "RAM").
        code: Unique machine-readable code (e.g., "size", "color", "ram").
        field_type: Data type (text, select, number, etc.).
        options: JSON field for dropdown/multiselect choices.
        is_required: Whether this attribute must have a value.
        is_filterable: Whether customers can filter by this attribute.
        is_variant: Whether this creates product variants (SKUs).
        is_visible: Whether to show in product details.
        sort_order: Display order in forms/lists.

    Field Types:
        - TEXT: Short text input (brand, material)
        - TEXTAREA: Long text input (care instructions)
        - NUMBER: Numeric value (weight, dimensions)
        - SELECT: Single choice from options (size: S/M/L)
        - MULTISELECT: Multiple choices (features)
        - BOOLEAN: Yes/No (is organic, is vegan)
        - DATE: Date value (expiry date)
        - COLOR: Color picker (product color)

    Variant vs Non-Variant:
        - is_variant=True: Creates separate SKUs (Size, Color)
        - is_variant=False: Just product info (Material, Brand)

    Example:
        size_attr = Attribute.objects.create(
            name="Size",
            code="size",
            field_type="select",
            options={"choices": ["S", "M", "L", "XL"]},
            is_variant=True,  # Creates SKUs
            is_filterable=True
        )
    """

    class FieldType(models.TextChoices):
        """Available field types for attributes."""
        TEXT = "text", "Text"
        TEXTAREA = "textarea", "Textarea"
        NUMBER = "number", "Number"
        SELECT = "select", "Select (Single Choice)"
        MULTISELECT = "multiselect", "Multi-Select"
        BOOLEAN = "boolean", "Boolean (Yes/No)"
        DATE = "date", "Date"
        COLOR = "color", "Color"

    name = models.CharField(
        verbose_name="Name",
        max_length=100,
        help_text="Display name of the attribute (e.g., 'Size', 'Color').",
    )

    code = models.SlugField(
        verbose_name="Code",
        max_length=100,
        unique=True,
        help_text="Unique machine-readable code (e.g., 'size', 'color', 'ram').",
    )

    field_type = models.CharField(
        verbose_name="Field Type",
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.TEXT,
        help_text="Type of input field for this attribute.",
    )

    options = models.JSONField(
        verbose_name="Options",
        default=dict,
        blank=True,
        help_text="JSON configuration for select/multiselect choices and validation rules.",
    )

    is_required = models.BooleanField(
        verbose_name="Is Required",
        default=False,
        help_text="Whether this attribute must have a value.",
    )

    is_filterable = models.BooleanField(
        verbose_name="Is Filterable",
        default=True,
        help_text="Whether customers can filter products by this attribute.",
    )

    is_variant = models.BooleanField(
        verbose_name="Is Variant Attribute",
        default=False,
        db_index=True,
        help_text="If True, this attribute creates product variants (separate SKUs).",
    )

    is_visible = models.BooleanField(
        verbose_name="Is Visible",
        default=True,
        help_text="Whether to display this attribute on product pages.",
    )

    sort_order = models.PositiveIntegerField(
        verbose_name="Sort Order",
        default=0,
        help_text="Display order in forms and lists.",
    )

    class Meta:
        verbose_name = "Attribute"
        verbose_name_plural = "Attributes"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        """String representation of the attribute."""
        variant_indicator = " [Variant]" if self.is_variant else ""
        return f"{self.name}{variant_indicator}"

    @property
    def has_choices(self) -> bool:
        """
        Check if this attribute has predefined choices.

        Returns:
            True if field_type is select/multiselect with choices defined.
        """
        if self.field_type in [self.FieldType.SELECT, self.FieldType.MULTISELECT]:
            return bool(self.options.get("choices"))
        return False

    @property
    def choices_list(self) -> list[str]:
        """
        Get list of available choices.

        Returns:
            List of choice values for select/multiselect fields.
        """
        if self.has_choices:
            return self.options.get("choices", [])
        return []


class ProductTypeAttribute(TimeStampedModel):
    """
    Links attributes to product types with ordering.

    This is the many-to-many relationship table between ProductType
    and Attribute, with an additional sort_order field.

    When you assign attributes to a product type, this model stores
    which attributes belong to that type and in what order they
    should appear.

    Attributes:
        product_type: The product type these attributes belong to.
        attribute: The attribute to include.
        sort_order: Display order for this attribute within the type.

    Example:
        # Assign Size and Color to Clothing type
        ProductTypeAttribute.objects.create(
            product_type=clothing_type,
            attribute=size_attr,
            sort_order=1
        )
        ProductTypeAttribute.objects.create(
            product_type=clothing_type,
            attribute=color_attr,
            sort_order=2
        )
    """

    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.CASCADE,
        related_name="product_type_attributes",
        verbose_name="Product Type",
    )

    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name="product_type_attributes",
        verbose_name="Attribute",
    )

    sort_order = models.PositiveIntegerField(
        verbose_name="Sort Order",
        default=0,
        help_text="Display order for this attribute.",
    )

    class Meta:
        verbose_name = "Product Type Attribute"
        verbose_name_plural = "Product Type Attributes"
        ordering = ["product_type", "sort_order"]
        unique_together = [["product_type", "attribute"]]

    def __str__(self) -> str:
        """String representation."""
        return f"{self.product_type.name} - {self.attribute.name}"


class Category(SEOModel, SortableModel, SoftDeleteModel):
    """
    Hierarchical product category model.

    Categories can be nested to create a tree structure:
    Electronics
    ├── Phones
    │   ├── Android
    │   └── iPhone
    └── Laptops

    Inherits from:
        - SEOModel: slug, meta_title, meta_description
        - SortableModel: sort_order for manual ordering
        - SoftDeleteModel: is_deleted, deleted_at

    Attributes:
        name: Category name.
        parent: Parent category (None for root categories).
        description: Category description.
        image: Category image/icon.
        status: active or hidden.
        product_count: Cached count of products (updated on save).
        
    Status Choices:
        - active: Visible to customers
        - hidden: Not visible (seasonal, etc.)

    Example:
        electronics = Category.objects.create(
            name="Electronics",
            slug="electronics",
            status="active"
        )
        
        phones = Category.objects.create(
            name="Phones",
            parent=electronics,
            slug="phones"
        )
    """

    class Status(models.TextChoices):
        """Category visibility status."""
        ACTIVE = "active", "Active"
        HIDDEN = "hidden", "Hidden"

    name = models.CharField(
        verbose_name="Name",
        max_length=255,
        help_text="Category name.",
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
        verbose_name="Parent Category",
        help_text="Parent category (leave blank for root categories).",
    )

    description = models.TextField(
        verbose_name="Description",
        blank=True,
        help_text="Category description for SEO and display.",
    )

    image = models.ImageField(
        verbose_name="Image",
        upload_to="categories/",
        blank=True,
        null=True,
        help_text="Category image or icon.",
    )

    status = models.CharField(
        verbose_name="Status",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        help_text="Category visibility status.",
    )

    product_count = models.PositiveIntegerField(
        verbose_name="Product Count",
        default=0,
        editable=False,
        help_text="Number of products in this category (cached).",
    )

    # Custom manager
    objects = CategoryManager()

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["parent", "status"]),
            models.Index(fields=["status", "sort_order"]),
        ]

    def __str__(self) -> str:
        """String representation with parent hierarchy."""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_slug_source(self) -> str:
        """Return the name field for slug generation."""
        return self.name

    @property
    def is_root(self) -> bool:
        """Check if this is a root category."""
        return self.parent is None

    @property
    def level(self) -> int:
        """
        Get nesting level (0 for root, 1 for direct children, etc.).

        Returns:
            Integer representing depth in category tree.
        """
        level = 0
        current = self.parent
        while current is not None:
            level += 1
            current = current.parent
        return level

    @property
    def has_children(self) -> bool:
        """Check if category has child categories."""
        return self.children.exists()

    def get_children(self) -> models.QuerySet:
        """Get immediate child categories."""
        return self.children.filter(status=self.Status.ACTIVE, is_deleted=False)

    def get_all_products(self) -> models.QuerySet:
        """
        Get all products in this category and descendants.

        Returns:
            QuerySet of products in this category tree.
        """
        # This will be implemented after Product model is created
        from apps.products.models import Product
        
        # Get this category and all descendants
        category_ids = [self.pk]
        descendants = Category.objects.get_descendants(self)
        category_ids.extend([d.pk for d in descendants])
        
        return Product.objects.filter(category_id__in=category_ids)

    def update_product_count(self) -> None:
        """
        Update cached product count.

        Should be called when products are added/removed.
        """
        self.product_count = self.products.filter(is_deleted=False).count()
        self.save(update_fields=["product_count"])
