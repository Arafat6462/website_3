"""
Publishable Model.

This module provides an abstract model for content that goes through
a publication workflow (draft → published → hidden).

Use for products, pages, blog posts, and any content that needs
visibility control.
"""

from typing import Any

from django.db import models
from django.utils import timezone

from apps.core.models.base import TimeStampedModel


class PublishableModel(TimeStampedModel):
    """
    Abstract model for content with publication status.

    Provides a status field with draft/published/hidden workflow,
    plus optional publish scheduling.

    Attributes:
        status: Current publication status (draft, published, hidden).
        published_at: When the content was/will be published.

    Status Workflow:
        draft → Content being prepared, not visible publicly
        published → Live and visible to users
        hidden → Was published but now hidden (e.g., out of season)

    Example:
        class Product(PublishableModel):
            name = models.CharField(max_length=255)

        # Create as draft
        product = Product.objects.create(name="T-Shirt", status="draft")

        # Publish
        product.publish()

        # Hide temporarily
        product.hide()
    """

    class Status(models.TextChoices):
        """Publication status choices."""

        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        HIDDEN = "hidden", "Hidden"

    status = models.CharField(
        verbose_name="Status",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Publication status of this content.",
    )

    published_at = models.DateTimeField(
        verbose_name="Published At",
        null=True,
        blank=True,
        db_index=True,
        help_text="Date and time when this content was published.",
    )

    class Meta:
        abstract = True

    def publish(self, commit: bool = True) -> None:
        """
        Publish this content, making it visible to users.

        Sets status to 'published' and records the publication timestamp
        if not already set.

        Args:
            commit: If True, saves the model after updating. Defaults to True.

        Example:
            product.publish()  # Immediately visible
        """
        self.status = self.Status.PUBLISHED

        if self.published_at is None:
            self.published_at = timezone.now()

        if commit:
            self.save(update_fields=["status", "published_at", "updated_at"])

    def unpublish(self, commit: bool = True) -> None:
        """
        Revert content to draft status.

        Sets status to 'draft'. Does NOT clear published_at
        to preserve publication history.

        Args:
            commit: If True, saves the model after updating. Defaults to True.

        Example:
            product.unpublish()  # Back to draft, needs review
        """
        self.status = self.Status.DRAFT

        if commit:
            self.save(update_fields=["status", "updated_at"])

    def hide(self, commit: bool = True) -> None:
        """
        Hide published content without reverting to draft.

        Use for temporarily hiding content (e.g., seasonal products,
        content under review) while indicating it was previously published.

        Args:
            commit: If True, saves the model after updating. Defaults to True.

        Example:
            product.hide()  # Temporarily hidden, can unhide later
        """
        self.status = self.Status.HIDDEN

        if commit:
            self.save(update_fields=["status", "updated_at"])

    @property
    def is_published(self) -> bool:
        """
        Check if content is currently published.

        Returns:
            True if status is 'published', False otherwise.
        """
        return self.status == self.Status.PUBLISHED

    @property
    def is_draft(self) -> bool:
        """
        Check if content is in draft status.

        Returns:
            True if status is 'draft', False otherwise.
        """
        return self.status == self.Status.DRAFT

    @property
    def is_hidden(self) -> bool:
        """
        Check if content is hidden.

        Returns:
            True if status is 'hidden', False otherwise.
        """
        return self.status == self.Status.HIDDEN

    @property
    def is_visible(self) -> bool:
        """
        Check if content should be visible to public.

        Currently same as is_published, but can be extended
        for scheduled publishing.

        Returns:
            True if content should be publicly visible.
        """
        return self.is_published
