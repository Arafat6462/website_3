"""
Category Manager.

This module provides a custom manager for the Category model
with methods for working with hierarchical category trees.
"""

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models import QuerySet


class CategoryManager(models.Manager):
    """
    Custom manager for Category model with tree operations.

    Provides methods for efficiently querying and manipulating
    hierarchical category structures.
    """

    def root_categories(self) -> "QuerySet":
        """
        Get all root (top-level) categories.

        Returns:
            QuerySet of categories where parent is None.

        Example:
            root_cats = Category.objects.root_categories()
        """
        return self.filter(parent__isnull=True)

    def get_children(self, category: "models.Model") -> "QuerySet":
        """
        Get immediate children of a category.

        Args:
            category: The parent category instance.

        Returns:
            QuerySet of direct child categories.

        Example:
            children = Category.objects.get_children(parent_category)
        """
        return self.filter(parent=category)

    def get_descendants(self, category: "models.Model") -> "QuerySet":
        """
        Get all descendants of a category (children, grandchildren, etc.).

        Uses a recursive approach to find all nested children.

        Args:
            category: The parent category instance.

        Returns:
            QuerySet of all descendant categories.

        Example:
            all_descendants = Category.objects.get_descendants(category)
        """
        # Start with direct children
        descendants = list(self.get_children(category))
        
        # Recursively get descendants of each child
        for child in list(descendants):
            descendants.extend(self.get_descendants(child))
        
        # Return as queryset
        pks = [d.pk for d in descendants]
        return self.filter(pk__in=pks)

    def get_ancestors(self, category: "models.Model") -> list:
        """
        Get all ancestors of a category (parent, grandparent, etc.).

        Returns a list ordered from immediate parent to root.

        Args:
            category: The category instance.

        Returns:
            List of ancestor category instances.

        Example:
            ancestors = Category.objects.get_ancestors(category)
            # Returns: [parent, grandparent, root]
        """
        ancestors = []
        current = category.parent
        
        while current is not None:
            ancestors.append(current)
            current = current.parent
        
        return ancestors

    def get_tree_path(self, category: "models.Model") -> list:
        """
        Get full tree path from root to category.

        Args:
            category: The category instance.

        Returns:
            List of categories from root to the given category.

        Example:
            path = Category.objects.get_tree_path(category)
            # Returns: [root, parent, category]
        """
        ancestors = self.get_ancestors(category)
        ancestors.reverse()  # Root first
        ancestors.append(category)  # Add current category
        return ancestors

    def active(self) -> "QuerySet":
        """
        Get all active categories.

        Returns:
            QuerySet of categories with status='active'.

        Example:
            active_cats = Category.objects.active()
        """
        return self.filter(status="active")
