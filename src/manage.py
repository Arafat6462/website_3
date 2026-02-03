#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

This module provides the entry point for Django management commands.
It sets up the Django environment and delegates to Django's command handler.

Usage:
    python manage.py <command> [options]

Common Commands:
    runserver       - Start development server
    migrate         - Apply database migrations
    makemigrations  - Create new migrations
    createsuperuser - Create admin user
    shell           - Start interactive Python shell
    test            - Run tests

Environment:
    DJANGO_SETTINGS_MODULE: Settings module to use (default: config.settings.development)
"""

import os
import sys


def main() -> None:
    """
    Run administrative tasks.
    
    Sets up the Django settings module environment variable and
    executes the command line arguments through Django's management utility.
    
    Raises:
        ImportError: If Django is not installed or not available on PYTHONPATH.
    """
    # Set default settings module if not already set
    # In production, this should be overridden via environment variable
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
