"""
Users Application Configuration.

This module defines the Django application configuration for the users app.
Handles signal registration for automatic wishlist creation.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Configuration class for the Users application.

    Attributes:
        default_auto_field: The type of auto-created primary key fields.
        name: The full Python path to the application.
        verbose_name: Human-readable name for the application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    verbose_name = "Users & Authentication"

    def ready(self) -> None:
        """
        Perform initialization tasks when the app is ready.

        Imports signals to ensure they are registered when Django starts.
        """
        # Import signals to register them
        import apps.users.signals  # noqa: F401
