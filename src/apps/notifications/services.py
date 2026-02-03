"""Email service for sending transactional emails.

This module provides synchronous email sending capabilities for the e-commerce platform.
All emails are sent immediately (no async/Celery yet for simplicity).

Supported email types:
    - Order confirmation
    - Order shipped notification
    - Welcome email
    - Password reset

Environment Variables Required:
    - EMAIL_HOST: SMTP server hostname
    - EMAIL_PORT: SMTP port (587 for TLS)
    - EMAIL_HOST_USER: SMTP username
    - EMAIL_HOST_PASSWORD: SMTP password
    - EMAIL_USE_TLS: Whether to use TLS (True/False)
    - DEFAULT_FROM_EMAIL: Sender email address
"""

import logging
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails.
    
    This service handles all email communications with customers and users.
    Emails are sent synchronously for simplicity.
    
    All methods follow the same pattern:
        1. Prepare email context
        2. Render HTML template
        3. Generate plain text version
        4. Send email
        5. Log result
    
    Attributes:
        from_email (str): Default sender email address
        token_generator (PasswordResetTokenGenerator): Token generator for password resets
    """
    
    def __init__(self):
        """Initialize email service with default settings."""
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.token_generator = PasswordResetTokenGenerator()
    
    def send_order_confirmation(self, order) -> bool:
        """Send order confirmation email to customer.
        
        Sent immediately after order is created. Contains order details,
        items purchased, total amount, and shipping information.
        
        Args:
            order: Order instance with all related data
        
        Returns:
            bool: True if email sent successfully, False otherwise
        
        Raises:
            Exception: If email backend fails (logged, not raised)
        """
        try:
            # Prepare email context
            context = {
                'order': order,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'items': order.items.select_related('variant__product'),
                'subtotal': order.subtotal,
                'shipping_cost': order.shipping_cost,
                'tax_amount': order.tax_amount,
                'discount_amount': order.discount_amount,
                'total': order.total,
                'shipping_address': {
                    'line1': order.shipping_address_line1,
                    'line2': order.shipping_address_line2,
                    'city': order.shipping_city,
                    'area': order.shipping_area,
                    'postal_code': order.shipping_postal_code,
                },
                'payment_method': order.get_payment_method_display(),
                'site_name': getattr(settings, 'SITE_NAME', 'Our Store'),
                'site_url': getattr(settings, 'SITE_URL', 'https://example.com'),
            }
            
            # Render HTML email
            html_message = render_to_string(
                'emails/order_confirmation.html',
                context
            )
            
            # Generate plain text version
            plain_message = strip_tags(html_message)
            
            # Send email
            subject = f'Order Confirmation - {order.order_number}'
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=self.from_email,
                to=[order.customer_email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            logger.info(
                f"Order confirmation email sent successfully: "
                f"order={order.order_number}, email={order.customer_email}"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send order confirmation email: "
                f"order={order.order_number}, error={str(e)}"
            )
            return False
    
    def send_shipped_email(self, order) -> bool:
        """Send shipping notification email to customer.
        
        Sent when order status changes to 'shipped'. Contains tracking
        information and estimated delivery date.
        
        Args:
            order: Order instance with tracking information
        
        Returns:
            bool: True if email sent successfully, False otherwise
        
        Raises:
            Exception: If email backend fails (logged, not raised)
        """
        try:
            # Prepare email context
            context = {
                'order': order,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'tracking_number': order.tracking_number,
                'courier_name': order.courier_name,
                'estimated_delivery': order.estimated_delivery,
                'items': order.items.select_related('variant__product'),
                'site_name': getattr(settings, 'SITE_NAME', 'Our Store'),
                'site_url': getattr(settings, 'SITE_URL', 'https://example.com'),
            }
            
            # Render HTML email
            html_message = render_to_string(
                'emails/order_shipped.html',
                context
            )
            
            # Generate plain text version
            plain_message = strip_tags(html_message)
            
            # Send email
            subject = f'Your Order Has Shipped - {order.order_number}'
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=self.from_email,
                to=[order.customer_email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            logger.info(
                f"Shipped email sent successfully: "
                f"order={order.order_number}, email={order.customer_email}"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send shipped email: "
                f"order={order.order_number}, error={str(e)}"
            )
            return False
    
    def send_welcome_email(self, user) -> bool:
        """Send welcome email to newly registered user.
        
        Sent immediately after user account creation. Contains welcome
        message and basic account information.
        
        Args:
            user: User instance (newly created)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        
        Raises:
            Exception: If email backend fails (logged, not raised)
        """
        try:
            # Prepare email context
            context = {
                'user': user,
                'first_name': user.first_name or 'Customer',
                'email': user.email,
                'site_name': getattr(settings, 'SITE_NAME', 'Our Store'),
                'site_url': getattr(settings, 'SITE_URL', 'https://example.com'),
                'login_url': f"{getattr(settings, 'SITE_URL', 'https://example.com')}/login/",
            }
            
            # Render HTML email
            html_message = render_to_string(
                'emails/welcome.html',
                context
            )
            
            # Generate plain text version
            plain_message = strip_tags(html_message)
            
            # Send email
            subject = f'Welcome to {getattr(settings, "SITE_NAME", "Our Store")}!'
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=self.from_email,
                to=[user.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            logger.info(
                f"Welcome email sent successfully: "
                f"user={user.email}"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send welcome email: "
                f"user={user.email}, error={str(e)}"
            )
            return False
    
    def send_password_reset_email(self, user, reset_url: Optional[str] = None) -> bool:
        """Send password reset email with secure token.
        
        Generates a secure one-time token valid for 24 hours. The token
        is included in the reset URL sent to the user.
        
        Token Flow:
            1. Generate token using Django's PasswordResetTokenGenerator
            2. Encode user ID as base64
            3. Build reset URL with uid and token
            4. Send email with URL
            5. Frontend receives token → calls API with new password
        
        Args:
            user: User instance requesting password reset
            reset_url: Optional custom reset URL (default: site_url/reset-password/)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        
        Raises:
            Exception: If email backend fails (logged, not raised)
        """
        try:
            # Generate secure token (valid for 24 hours)
            token = self.token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            if reset_url is None:
                site_url = getattr(settings, 'SITE_URL', 'https://example.com')
                reset_url = f"{site_url}/reset-password/"
            
            reset_link = f"{reset_url}?uid={uid}&token={token}"
            
            # Prepare email context
            context = {
                'user': user,
                'first_name': user.first_name or 'Customer',
                'reset_link': reset_link,
                'token_validity_hours': 24,
                'site_name': getattr(settings, 'SITE_NAME', 'Our Store'),
                'site_url': getattr(settings, 'SITE_URL', 'https://example.com'),
            }
            
            # Render HTML email
            html_message = render_to_string(
                'emails/password_reset.html',
                context
            )
            
            # Generate plain text version
            plain_message = strip_tags(html_message)
            
            # Send email
            subject = 'Password Reset Request'
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=self.from_email,
                to=[user.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            logger.info(
                f"Password reset email sent successfully: "
                f"user={user.email}, uid={uid}"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send password reset email: "
                f"user={user.email}, error={str(e)}"
            )
            return False
    
    def verify_password_reset_token(self, user, token: str) -> bool:
        """Verify password reset token is valid.
        
        Tokens are valid for 24 hours from generation. Django's
        PasswordResetTokenGenerator handles expiry automatically.
        
        Args:
            user: User instance
            token: Token string to verify
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        return self.token_generator.check_token(user, token)


# Singleton instance
email_service = EmailService()
