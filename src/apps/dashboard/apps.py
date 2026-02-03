"""Django app configuration for dashboard."""

from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """
    Configuration for the dashboard application.
    
    This app provides admin dashboard functionality including
    statistics, charts, and analytics.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = 'Dashboard'
