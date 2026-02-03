"""
Users Application Package.

This package contains user authentication and profile management:
- Custom User model with e-commerce fields
- CustomerAddress model for shipping/billing addresses
- Staff permission groups for admin panel access
- User statistics tracking

Usage:
    from apps.users.models import User, CustomerAddress
    
    user = User.objects.create_user('customer@example.com', 'password')
"""

default_app_config = "apps.users.apps.UsersConfig"
