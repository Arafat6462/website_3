"""
Users Application Models.

This module contains user-related models:
- User: Custom user model with e-commerce fields
- CustomerAddress: Shipping/billing addresses for customers

The User model extends Django's AbstractUser but uses email as the
primary identifier instead of username.
"""

import uuid
from decimal import Decimal
from typing import Any

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.users.managers import UserManager


class User(AbstractUser):
    """
    Custom User model for the e-commerce platform.

    Extends Django's AbstractUser with additional e-commerce fields.
    Uses email as the primary identifier instead of username.

    Attributes:
        public_id: UUID for public API exposure (instead of sequential ID).
        email: Email address (unique, used for login).
        phone: Phone number (unique, Bangladeshi format).
        is_blocked: Whether user is blocked from the platform.
        block_reason: Reason for blocking (admin use).
        email_verified: Whether user's email has been verified.
        total_orders: Count of completed orders (cached).
        total_spent: Total amount spent on orders (cached).
        admin_notes: Internal notes about the user (staff only).

    Staff Fields (inherited from AbstractUser):
        is_staff: Can access admin panel.
        is_superuser: Has all permissions.
        groups: Permission groups assigned to this user.

    Example:
        # Create customer
        user = User.objects.create_user(
            email='customer@example.com',
            password='password123',
            phone='01712345678'
        )

        # Create staff member
        staff = User.objects.create_user(
            email='manager@example.com',
            password='password123',
            is_staff=True
        )
        staff.groups.add(order_managers_group)
    """

    # Override username to be optional (we use email for login)
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        help_text="Optional username. Email is used for authentication.",
    )

    # Public UUID for API exposure
    public_id = models.UUIDField(
        verbose_name="Public ID",
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text="Public identifier for API responses.",
    )

    # Email as primary identifier
    email = models.EmailField(
        verbose_name="Email Address",
        unique=True,
        db_index=True,
        help_text="Email address used for login and communication.",
    )

    # Phone number (Bangladeshi format: 11 digits starting with 01)
    phone_validator = RegexValidator(
        regex=r"^01[0-9]{9}$",
        message="Enter a valid Bangladeshi phone number (11 digits starting with 01).",
    )

    phone = models.CharField(
        verbose_name="Phone Number",
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        validators=[phone_validator],
        db_index=True,
        help_text="Bangladeshi phone number (e.g., 01712345678).",
    )

    # Blocking functionality
    is_blocked = models.BooleanField(
        verbose_name="Is Blocked",
        default=False,
        db_index=True,
        help_text="Block user from accessing the platform.",
    )

    block_reason = models.TextField(
        verbose_name="Block Reason",
        blank=True,
        help_text="Reason for blocking this user (internal use).",
    )

    # Email verification
    email_verified = models.BooleanField(
        verbose_name="Email Verified",
        default=False,
        help_text="Whether user has verified their email address.",
    )

    # Order statistics (cached for performance)
    total_orders = models.PositiveIntegerField(
        verbose_name="Total Orders",
        default=0,
        help_text="Total number of completed orders.",
    )

    total_spent = models.DecimalField(
        verbose_name="Total Spent",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total amount spent on all orders.",
    )

    # Admin notes
    admin_notes = models.TextField(
        verbose_name="Admin Notes",
        blank=True,
        help_text="Internal notes about this user (visible only to staff).",
    )

    # Use email for authentication
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # Email is already in USERNAME_FIELD

    # Custom manager
    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["is_staff", "is_active"]),
            models.Index(fields=["is_blocked"]),
        ]

    def __str__(self) -> str:
        """
        String representation of the user.

        Returns:
            User's email or full name if available.
        """
        if self.get_full_name():
            return f"{self.get_full_name()} ({self.email})"
        return self.email

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save the user instance.

        Ensures email is set if username is being used, and vice versa.
        """
        # If no username, use email prefix
        if not self.username and self.email:
            self.username = self.email.split("@")[0] + f"-{uuid.uuid4().hex[:6]}"

        super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        """
        Get user's full name.

        Returns:
            First name + last name, or email if names not set.
        """
        full_name = super().get_full_name()
        return full_name if full_name.strip() else self.email

    def get_short_name(self) -> str:
        """
        Get user's short name.

        Returns:
            First name, or email prefix if not set.
        """
        if self.first_name:
            return self.first_name
        return self.email.split("@")[0]

    @property
    def is_customer(self) -> bool:
        """
        Check if user is a customer (not staff).

        Returns:
            True if user is not staff, False otherwise.
        """
        return not self.is_staff

    @property
    def can_login(self) -> bool:
        """
        Check if user can login.

        Users cannot login if they are blocked or inactive.

        Returns:
            True if user can login, False otherwise.
        """
        return self.is_active and not self.is_blocked

    def block(self, reason: str = "") -> None:
        """
        Block this user from accessing the platform.

        Args:
            reason: Reason for blocking (optional).

        Example:
            user.block("Fraudulent activity detected")
        """
        self.is_blocked = True
        self.block_reason = reason
        self.save(update_fields=["is_blocked", "block_reason"])

    def unblock(self) -> None:
        """
        Unblock this user, allowing access again.

        Example:
            user.unblock()
        """
        self.is_blocked = False
        self.block_reason = ""
        self.save(update_fields=["is_blocked", "block_reason"])

    def verify_email(self) -> None:
        """
        Mark user's email as verified.

        Example:
            user.verify_email()
        """
        self.email_verified = True
        self.save(update_fields=["email_verified"])

    def update_order_stats(self, order_total: Decimal) -> None:
        """
        Update user's order statistics after a completed order.

        Args:
            order_total: Total amount of the completed order.

        Example:
            user.update_order_stats(Decimal('1500.00'))
        """
        self.total_orders += 1
        self.total_spent += order_total
        self.save(update_fields=["total_orders", "total_spent"])


class CustomerAddress(TimeStampedModel):
    """
    Customer shipping/billing address model.

    Stores delivery addresses for customers. Users can have multiple
    addresses with one marked as default.

    Attributes:
        user: The user who owns this address.
        label: Custom label for the address (e.g., "Home", "Office").
        recipient_name: Name of person receiving deliveries.
        phone: Contact phone number for deliveries.
        address_line1: Street address, building name, etc.
        address_line2: Apartment, suite, floor, etc. (optional).
        city: City name.
        area: Area/district within city.
        postal_code: Postal/ZIP code (optional for Bangladesh).
        is_default: Whether this is the default address.

    Business Rules:
        - Each user can have multiple addresses
        - Only one address can be default per user
        - Setting a new default automatically unsets the previous one

    Example:
        address = CustomerAddress.objects.create(
            user=user,
            label='Home',
            recipient_name='John Doe',
            phone='01712345678',
            address_line1='123 Main St',
            city='Dhaka',
            area='Gulshan',
            is_default=True
        )
    """

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name="User",
        help_text="User who owns this address.",
    )

    label = models.CharField(
        verbose_name="Label",
        max_length=50,
        blank=True,
        help_text="Custom label (e.g., 'Home', 'Office').",
    )

    recipient_name = models.CharField(
        verbose_name="Recipient Name",
        max_length=255,
        help_text="Full name of person receiving deliveries.",
    )

    phone = models.CharField(
        verbose_name="Phone Number",
        max_length=11,
        validators=[User.phone_validator],
        help_text="Contact phone number for deliveries.",
    )

    address_line1 = models.CharField(
        verbose_name="Address Line 1",
        max_length=255,
        help_text="Street address, building name, house number.",
    )

    address_line2 = models.CharField(
        verbose_name="Address Line 2",
        max_length=255,
        blank=True,
        help_text="Apartment, suite, floor, etc. (optional).",
    )

    city = models.CharField(
        verbose_name="City",
        max_length=100,
        db_index=True,
        help_text="City name (e.g., Dhaka, Chittagong).",
    )

    area = models.CharField(
        verbose_name="Area",
        max_length=100,
        db_index=True,
        help_text="Area/district within city (e.g., Gulshan, Dhanmondi).",
    )

    postal_code = models.CharField(
        verbose_name="Postal Code",
        max_length=10,
        blank=True,
        help_text="Postal/ZIP code (optional).",
    )

    is_default = models.BooleanField(
        verbose_name="Is Default",
        default=False,
        db_index=True,
        help_text="Use this as default shipping address.",
    )

    class Meta:
        verbose_name = "Customer Address"
        verbose_name_plural = "Customer Addresses"
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["city", "area"]),
        ]

    def __str__(self) -> str:
        """
        String representation of the address.

        Returns:
            Label and city, or just city if no label.
        """
        if self.label:
            return f"{self.label} - {self.city}"
        return f"{self.city}, {self.area}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save the address.

        If this address is being set as default, unset any other
        default addresses for the same user.
        """
        if self.is_default:
            # Unset other default addresses for this user
            CustomerAddress.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)

        super().save(*args, **kwargs)

    @property
    def full_address(self) -> str:
        """
        Get complete formatted address.

        Returns:
            Formatted multi-line address string.
        """
        lines = [
            self.recipient_name,
            self.address_line1,
        ]

        if self.address_line2:
            lines.append(self.address_line2)

        lines.append(f"{self.area}, {self.city}")

        if self.postal_code:
            lines.append(self.postal_code)

        lines.append(f"Phone: {self.phone}")

        return "\n".join(lines)

    @property
    def short_address(self) -> str:
        """
        Get short one-line address.

        Returns:
            Compact address string for display in lists.
        """
        parts = [self.area, self.city]
        if self.label:
            parts.insert(0, self.label)
        return ", ".join(parts)

    def set_as_default(self) -> None:
        """
        Set this address as the default for the user.

        Automatically unsets any other default addresses.

        Example:
            address.set_as_default()
        """
        if not self.is_default:
            self.is_default = True
            self.save()
