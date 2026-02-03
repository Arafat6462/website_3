"""
ASGI Configuration for E-Commerce Backend.

This module exposes the ASGI callable as a module-level variable named `application`.

ASGI (Asynchronous Server Gateway Interface) is the Python standard for
async-capable web servers to communicate with web applications. This enables
handling of WebSockets, HTTP/2, and other async protocols.

Usage with Uvicorn:
    uvicorn config.asgi:application --host 0.0.0.0 --port 8000

Usage with Daphne:
    daphne config.asgi:application --bind 0.0.0.0 --port 8000

Note:
    For this project, we primarily use WSGI (Gunicorn) in production.
    ASGI is provided for future async capabilities if needed.

References:
    - ASGI: https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
    - Uvicorn: https://www.uvicorn.org/
"""

import os

from django.core.asgi import get_asgi_application

# Set the default Django settings module for the ASGI application
# This should be overridden by environment variable in production
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Create the ASGI application object
# This is the entry point for ASGI servers
application = get_asgi_application()
