"""
Django Settings Package.

This package provides environment-specific settings:
- base.py: Common settings shared across all environments
- development.py: Development-specific settings (DEBUG=True, etc.)
- production.py: Production-specific settings (security hardened)

The active settings module is determined by the DJANGO_SETTINGS_MODULE
environment variable, which should be set to one of:
- config.settings.development (default for local development)
- config.settings.production (for production deployment)

Usage:
    # In .env file or environment:
    DJANGO_SETTINGS_MODULE=config.settings.development
"""
