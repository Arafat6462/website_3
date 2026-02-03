"""CMS app configuration."""

from django.apps import AppConfig


class CmsConfig(AppConfig):
    """Configuration for CMS app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cms"
    verbose_name = "CMS"
