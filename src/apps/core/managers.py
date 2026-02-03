"""
Core Application Managers.

This module contains custom Django model managers that provide
filtered querysets for common patterns like soft-delete and publishing.

Managers:
    - SoftDeleteManager: Excludes soft-deleted records by default
    - PublishedManager: Returns only published records
    - SoftDeleteAllManager: Includes soft-deleted records

Usage:
    class Product(SoftDeleteModel):
        # Default manager excludes deleted
        objects = SoftDeleteManager()
        # Include deleted items when needed
        all_objects = SoftDeleteAllManager()

    # Normal queries exclude deleted items
    Product.objects.all()  # Only non-deleted

    # Include deleted when needed (admin, restore, etc.)
    Product.all_objects.all()  # All including deleted
"""

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models import QuerySet


class SoftDeleteQuerySet(models.QuerySet):
    """
    Custom QuerySet that supports soft-delete operations.

    Provides bulk soft-delete and restore operations while maintaining
    the standard QuerySet interface.
    """

    def delete(self) -> tuple[int, dict[str, int]]:
        """
        Soft-delete all records in the queryset.

        Instead of actually deleting records, sets is_deleted=True.
        For actual deletion, use hard_delete().

        Returns:
            Tuple of (count, {model_label: count}) matching Django's delete signature.
        """
        from django.utils import timezone

        count = self.update(is_deleted=True, deleted_at=timezone.now())
        return count, {self.model._meta.label: count}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        """
        Permanently delete all records in the queryset.

        WARNING: This cannot be undone. Use with caution.

        Returns:
            Tuple of (count, {model_label: count}) from actual deletion.
        """
        return super().delete()

    def restore(self) -> int:
        """
        Restore all soft-deleted records in the queryset.

        Returns:
            Number of records restored.
        """
        return self.update(is_deleted=False, deleted_at=None)


class SoftDeleteManager(models.Manager):
    """
    Manager that excludes soft-deleted records by default.

    Use this as the default manager for models with soft-delete
    to ensure deleted records don't appear in normal queries.

    Example:
        class Product(SoftDeleteModel):
            objects = SoftDeleteManager()

        # These queries automatically exclude deleted products
        Product.objects.all()
        Product.objects.filter(price__gt=100)
    """

    def get_queryset(self) -> "QuerySet":
        """
        Return queryset excluding soft-deleted records.

        Returns:
            QuerySet filtered to exclude is_deleted=True records.
        """
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class SoftDeleteAllManager(models.Manager):
    """
    Manager that includes ALL records, even soft-deleted ones.

    Use this when you need to access deleted records, such as:
    - Admin interface (to see/restore deleted items)
    - Reports that need historical data
    - Restore operations

    Example:
        class Product(SoftDeleteModel):
            objects = SoftDeleteManager()
            all_objects = SoftDeleteAllManager()

        # Access deleted products
        Product.all_objects.filter(is_deleted=True)
    """

    def get_queryset(self) -> "QuerySet":
        """
        Return queryset including all records.

        Returns:
            Unfiltered SoftDeleteQuerySet.
        """
        return SoftDeleteQuerySet(self.model, using=self._db)


class PublishedQuerySet(models.QuerySet):
    """
    Custom QuerySet for publishable content.

    Provides convenient methods for filtering by publication status.
    """

    def published(self) -> "QuerySet":
        """
        Filter to only published records.

        Returns:
            QuerySet of records with status='published'.
        """
        return self.filter(status="published")

    def draft(self) -> "QuerySet":
        """
        Filter to only draft records.

        Returns:
            QuerySet of records with status='draft'.
        """
        return self.filter(status="draft")

    def hidden(self) -> "QuerySet":
        """
        Filter to only hidden records.

        Returns:
            QuerySet of records with status='hidden'.
        """
        return self.filter(status="hidden")


class PublishedManager(models.Manager):
    """
    Manager that returns only published records by default.

    Use this for public-facing queries where only published
    content should be visible.

    Example:
        class Product(PublishableModel):
            # For public API/frontend
            published = PublishedManager()
            # For admin (all statuses)
            objects = models.Manager()

        # Frontend shows only published
        Product.published.all()
    """

    def get_queryset(self) -> "QuerySet":
        """
        Return queryset of only published records.

        Returns:
            QuerySet filtered to status='published'.
        """
        return PublishedQuerySet(self.model, using=self._db).filter(status="published")
