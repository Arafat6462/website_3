"""
Core Models Package.

This package contains abstract base models that provide common
functionality for all models in the application.

Available Models:
    - TimeStampedModel: Adds created_at, updated_at fields
    - SoftDeleteModel: Adds soft-delete capability (is_deleted, deleted_at)
    - PublishableModel: Adds publication status workflow
    - SEOModel: Adds SEO fields (slug, meta_title, meta_description)
    - SortableModel: Adds sort_order field for ordering

Usage:
    from apps.core.models import TimeStampedModel, SoftDeleteModel

    class Product(TimeStampedModel, SoftDeleteModel):
        name = models.CharField(max_length=255)
        # Automatically gets created_at, updated_at, is_deleted, deleted_at
"""

from apps.core.models.base import SoftDeleteModel, TimeStampedModel
from apps.core.models.publishable import PublishableModel
from apps.core.models.seo import SEOModel
from apps.core.models.sortable import SortableModel

__all__ = [
    "TimeStampedModel",
    "SoftDeleteModel",
    "PublishableModel",
    "SEOModel",
    "SortableModel",
]
