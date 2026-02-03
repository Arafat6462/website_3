"""
Core Application Package.

This package contains reusable components shared across all apps:
- Abstract base models (TimeStampedModel, SoftDeleteModel, etc.)
- Custom managers (SoftDeleteManager, PublishedManager)
- Utility functions (slug generation, SKU generation)
- Custom exceptions

Usage:
    from apps.core.models import TimeStampedModel, SoftDeleteModel
    from apps.core.managers import SoftDeleteManager
    from apps.core.utils import generate_unique_slug
"""

default_app_config = "apps.core.apps.CoreConfig"
