"""
Django Base Settings.

This module contains settings common to all environments (development, production).
Environment-specific settings should override these in their respective modules.

Settings are loaded from environment variables using django-environ for security.
Never hardcode sensitive values like SECRET_KEY or database credentials.

References:
    - Django Settings: https://docs.djangoproject.com/en/5.1/ref/settings/
    - django-environ: https://django-environ.readthedocs.io/
"""

import os
from pathlib import Path

import environ

# =============================================================================
# Path Configuration
# =============================================================================
# BASE_DIR: Points to the 'src' directory (where manage.py is located)
# ROOT_DIR: Points to the project root (where docker-compose.yml is located)
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent

# =============================================================================
# Environment Variables
# =============================================================================
# Initialize django-environ and read from .env file
# =============================================================================

env = environ.Env(
    # Set default values and casting
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
)

# Read .env file from project root
env_file = ROOT_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

# =============================================================================
# Core Settings
# =============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# =============================================================================
# Application Definition
# =============================================================================

DJANGO_APPS = [
    # Unfold admin must come before django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    # Django core apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    # REST Framework
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    # API Documentation
    "drf_spectacular",
    # Storage
    "storages",
    # Utilities
    "django_extensions",
]

LOCAL_APPS = [
    # Core app - abstract models, utilities, exceptions
    "apps.core",
    # Users app - custom user model, must come early
    "apps.users",
    # Products app - catalog, EAV attributes, categories
    "apps.products",
    # Orders app - cart, checkout, orders
    "apps.orders",
    # Engagement app - reviews, wishlist
    "apps.engagement",
    # Notifications app - email service
    "apps.notifications",
    # CMS app - pages, banners, settings
    "apps.cms",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =============================================================================
# Middleware Configuration
# =============================================================================

MIDDLEWARE = [
    # Security middleware should be first
    "django.middleware.security.SecurityMiddleware",
    # CORS headers - must be before CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# =============================================================================
# Template Configuration
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# =============================================================================
# Database Configuration
# =============================================================================
# Using PostgreSQL as specified in requirements
# Connection details loaded from environment variables
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="ecom_db"),
        "USER": env("DB_USER", default="ecom_user"),
        "PASSWORD": env("DB_PASSWORD", default="ecom_password"),
        "HOST": env("DB_HOST", default="db"),
        "PORT": env("DB_PORT", default="5432"),
        # Connection settings for reliability
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# Use atomic requests - entire view wrapped in transaction
# Automatically rolls back on exceptions
DATABASES["default"]["ATOMIC_REQUESTS"] = True

# =============================================================================
# Password Validation
# =============================================================================
# Strong password requirements for security
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# =============================================================================
# Custom User Model
# =============================================================================
# Using custom User model with email as username
# IMPORTANT: Must be set before running initial migrations
# =============================================================================

AUTH_USER_MODEL = "users.User"

# Password hashing - Argon2 is the most secure option
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# =============================================================================
# Internationalization
# =============================================================================
# Configured for Bangladesh market as per requirements
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

# =============================================================================
# Static Files (CSS, JavaScript, Images)
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = ROOT_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# =============================================================================
# Media Files (User Uploads)
# =============================================================================
# Default to local storage; production should use cloud storage
# =============================================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = ROOT_DIR / "media"

# =============================================================================
# Default Primary Key Field Type
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# Custom User Model
# =============================================================================
# Will be configured in Phase 3 when we create the users app
# AUTH_USER_MODEL = "users.User"
# =============================================================================

# =============================================================================
# Django REST Framework Configuration
# =============================================================================

REST_FRAMEWORK = {
    # Authentication
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Permissions - default to allow any, specific views will override
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    # Pagination
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Filtering
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # Schema generation
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Exception handling
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    # Date/time formats
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%SZ",
    "DATE_FORMAT": "%Y-%m-%d",
}

# =============================================================================
# JWT Settings
# =============================================================================

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# =============================================================================
# CORS Settings
# =============================================================================

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# CSRF Settings
# =============================================================================

CSRF_TRUSTED_ORIGINS = env(
    "CSRF_TRUSTED_ORIGINS",
    default=["http://localhost:8000", "http://127.0.0.1:8000"],
)

# =============================================================================
# API Documentation (drf-spectacular)
# =============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "E-Commerce API",
    "DESCRIPTION": "API for e-commerce backend with products, orders, and user management",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/v1",
}

# =============================================================================
# Django Unfold Admin Configuration
# =============================================================================

UNFOLD = {
    "SITE_TITLE": "E-Commerce Admin",
    "SITE_HEADER": "E-Commerce",
    "SITE_SYMBOL": "shopping_cart",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            # Navigation will be configured as we add apps
        ],
    },
}

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

# Email backend
# Development: Console backend (prints to terminal)
# Production: SMTP backend (actual email sending)
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)

# SMTP Configuration (used in production)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

# Sender email address
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", "noreply@example.com"
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Site information for email templates
SITE_NAME = os.getenv("SITE_NAME", "E-Commerce Store")
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

# =============================================================================
# Logging Configuration
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
