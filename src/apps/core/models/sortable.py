"""
Sortable Model.

This module provides an abstract model for manual ordering/sorting
of records using a sort_order field.

Use for categories, product images, menu items, and any content
that needs manual ordering.
"""

from typing import TYPE_CHECKING, Any

from django.db import models

from apps.core.models.base import TimeStampedModel

if TYPE_CHECKING:
    from django.db.models import QuerySet


class SortableModel(TimeStampedModel):
    """
    Abstract model providing manual sort order.

    Adds a sort_order field that can be used to manually order records.
    Lower numbers appear first (ascending order).

    Attributes:
        sort_order: Integer for manual ordering. Lower = first. Default 0.

    Ordering:
        By default, adds 'sort_order' to Meta.ordering. Child classes
        can override to add secondary ordering fields.

    Example:
        class Category(SortableModel):
            name = models.CharField(max_length=255)

            class Meta(SortableModel.Meta):
                ordering = ['sort_order', 'name']

        # Reorder categories
        cat1.sort_order = 1
        cat2.sort_order = 2
        cat3.sort_order = 3
    """

    sort_order = models.PositiveIntegerField(
        verbose_name="Sort Order",
        default=0,
        db_index=True,
        help_text="Display order. Lower numbers appear first.",
    )

    class Meta:
        abstract = True
        ordering = ["sort_order", "-created_at"]

    def move_up(self) -> bool:
        """
        Move this item up in the sort order (decrease sort_order).

        Swaps sort_order with the item immediately above this one.

        Returns:
            True if moved, False if already at top.

        Example:
            category.move_up()  # Now appears before previous item
        """
        # Find item with next lower sort_order
        above = (
            self.__class__.objects.filter(sort_order__lt=self.sort_order)
            .order_by("-sort_order")
            .first()
        )

        if above:
            # Swap sort_order values
            above.sort_order, self.sort_order = self.sort_order, above.sort_order
            above.save(update_fields=["sort_order"])
            self.save(update_fields=["sort_order"])
            return True

        return False

    def move_down(self) -> bool:
        """
        Move this item down in the sort order (increase sort_order).

        Swaps sort_order with the item immediately below this one.

        Returns:
            True if moved, False if already at bottom.

        Example:
            category.move_down()  # Now appears after next item
        """
        # Find item with next higher sort_order
        below = (
            self.__class__.objects.filter(sort_order__gt=self.sort_order)
            .order_by("sort_order")
            .first()
        )

        if below:
            # Swap sort_order values
            below.sort_order, self.sort_order = self.sort_order, below.sort_order
            below.save(update_fields=["sort_order"])
            self.save(update_fields=["sort_order"])
            return True

        return False

    def move_to(self, position: int) -> None:
        """
        Move this item to a specific position.

        Updates sort_order to the given position. Does not
        reorder other items - use reorder_all() for that.

        Args:
            position: New sort_order value.

        Example:
            category.move_to(5)  # Set sort_order = 5
        """
        self.sort_order = position
        self.save(update_fields=["sort_order"])

    @classmethod
    def reorder_all(cls, ordered_pks: list[int]) -> None:
        """
        Reorder all items based on a list of primary keys.

        Assigns sort_order values (0, 1, 2, ...) based on the
        order of IDs in the list.

        Args:
            ordered_pks: List of primary keys in desired order.

        Example:
            Category.reorder_all([3, 1, 4, 2])
            # Category 3 gets sort_order=0
            # Category 1 gets sort_order=1
            # etc.
        """
        for index, pk in enumerate(ordered_pks):
            cls.objects.filter(pk=pk).update(sort_order=index)

    @classmethod
    def get_next_sort_order(cls) -> int:
        """
        Get the next available sort_order value.

        Returns a value higher than the current maximum,
        useful for appending new items at the end.

        Returns:
            Integer one higher than current max sort_order.

        Example:
            new_category.sort_order = Category.get_next_sort_order()
        """
        max_order = cls.objects.aggregate(max_order=models.Max("sort_order"))["max_order"]
        return (max_order or 0) + 1
