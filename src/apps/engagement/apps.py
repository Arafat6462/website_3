"""Django app configuration for engagement app."""

from django.apps import AppConfig


class EngagementConfig(AppConfig):
    """Configuration for the engagement application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.engagement"
    verbose_name = "Engagement"

    def ready(self) -> None:
        """Import signals when app is ready."""
        pass
