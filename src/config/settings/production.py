"""
Production Settings.

Security-hardened settings for production deployment.
Inherits from base settings and overrides for production environment.
"""

from .base import *

# =============================================================================
# Security Settings
# =============================================================================

# SECURITY WARNING: Keep DEBUG false in production!
DEBUG = env.bool("DEBUG", default=False)

# SECURITY WARNING: Set this to your actual domain in production
# Handle both string (from env var) and list (from base.py default)
ALLOWED_HOSTS_RAW = env("ALLOWED_HOSTS", default="ecom.arafat2.me,165.22.217.133,localhost")
if isinstance(ALLOWED_HOSTS_RAW, str):
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_RAW.split(",")]
else:
    ALLOWED_HOSTS = ALLOWED_HOSTS_RAW

# =============================================================================
# HTTPS & SSL Settings
# =============================================================================

# Force HTTPS
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)

# HSTS Settings (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# =============================================================================
# Cookie Security
# =============================================================================

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Session timeout (2 weeks)
SESSION_COOKIE_AGE = 1209600

# =============================================================================
# Security Headers
# =============================================================================

# Prevent clickjacking
X_FRAME_OPTIONS = 'DENY'

# Prevent MIME type sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# XSS Protection
SECURE_BROWSER_XSS_FILTER = True

# Referrer policy
SECURE_REFERRER_POLICY = 'same-origin'

# =============================================================================
# Content Security Policy
# =============================================================================
# Add CSP middleware if using django-csp package
# CSP_DEFAULT_SRC = ("'self'",)
# CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
# CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
# CSP_IMG_SRC = ("'self'", "data:", "https:")
# CSP_FONT_SRC = ("'self'", "data:")

# =============================================================================
# CORS Settings (Production)
# =============================================================================

# Restrict CORS to actual frontend domain
CORS_ALLOWED_ORIGINS = env(
    "CORS_ALLOWED_ORIGINS",
    default=["https://ecom.arafat2.me", "http://165.22.217.133"]
)

CORS_ALLOW_CREDENTIALS = True

# CSRF trusted origins for your actual domain
CSRF_TRUSTED_ORIGINS = env(
    "CSRF_TRUSTED_ORIGINS",
    default=["https://ecom.arafat2.me", "http://165.22.217.133"]
)

# =============================================================================
# Database Configuration (Production)
# =============================================================================
# Use environment variables for production database
# Never hardcode credentials!

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 600,  # Connection pooling
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# =============================================================================
# Static & Media Files (Production)
# =============================================================================

# Use local storage for now (S3 optional)
USE_S3 = env.bool("USE_S3", default=False)

if USE_S3:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default=None)
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
else:
    # Use local storage
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =============================================================================
# Email Configuration (Production)
# =============================================================================

EMAIL_BACKEND = env("EMAIL_BACKEND", default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@ecom.arafat2.me")
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)

# =============================================================================
# Logging Configuration (Production)
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
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/django/error.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# =============================================================================
# Password Validation (Strict in Production)
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,  # Stricter in production
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# =============================================================================
# Admin URL Obscurity (Security through obscurity)
# =============================================================================
# Change admin URL in production urls.py to something unpredictable
# Example: path("secret-admin-panel-xyz123/", admin.site.urls)

# =============================================================================
# Rate Limiting (Production)
# =============================================================================
# django-ratelimit uses cache backend
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://redis:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django.core.cache.cache.RedisClientClass",
        },
        "KEY_PREFIX": "ecom",
        "TIMEOUT": 300,
    }
}

# =============================================================================
# Additional Security Settings
# =============================================================================

# Prevent host header injection
USE_X_FORWARDED_HOST = False

# Prevent parameter pollution
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# File upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB

# Admin site security
ADMIN_URL = env("ADMIN_URL", default="admin/")  # Override in .env for obscurity
