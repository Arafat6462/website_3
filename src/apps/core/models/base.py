"""
Base Abstract Models.

This module provides fundamental abstract models that handle:
- Automatic timestamp tracking (created_at, updated_at)
- Soft-delete functionality (is_deleted, deleted_at)

These models form the foundation for most other models in the application.
"""

from typing import Any

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract model that provides automatic timestamp fields.

    Automatically tracks when records are created and last modified.
    Should be inherited by virtually all models in the application.

    Attributes:
        created_at: Timestamp when the record was created. Auto-set, not editable.
        updated_at: Timestamp when the record was last modified. Auto-updated.

    Example:
        class Product(TimeStampedModel):
            name = models.CharField(max_length=255)

        # created_at and updated_at are automatically managed
        product = Product.objects.create(name="T-Shirt")
        print(product.created_at)  # 2026-02-03 12:00:00
    """

    created_at = models.DateTimeField(
        verbose_name="Created At",
        auto_now_add=True,
        editable=False,
        db_index=True,
        help_text="Timestamp when this record was created.",
    )

    updated_at = models.DateTimeField(
        verbose_name="Updated At",
        auto_now=True,
        help_text="Timestamp when this record was last modified.",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        get_latest_by = "created_at"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save the model instance.

        Ensures updated_at is always refreshed, even in bulk operations
        where auto_now might not trigger.

        Args:
            *args: Positional arguments passed to parent save().
            **kwargs: Keyword arguments passed to parent save().
        """
        # If update_fields is specified, ensure updated_at is included
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            update_fields = set(update_fields)
            update_fields.add("updated_at")
            kwargs["update_fields"] = list(update_fields)

        super().save(*args, **kwargs)


class SoftDeleteModel(TimeStampedModel):
    """
    Abstract model that provides soft-delete functionality.

    Instead of permanently deleting records, marks them as deleted.
    Deleted records can be restored and are excluded from normal queries.

    Inherits from TimeStampedModel for timestamp tracking.

    Attributes:
        is_deleted: Boolean flag indicating if record is soft-deleted.
        deleted_at: Timestamp when record was soft-deleted. Null if not deleted.

    Manager Notes:
        - Use SoftDeleteManager as default to auto-exclude deleted records
        - Use SoftDeleteAllManager to include deleted records when needed

    Example:
        class Product(SoftDeleteModel):
            objects = SoftDeleteManager()      # Excludes deleted
            all_objects = SoftDeleteAllManager()  # Includes all

            name = models.CharField(max_length=255)

        product = Product.objects.get(pk=1)
        product.delete()  # Soft-deletes, doesn't remove from DB

        # Restore if needed
        product.restore()
    """

    is_deleted = models.BooleanField(
        verbose_name="Is Deleted",
        default=False,
        db_index=True,
        help_text="Indicates if this record has been soft-deleted.",
    )

    deleted_at = models.DateTimeField(
        verbose_name="Deleted At",
        null=True,
        blank=True,
        editable=False,
        help_text="Timestamp when this record was soft-deleted.",
    )

    class Meta:
        abstract = True

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        """
        Soft-delete this record.

        Sets is_deleted=True and records the deletion timestamp.
        Does NOT permanently remove the record from the database.

        For permanent deletion, use hard_delete().

        Args:
            using: Database alias to use.
            keep_parents: Whether to keep parent links (unused in soft-delete).

        Returns:
            Tuple of (1, {model_label: 1}) to match Django's delete signature.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

        return 1, {self._meta.label: 1}

    def hard_delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        """
        Permanently delete this record from the database.

        WARNING: This action cannot be undone.

        Args:
            using: Database alias to use.
            keep_parents: Whether to keep parent links.

        Returns:
            Tuple of (count, {model_label: count}) from actual deletion.
        """
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self) -> None:
        """
        Restore a soft-deleted record.

        Clears the is_deleted flag and deleted_at timestamp,
        making the record visible in normal queries again.

        Example:
            product = Product.all_objects.get(pk=1)
            product.restore()  # Now visible in Product.objects queries
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

    @property
    def is_active(self) -> bool:
        """
        Check if record is active (not deleted).

        Returns:
            True if record is not soft-deleted, False otherwise.
        """
        return not self.is_deleted
