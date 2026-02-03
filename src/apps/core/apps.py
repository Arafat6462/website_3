"""
Core Application Configuration.

This module defines the Django application configuration for the core app.
The core app provides foundational components used throughout the project.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuration class for the Core application.

    Attributes:
        default_auto_field: The type of auto-created primary key fields.
        name: The full Python path to the application.
        verbose_name: Human-readable name for the application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self) -> None:
        """
        Perform initialization tasks when the app is ready.

        This method is called once Django has loaded all applications.
        Currently unused but available for signal registration if needed.
        """
        pass
