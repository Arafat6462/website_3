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


# ============================================================================
# PHASE 5: PRODUCTS & VARIANTS
# ============================================================================


class Product(SEOModel, SoftDeleteModel, TimeStampedModel):
    """
    Product model - represents a product in the catalog.

    A product can have multiple variants (SKUs) based on variant attributes.
    For example, a T-Shirt product might have variants for each Size+Color combination.

    Attributes:
        public_id: UUID for public API access (hides sequential IDs).
        product_type: Template defining what attributes this product has.
        category: The category this product belongs to.
        name: Product name.
        slug: Auto-generated from name, unique URL identifier.
        short_description: Brief product description (for listings).
        description: Full product description (for detail page).
        base_price: Default price (variants can override).
        compare_price: Original price for showing discounts.
        cost_price: Internal cost (for profit calculation).
        status: Draft, Published, or Hidden.
        is_featured: Show on homepage/featured sections.
        is_new: Mark as "New Arrival".
        track_inventory: Whether to track stock levels.
        allow_backorder: Allow ordering when out of stock.
        view_count: Number of times viewed (cached).
        sold_count: Number of units sold (cached).
        meta_title: SEO title (from SEOModel).
        meta_description: SEO description (from SEOModel).

    Example:
        tshirt = Product.objects.create(
            product_type=clothing_type,
            category=tshirts_category,
            name="Cotton T-Shirt",
            base_price=25.00,
            status="published"
        )
    """

    class Status(models.TextChoices):
        """Product status choices."""

        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        HIDDEN = "hidden", "Hidden"

    public_id = models.UUIDField(unique=True, editable=False)
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        related_name="products",
        help_text="Product type determines available attributes",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        help_text="Category for organization and filtering",
    )
    name = models.CharField(max_length=255, db_index=True, help_text="Product name")
    short_description = models.TextField(
        blank=True, help_text="Brief description for listings"
    )
    description = models.TextField(blank=True, help_text="Full product description")
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Base price (variants can override)",
    )
    compare_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Original price for showing discounts",
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Cost to acquire/produce",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Product visibility status",
    )
    is_featured = models.BooleanField(
        default=False, db_index=True, help_text="Show in featured sections"
    )
    is_new = models.BooleanField(
        default=False, db_index=True, help_text="Mark as new arrival"
    )
    track_inventory = models.BooleanField(
        default=True, help_text="Track stock levels for this product"
    )
    allow_backorder = models.BooleanField(
        default=False, help_text="Allow orders when out of stock"
    )
    view_count = models.PositiveIntegerField(
        default=0, help_text="Number of times viewed"
    )
    sold_count = models.PositiveIntegerField(
        default=0, help_text="Number of units sold"
    )

    class Meta:
        db_table = "products_product"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "status"]),
            models.Index(fields=["is_featured", "status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Generate public_id and slug on first save."""
        import uuid

        if not self.public_id:
            self.public_id = uuid.uuid4()

        # slug auto-generated by SEOModel
        super().save(*args, **kwargs)

    def publish(self) -> None:
        """Publish this product."""
        self.status = self.Status.PUBLISHED
        self.save(update_fields=["status", "updated_at"])

    def unpublish(self) -> None:
        """Unpublish (draft) this product."""
        self.status = self.Status.DRAFT
        self.save(update_fields=["status", "updated_at"])

    def hide(self) -> None:
        """Hide this product."""
        self.status = self.Status.HIDDEN
        self.save(update_fields=["status", "updated_at"])

    @property
    def is_published(self) -> bool:
        """Check if product is published."""
        return self.status == self.Status.PUBLISHED

    @property
    def has_discount(self) -> bool:
        """Check if product has a discount."""
        return bool(self.compare_price and self.compare_price > self.base_price)

    @property
    def discount_percentage(self) -> int:
        """Calculate discount percentage."""
        if not self.has_discount:
            return 0
        return int(((self.compare_price - self.base_price) / self.compare_price) * 100)


class ProductVariant(SoftDeleteModel, TimeStampedModel):
    """
    Product variant model - represents a specific SKU of a product.

    Variants are created based on variant attributes (is_variant=True).
    For example:
    - T-Shirt with Size+Color variants: S-Red, S-Blue, M-Red, M-Blue, etc.
    - Phone with RAM+Storage variants: 8GB-128GB, 8GB-256GB, 16GB-512GB, etc.

    Each variant has its own:
    - SKU (unique identifier)
    - Price (can differ from base_price)
    - Stock quantity
    - Images (variant-specific images)

    Attributes:
        public_id: UUID for public API access.
        product: Parent product.
        sku: Stock Keeping Unit - unique identifier.
        name: Variant name (e.g., "Red - Large").
        price: Variant price (overrides product.base_price if set).
        compare_price: Original price for discounts.
        cost_price: Cost to acquire.
        stock_quantity: Current stock level.
        low_stock_threshold: Alert when stock falls below this.
        weight: Shipping weight in kg.
        barcode: Barcode/UPC for scanning.
        is_active: Whether this variant is available for sale.
        is_default: Default variant to show (one per product).
        sort_order: Display order.

    Example:
        variant = ProductVariant.objects.create(
            product=tshirt,
            sku="CTEE-S-RED",
            name="Small - Red",
            price=25.00,
            stock_quantity=100
        )
    """

    public_id = models.UUIDField(unique=True, editable=False)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )
    sku = models.CharField(
        max_length=100, unique=True, db_index=True, help_text="Stock Keeping Unit"
    )
    name = models.CharField(
        max_length=255, help_text="Variant name (e.g., 'Red - Large')"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Variant price (if different from base price)",
    )
    compare_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Original price for showing discounts",
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Cost to acquire",
    )
    stock_quantity = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], help_text="Current stock level"
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=10, help_text="Alert when stock falls below this"
    )
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Weight in kg",
    )
    barcode = models.CharField(
        max_length=100, blank=True, help_text="Barcode/UPC for scanning"
    )
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Available for sale"
    )
    is_default = models.BooleanField(
        default=False, help_text="Default variant to display"
    )
    sort_order = models.PositiveIntegerField(default=0, help_text="Display order")

    class Meta:
        db_table = "products_productvariant"
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["product", "is_active"]),
            models.Index(fields=["stock_quantity"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Generate public_id on first save."""
        import uuid

        if not self.public_id:
            self.public_id = uuid.uuid4()

        super().save(*args, **kwargs)

    @property
    def effective_price(self) -> float:
        """Get the effective price (variant price or product base price)."""
        return self.price if self.price is not None else self.product.base_price

    @property
    def is_in_stock(self) -> bool:
        """Check if variant is in stock."""
        return self.stock_quantity > 0

    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below threshold."""
        return 0 < self.stock_quantity <= self.low_stock_threshold


class ProductAttributeValue(models.Model):
    """
    EAV storage for product-level attributes (is_variant=False).

    Stores non-variant attributes like Material, Brand, Care Instructions.
    These are properties of the product itself, not individual variants.

    Attributes:
        product: The product this value belongs to.
        attribute: The attribute definition.
        value: The actual value (stored as text, cast based on attribute.field_type).

    Example:
        # Material attribute for a T-Shirt
        ProductAttributeValue.objects.create(
            product=tshirt,
            attribute=material_attr,
            value="100% Cotton"
        )
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="attribute_values"
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.TextField(help_text="Attribute value (format depends on field_type)")

    class Meta:
        db_table = "products_productattributevalue"
        verbose_name = "Product Attribute Value"
        verbose_name_plural = "Product Attribute Values"
        unique_together = [("product", "attribute")]
        indexes = [
            models.Index(fields=["product"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.attribute.name}: {self.value}"


class VariantAttributeValue(models.Model):
    """
    EAV storage for variant-level attributes (is_variant=True).

    Stores variant-defining attributes like Size, Color, RAM, Storage.
    These differentiate one variant from another within the same product.

    Attributes:
        variant: The variant this value belongs to.
        attribute: The attribute definition.
        value: The actual value (e.g., "M", "Red", "8GB").

    Example:
        # Size=M, Color=Red for a specific T-Shirt variant
        VariantAttributeValue.objects.create(
            variant=variant,
            attribute=size_attr,
            value="M"
        )
        VariantAttributeValue.objects.create(
            variant=variant,
            attribute=color_attr,
            value="Red"
        )
    """

    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="attribute_values"
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.TextField(help_text="Attribute value")

    class Meta:
        db_table = "products_variantattributevalue"
        verbose_name = "Variant Attribute Value"
        verbose_name_plural = "Variant Attribute Values"
        unique_together = [("variant", "attribute")]
        indexes = [
            models.Index(fields=["variant"]),
        ]

    def __str__(self) -> str:
        return f"{self.variant.name} - {self.attribute.name}: {self.value}"


class ProductImage(SortableModel, TimeStampedModel):
    """
    Product image model - stores product and variant images.

    Images can be:
    - Product-level: General images (product field set, variant field null)
    - Variant-specific: Shown only for that variant (variant field set)

    Attributes:
        product: The product this image belongs to (required).
        variant: Optional - specific variant this image is for.
        image: Image file.
        alt_text: Alternative text for accessibility/SEO.
        is_primary: Whether this is the main image.
        sort_order: Display order.

    Example:
        # Product image (shown for all variants)
        ProductImage.objects.create(
            product=tshirt,
            image="products/tshirt.jpg",
            alt_text="Cotton T-Shirt",
            is_primary=True
        )

        # Variant-specific image
        ProductImage.objects.create(
            product=tshirt,
            variant=red_variant,
            image="products/tshirt-red.jpg",
            alt_text="Red T-Shirt"
        )
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="images",
        null=True,
        blank=True,
        help_text="Leave empty for product-level images",
    )
    image = models.ImageField(upload_to="products/%Y/%m/", help_text="Product image")
    alt_text = models.CharField(
        max_length=255, blank=True, help_text="Image description for SEO/accessibility"
    )
    is_primary = models.BooleanField(
        default=False, help_text="Main image for product/variant"
    )

    class Meta:
        db_table = "products_productimage"
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ["sort_order", "-created_at"]

    def __str__(self) -> str:
        if self.variant:
            return f"{self.variant.name} - Image"
        return f"{self.product.name} - Image"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Auto-generate alt_text if not provided."""
        if not self.alt_text:
            if self.variant:
                self.alt_text = f"{self.variant.name}"
            else:
                self.alt_text = f"{self.product.name}"

        super().save(*args, **kwargs)


class VariantPriceHistory(TimeStampedModel):
    """
    Track price changes for variants over time.

    Useful for:
    - Price history charts
    - Audit trail
    - Price drop notifications
    - Analytics

    Attributes:
        variant: The variant whose price changed.
        old_price: Previous price.
        new_price: New price.
        changed_by: User who made the change.

    Example:
        # Automatically logged when variant price changes
        VariantPriceHistory.objects.create(
            variant=variant,
            old_price=25.00,
            new_price=22.00,
            changed_by=admin_user
        )
    """

    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="price_history"
    )
    old_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    new_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    changed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="price_changes",
    )

    class Meta:
        db_table = "products_variantpricehistory"
        verbose_name = "Variant Price History"
        verbose_name_plural = "Variant Price History"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.variant.sku}: {self.old_price} → {self.new_price}"


# ============================================================================
# PHASE 6: INVENTORY MANAGEMENT
# ============================================================================


class InventoryLog(TimeStampedModel):
    """
    Inventory log model - tracks all stock changes for auditing.

    Every stock change is logged with:
    - What changed (quantity)
    - Why it changed (change_type)
    - Who made the change (created_by)
    - Reference to related entity (order, adjustment, etc.)

    This provides complete audit trail for inventory management.

    Attributes:
        variant: The product variant whose stock changed.
        change_type: Type of change (sold, restocked, adjustment, etc.).
        quantity_change: How much changed (positive for increase, negative for decrease).
        quantity_before: Stock level before change.
        quantity_after: Stock level after change.
        reference: Reference ID (order number, supplier invoice, etc.).
        notes: Additional context about the change.
        created_by: User who made the change (null for system changes).

    Example:
        # Log a sale
        InventoryLog.objects.create(
            variant=variant,
            change_type='sold',
            quantity_change=-2,
            quantity_before=100,
            quantity_after=98,
            reference='ORD-2026-00123',
            created_by=None  # System generated
        )

        # Log a restock
        InventoryLog.objects.create(
            variant=variant,
            change_type='restocked',
            quantity_change=50,
            quantity_before=98,
            quantity_after=148,
            reference='PO-2026-001',
            notes='Received from supplier',
            created_by=admin_user
        )
    """

    class ChangeType(models.TextChoices):
        """Types of inventory changes."""

        SOLD = "sold", "Sold (Order)"
        RESTOCKED = "restocked", "Restocked"
        ADJUSTMENT = "adjustment", "Manual Adjustment"
        RETURN = "return", "Customer Return"
        DAMAGED = "damaged", "Damaged/Lost"
        RESERVED = "reserved", "Reserved (Pending Order)"
        RELEASED = "released", "Released (Cancelled Order)"

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="inventory_logs",
        help_text="Variant whose stock changed",
    )
    change_type = models.CharField(
        max_length=20,
        choices=ChangeType.choices,
        db_index=True,
        help_text="Type of inventory change",
    )
    quantity_change = models.IntegerField(
        help_text="Change in quantity (positive=increase, negative=decrease)"
    )
    quantity_before = models.IntegerField(
        validators=[MinValueValidator(0)], help_text="Stock before change"
    )
    quantity_after = models.IntegerField(
        validators=[MinValueValidator(0)], help_text="Stock after change"
    )
    reference = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Reference ID (order number, PO number, etc.)",
    )
    notes = models.TextField(blank=True, help_text="Additional context")
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_changes",
        help_text="User who made the change (null for system)",
    )

    class Meta:
        db_table = "products_inventorylog"
        verbose_name = "Inventory Log"
        verbose_name_plural = "Inventory Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["variant", "-created_at"]),
            models.Index(fields=["change_type", "-created_at"]),
            models.Index(fields=["reference"]),
        ]

    def __str__(self) -> str:
        sign = "+" if self.quantity_change >= 0 else ""
        return (
            f"{self.variant.sku}: {sign}{self.quantity_change} "
            f"({self.quantity_before} → {self.quantity_after})"
        )
