"""
Django Development Settings.

This module extends base settings with development-specific configuration.
These settings prioritize developer experience and debugging capabilities.

WARNING: These settings are NOT secure for production use!

Features enabled:
    - DEBUG mode for detailed error pages
    - Django Debug Toolbar for performance analysis
    - Console email backend (no actual emails sent)
    - Local file storage for media
    - Relaxed security settings
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# Debug Mode
# =============================================================================
# Enable debug mode for detailed error pages and development tools
# =============================================================================

DEBUG = True

# =============================================================================
# Allowed Hosts
# =============================================================================
# In development, allow localhost and common local addresses
# =============================================================================

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "[::1]",
]

# =============================================================================
# Debug Toolbar Configuration
# =============================================================================
# Only installed in development for performance profiling
# Disabled during tests
# =============================================================================

import sys

# Only enable debug toolbar if not running tests
TESTING = 'test' in sys.argv

if not TESTING:
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ] + MIDDLEWARE  # noqa: F405

    # IPs allowed to see debug toolbar
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
    ]

    # Docker-specific: Allow debug toolbar in Docker container
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
        "IS_RUNNING_TESTS": False,
    }

# =============================================================================
# Email Configuration
# =============================================================================
# Use console backend - emails printed to terminal instead of sent
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# Database Configuration
# =============================================================================
# Development can use the same database settings from base
# Connection pooling is less important in development
# =============================================================================

DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405

# =============================================================================
# Static & Media Files
# =============================================================================
# Use local file storage in development
# =============================================================================

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# =============================================================================
# CORS Configuration
# =============================================================================
# Allow all origins in development for easier frontend testing
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# Logging Configuration
# =============================================================================
# More verbose logging in development
# =============================================================================

LOGGING["loggers"]["django.db.backends"] = {  # noqa: F405
    "handlers": ["console"],
    "level": "WARNING",  # Set to DEBUG to see all SQL queries
    "propagate": False,
}

# =============================================================================
# Security Settings (Relaxed for Development)
# =============================================================================
# These are deliberately insecure for local development convenience
# NEVER use these settings in production!
# =============================================================================

# Session settings
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True

# CSRF settings
CSRF_COOKIE_SECURE = False

# Security headers (disabled in development)
SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = "SAMEORIGIN"

# =============================================================================
# Django Extensions
# =============================================================================
# Additional development tools
# =============================================================================

SHELL_PLUS_PRINT_SQL = True  # Print SQL in shell_plus

# =============================================================================
# Cache Configuration
# =============================================================================
# Use local memory cache in development (no Redis/Memcached needed)
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
