"""
WSGI Configuration for E-Commerce Backend.

This module exposes the WSGI callable as a module-level variable named `application`.

WSGI (Web Server Gateway Interface) is the Python standard for web servers
to communicate with web applications. This is used by production servers
like Gunicorn, uWSGI, etc.

Usage with Gunicorn:
    gunicorn config.wsgi:application --bind 0.0.0.0:8000

References:
    - WSGI: https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
    - Gunicorn: https://gunicorn.org/
"""

import os

from django.core.wsgi import get_wsgi_application

# Set the default Django settings module for the WSGI application
# This should be overridden by environment variable in production
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Create the WSGI application object
# This is the entry point for WSGI servers
application = get_wsgi_application()
