"""
Engagement Application Models - Phase 11: Social Proof & User Interaction.

This module contains models for customer engagement:
- ProductReview: Customer product reviews with ratings and approval workflow
- Wishlist: User wishlist for saved products
- WishlistItem: Items in a user's wishlist
"""

from typing import Any
import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class ProductReview(TimeStampedModel):
    """
    Customer product reviews with ratings and admin approval.

    Features:
    - Star rating (1-5)
    - Text comment
    - Optional images (JSON array)
    - Admin approval workflow
    - Admin can reply to reviews
    
    Attributes:
        user: Customer who wrote the review
        product: Product being reviewed
        rating: Star rating (1-5)
        comment: Review text
        images: Optional review images (JSON array of URLs)
        is_approved: Admin approval status
        admin_reply: Admin's response to review
        admin_replied_at: When admin replied
        
    Example:
        review = ProductReview.objects.create(
            user=user,
            product=product,
            rating=5,
            comment="Excellent product! Highly recommended."
        )
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Star rating from 1 to 5",
    )
    comment = models.TextField(help_text="Review text")
    images = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of image URLs",
    )
    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Admin approval status",
    )
    admin_reply = models.TextField(
        blank=True,
        help_text="Admin's response to review",
    )
    admin_replied_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When admin replied",
    )

    class Meta:
        db_table = "engagement_productreview"
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["is_approved", "-created_at"]),
            models.Index(fields=["rating"]),
        ]
        # One review per user per product
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_review",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.product.name} ({self.rating}★)"

    @property
    def has_admin_reply(self) -> bool:
        """Check if admin has replied to this review."""
        return bool(self.admin_reply)

    def approve(self) -> None:
        """Approve this review."""
        self.is_approved = True
        self.save(update_fields=["is_approved", "updated_at"])

    def reject(self) -> None:
        """Reject (unapprove) this review."""
        self.is_approved = False
        self.save(update_fields=["is_approved", "updated_at"])

    def add_admin_reply(self, reply: str) -> None:
        """
        Add admin reply to review.
        
        Args:
            reply: Admin's response text
        """
        self.admin_reply = reply
        self.admin_replied_at = timezone.now()
        self.save(update_fields=["admin_reply", "admin_replied_at", "updated_at"])


class Wishlist(TimeStampedModel):
    """
    User wishlist for saved products.

    Each user has one wishlist containing multiple items.
    
    Attributes:
        public_id: UUID for external reference
        user: Wishlist owner
        
    Example:
        wishlist = Wishlist.objects.create(user=user)
    """

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="wishlist",
    )

    class Meta:
        db_table = "engagement_wishlist"
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"

    def __str__(self) -> str:
        return f"Wishlist - {self.user.email}"

    @property
    def item_count(self) -> int:
        """Get total number of items in wishlist."""
        return self.items.count()


class WishlistItem(TimeStampedModel):
    """
    Individual item in a user's wishlist.

    Links wishlist to specific product variants.
    
    Attributes:
        wishlist: Parent wishlist
        variant: Product variant saved
        
    Example:
        item = WishlistItem.objects.create(
            wishlist=wishlist,
            variant=variant
        )
    """

    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )

    class Meta:
        db_table = "engagement_wishlistitem"
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"
        ordering = ["-created_at"]
        # One variant per wishlist
        constraints = [
            models.UniqueConstraint(
                fields=["wishlist", "variant"],
                name="unique_wishlist_variant",
            )
        ]

    def __str__(self) -> str:
        return f"{self.wishlist.user.email} - {self.variant.name}"
