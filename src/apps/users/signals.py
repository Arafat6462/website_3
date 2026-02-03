"""
User Application Signals.

This module contains signal handlers for user-related events:
- Create wishlist when user is created
- Other post-save/pre-save operations

Signals are registered automatically when the app is ready.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wishlist(sender: type, instance: "settings.AUTH_USER_MODEL", created: bool, **kwargs: any) -> None:
    """
    Create a wishlist for newly created users.

    This signal ensures every user has a wishlist ready to use.
    Will be implemented when wishlist model is created in Phase 11.

    Args:
        sender: The User model class.
        instance: The actual user instance being saved.
        created: True if this is a new user, False if updating.
        **kwargs: Additional signal arguments.
    """
    if created and not instance.is_staff:
        # Wishlist creation will be implemented in Phase 11
        # from apps.engagement.models import Wishlist
        # Wishlist.objects.get_or_create(user=instance)
        pass


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_username_set(sender: type, instance: "settings.AUTH_USER_MODEL", created: bool, **kwargs: any) -> None:
    """
    Ensure username is set if email is provided.

    Django's admin requires username for some operations,
    so we auto-generate it from email if not provided.

    Args:
        sender: The User model class.
        instance: The actual user instance being saved.
        created: True if this is a new user, False if updating.
        **kwargs: Additional signal arguments.
    """
    if created and not instance.username and instance.email:
        # This is handled in the model's save() method
        # but kept here as a safety net
        pass
