"""Admin configuration for dashboard app."""

from django.contrib import admin

# Dashboard app doesn't have models to register.
# Dashboard functionality is provided through:
# 1. Dashboard callback in views.py (integrated with Unfold)
# 2. URL endpoints for AJAX data
# 3. Custom admin actions in other apps (orders, products, etc.)
