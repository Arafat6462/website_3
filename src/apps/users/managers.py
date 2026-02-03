"""
Custom User Manager.

This module provides a custom user manager for creating users and superusers
with email as the primary identifier instead of username.
"""

from typing import Any

from django.contrib.auth.models import BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier.

    Provides methods to create regular users and superusers.
    Normalizes email addresses and ensures required fields are set.
    """

    def create_user(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> "models.Model":
        """
        Create and save a regular user with the given email and password.

        Args:
            email: User's email address (required).
            password: User's password. If None, user won't be able to login.
            **extra_fields: Additional fields to set on the user model.

        Returns:
            The created User instance.

        Raises:
            ValueError: If email is not provided.

        Example:
            user = User.objects.create_user(
                email='customer@example.com',
                password='secure_password',
                first_name='John',
                last_name='Doe'
            )
        """
        if not email:
            raise ValueError("Email address is required")

        # Normalize email (lowercase domain)
        email = self.normalize_email(email)

        # Ensure is_staff and is_superuser are False for regular users
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)

        # Create user instance
        user = self.model(email=email, **extra_fields)

        # Set password (hashed)
        if password:
            user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> "models.Model":
        """
        Create and save a superuser with the given email and password.

        Superusers have all permissions and can access the admin panel.

        Args:
            email: Superuser's email address (required).
            password: Superuser's password (required for login).
            **extra_fields: Additional fields to set on the user model.

        Returns:
            The created superuser instance.

        Raises:
            ValueError: If email is not provided or if is_staff/is_superuser
                       are explicitly set to False.

        Example:
            superuser = User.objects.create_superuser(
                email='admin@example.com',
                password='admin_password'
            )
        """
        # Ensure superuser flags are True
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email: str) -> "models.Model":
        """
        Get user by email (natural key for authentication).

        Args:
            email: User's email address.

        Returns:
            User instance matching the email.

        Raises:
            User.DoesNotExist: If no user with that email exists.
        """
        return self.get(email=email)

    def customers(self) -> models.QuerySet:
        """
        Get queryset of customer users (non-staff).

        Returns:
            QuerySet of users where is_staff=False.

        Example:
            customers = User.objects.customers()
        """
        return self.filter(is_staff=False)

    def staff(self) -> models.QuerySet:
        """
        Get queryset of staff users (admin panel access).

        Returns:
            QuerySet of users where is_staff=True.

        Example:
            staff_users = User.objects.staff()
        """
        return self.filter(is_staff=True)

    def active(self) -> models.QuerySet:
        """
        Get queryset of active users.

        Returns:
            QuerySet of users where is_active=True and is_blocked=False.

        Example:
            active_users = User.objects.active()
        """
        return self.filter(is_active=True, is_blocked=False)

    def blocked(self) -> models.QuerySet:
        """
        Get queryset of blocked users.

        Returns:
            QuerySet of users where is_blocked=True.

        Example:
            blocked_users = User.objects.blocked()
        """
        return self.filter(is_blocked=True)
