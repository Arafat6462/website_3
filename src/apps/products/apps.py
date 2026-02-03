"""
Products Application Configuration.

This module defines the Django application configuration for the products app.
Handles product catalog, categories, and EAV attribute system.
"""

from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """
    Configuration class for the Products application.

    Attributes:
        default_auto_field: The type of auto-created primary key fields.
        name: The full Python path to the application.
        verbose_name: Human-readable name for the application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.products"
    verbose_name = "Products & Catalog"

    def ready(self) -> None:
        """
        Perform initialization tasks when the app is ready.

        Currently unused but available for signal registration if needed.
        """
        pass
