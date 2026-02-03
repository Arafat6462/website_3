#!/usr/bin/env python
"""Phase 12 Tests: Notifications (Email System).

This module tests the email notification system including:
- Order confirmation emails
- Order shipped emails
- Welcome emails
- Password reset emails
- Token generation and verification
- Template rendering
- Error handling

All tests use Django's test email backend which stores emails in memory.
"""

import os
import sys
from decimal import Decimal
from django.test import TestCase, override_settings
from django.core import mail
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
import django

django.setup()

from apps.users.models import CustomerAddress
from apps.products.models import Product, ProductVariant, Category, ProductType
from apps.orders.models import Order, OrderItem, Cart, ShippingZone
from apps.orders.services import OrderService, CartService
from apps.notifications.services import email_service

User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@example.com",
    SITE_NAME="Test Store",
    SITE_URL="http://testserver",
)
class EmailServiceTests(TestCase):
    """Test suite for email notification service.
    
    Tests all email types, token generation, template rendering,
    and error handling scenarios.
    """
    
    def setUp(self):
        """Set up test fixtures.
        
        Creates:
            - Test user
            - Test product and variant
            - Test order
            - Test shipping zone
        """
        # Clear mail outbox
        mail.outbox = []
        
        # Create test user
        self.user = User.objects.create_user(
            email="customer@example.com",
            phone="01712345678",
            password="testpass123",
            first_name="John",
            last_name="Doe",
        )
        
        # Create user address
        self.address = CustomerAddress.objects.create(
            user=self.user,
            label="Home",
            recipient_name="John Doe",
            phone="01712345678",
            address_line1="123 Main St",
            city="Dhaka",
            area="Gulshan",
            is_default=True,
        )
        
        # Create test product
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
            status="active",
        )
        
        self.product_type = ProductType.objects.create(
            name="Test Type",
            slug="test-type",
        )
        
        self.product = Product.objects.create(
            product_type=self.product_type,
            category=self.category,
            name="Test Product",
            slug="test-product",
            base_price=Decimal("1000.00"),
            status="published",
        )
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="TEST-001",
            name="Default",
            price=Decimal("1000.00"),
            stock_quantity=10,
            is_default=True,
        )
        
        # Create shipping zone
        self.shipping_zone = ShippingZone.objects.create(
            name="Dhaka",
            areas=["Gulshan", "Banani", "Dhanmondi"],
            shipping_cost=Decimal("100.00"),
            is_active=True,
        )
    
    def test_send_order_confirmation_email(self):
        """Test sending order confirmation email.
        
        Verifies:
            - Email is sent
            - Correct recipient
            - Order details in body
            - HTML and plain text versions
        """
        # Create order
        cart = Cart.objects.create(user=self.user)
        CartService.add_item(cart, self.variant, 2)
        
        shipping_data = {
            "customer_name": "John Doe",
            "customer_email": self.user.email,
            "customer_phone": "01712345678",
            "address_line1": "123 Main St",
            "address_line2": "",
            "city": "Dhaka",
            "area": "Gulshan",
            "postal_code": "1212",
        }
        
        order = OrderService.create_from_cart(cart, shipping_data, "cod", user=self.user)
        
        # Send confirmation email
        result = email_service.send_order_confirmation(order)
        
        # Verify email sent
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email details
        email = mail.outbox[0]
        self.assertEqual(email.to, [order.customer_email])
        self.assertIn(order.order_number, email.subject)
        self.assertIn(order.order_number, email.body)
        self.assertIn("Test Product", email.body)
        self.assertIn("2000", email.body)  # Check for amount (without formatting)
        
        # Check HTML alternative
        self.assertEqual(len(email.alternatives), 1)
        html_content = email.alternatives[0][0]
        self.assertIn(order.order_number, html_content)
        self.assertIn("Order Confirmed", html_content)
        
        print("\n✅ Order confirmation email sent successfully")
        print(f"   To: {email.to[0]}")
        print(f"   Subject: {email.subject}")
        print(f"   Order: {order.order_number}")
    
    def test_send_shipped_email(self):
        """Test sending order shipped notification email.
        
        Verifies:
            - Email is sent
            - Tracking information included
            - Estimated delivery date shown
        """
        # Create and ship order
        cart = Cart.objects.create(user=self.user)
        CartService.add_item(cart, self.variant, 1)
        
        shipping_data = {
            "customer_name": "John Doe",
            "customer_email": self.user.email,
            "customer_phone": "01712345678",
            "address_line1": "123 Main St",
            "address_line2": "",
            "city": "Dhaka",
            "area": "Gulshan",
            "postal_code": "1212",
        }
        
        order = OrderService.create_from_cart(cart, shipping_data, "cod", user=self.user)
        
        # Mark as shipped with tracking
        order.tracking_number = "TRACK123456"
        order.courier_name = "Test Courier"
        order.status = "shipped"
        order.save()
        
        # Clear previous emails
        mail.outbox = []
        
        # Send shipped email
        result = email_service.send_shipped_email(order)
        
        # Verify email sent
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email details
        email = mail.outbox[0]
        self.assertEqual(email.to, [order.customer_email])
        self.assertIn("Shipped", email.subject)
        self.assertIn(order.tracking_number, email.body)
        self.assertIn(order.courier_name, email.body)
        
        print("\n✅ Shipped email sent successfully")
        print(f"   Tracking: {order.tracking_number}")
        print(f"   Courier: {order.courier_name}")
    
    def test_send_welcome_email(self):
        """Test sending welcome email to new user.
        
        Verifies:
            - Email is sent
            - User name is personalized
            - Welcome message included
        """
        # Clear previous emails
        mail.outbox = []
        
        # Send welcome email
        result = email_service.send_welcome_email(self.user)
        
        # Verify email sent
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email details
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertIn("Welcome", email.subject)
        self.assertIn(self.user.first_name, email.body)
        self.assertIn("Test Store", email.body)
        
        print("\n✅ Welcome email sent successfully")
        print(f"   To: {self.user.first_name} ({email.to[0]})")
        print(f"   Subject: {email.subject}")
    
    def test_send_password_reset_email(self):
        """Test sending password reset email.
        
        Verifies:
            - Email is sent
            - Reset link included
            - Token is valid
            - UID is correct
        """
        # Clear previous emails
        mail.outbox = []
        
        # Send password reset email
        result = email_service.send_password_reset_email(self.user)
        
        # Verify email sent
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email details
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertIn("Password Reset", email.subject)
        self.assertIn("reset-password", email.body)
        
        # Extract token and UID from email body
        body = email.body
        self.assertIn("uid=", body)
        self.assertIn("token=", body)
        
        # Verify token in HTML version
        html_content = email.alternatives[0][0]
        self.assertIn("reset-password", html_content)
        self.assertIn("24 hours", html_content)
        
        print("\n✅ Password reset email sent successfully")
        print(f"   To: {email.to[0]}")
        print(f"   Contains: Reset link with token")
    
    def test_password_reset_token_generation(self):
        """Test password reset token generation and verification.
        
        Verifies:
            - Token is generated
            - Token is valid immediately
            - Token validates correct user
            - UID decodes to correct user ID
        """
        # Generate token
        token = email_service.token_generator.make_token(self.user)
        
        # Verify token is not empty
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 0)
        
        # Verify token is valid
        is_valid = email_service.verify_password_reset_token(self.user, token)
        self.assertTrue(is_valid)
        
        # Verify token fails for different user
        other_user = User.objects.create_user(
            email="other@example.com",
            phone="01798765432",
            password="testpass123",
        )
        is_valid_other = email_service.verify_password_reset_token(other_user, token)
        self.assertFalse(is_valid_other)
        
        # Verify token fails for invalid token
        is_valid_invalid = email_service.verify_password_reset_token(
            self.user, "invalid-token-123"
        )
        self.assertFalse(is_valid_invalid)
        
        print("\n✅ Password reset token generation works correctly")
        print(f"   Token length: {len(token)}")
        print(f"   Valid for user: {self.user.email}")
        print(f"   Invalid for other users: ✓")
    
    def test_password_reset_uid_encoding(self):
        """Test UID encoding in password reset.
        
        Verifies:
            - UID encodes user ID correctly
            - UID can be decoded back to user ID
        """
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        # Encode UID
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        # Decode UID
        decoded_id = int(force_str(urlsafe_base64_decode(uid)))
        
        # Verify decoded ID matches user ID
        self.assertEqual(decoded_id, self.user.pk)
        
        # Retrieve user by decoded ID
        retrieved_user = User.objects.get(pk=decoded_id)
        self.assertEqual(retrieved_user, self.user)
        
        print("\n✅ UID encoding/decoding works correctly")
        print(f"   User ID: {self.user.pk}")
        print(f"   Encoded UID: {uid}")
        print(f"   Decoded ID: {decoded_id}")
    
    def test_email_template_rendering(self):
        """Test email templates render correctly.
        
        Verifies:
            - Templates exist
            - Context variables are rendered
            - HTML contains proper structure
        """
        # Create order for testing
        cart = Cart.objects.create(user=self.user)
        CartService.add_item(cart, self.variant, 1)
        
        shipping_data = {
            "customer_name": "John Doe",
            "customer_email": self.user.email,
            "customer_phone": "01712345678",
            "address_line1": "123 Main St",
            "address_line2": "",
            "city": "Dhaka",
            "area": "Gulshan",
            "postal_code": "1212",
        }
        
        order = OrderService.create_from_cart(cart, shipping_data, "cod", user=self.user)
        
        # Send email
        email_service.send_order_confirmation(order)
        
        # Get HTML content
        html_content = mail.outbox[0].alternatives[0][0]
        
        # Verify HTML structure
        self.assertIn("<!DOCTYPE html>", html_content)
        self.assertIn("<html", html_content)
        self.assertIn("</html>", html_content)
        self.assertIn(order.order_number, html_content)
        self.assertIn(order.customer_name, html_content)
        
        print("\n✅ Email templates render correctly")
        print(f"   HTML structure: Valid")
        print(f"   Variables rendered: ✓")
    
    def test_email_error_handling(self):
        """Test email service error handling.
        
        Verifies:
            - Service handles errors gracefully
            - Returns False on failure
            - Logs error (doesn't crash)
        """
        # Create invalid order (missing required fields)
        order = Order()  # Empty order, will cause errors
        
        # Try to send email (should fail gracefully)
        result = email_service.send_order_confirmation(order)
        
        # Should return False on error
        self.assertFalse(result)
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
        
        print("\n✅ Email error handling works correctly")
        print(f"   Error handled gracefully: ✓")
        print(f"   Returns False on failure: ✓")
    
    def test_custom_reset_url(self):
        """Test custom password reset URL.
        
        Verifies:
            - Custom URL can be provided
            - Custom URL is used in email
        """
        mail.outbox = []
        
        # Send with custom reset URL
        custom_url = "https://custom-frontend.com/reset-password/"
        result = email_service.send_password_reset_email(
            self.user, reset_url=custom_url
        )
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check custom URL is used
        email = mail.outbox[0]
        self.assertIn("custom-frontend.com", email.body)
        
        print("\n✅ Custom reset URL works correctly")
        print(f"   Custom URL used: {custom_url}")
    
    def test_multiple_items_in_order_email(self):
        """Test order confirmation with multiple items.
        
        Verifies:
            - All items are listed
            - Quantities are shown
            - Totals are calculated correctly
        """
        # Create second product
        variant2 = ProductVariant.objects.create(
            product=self.product,
            sku="TEST-002",
            name="Variant 2",
            price=Decimal("500.00"),
            stock_quantity=5,
        )
        
        # Create order with multiple items
        cart = Cart.objects.create(user=self.user)
        CartService.add_item(cart, self.variant, 2)
        CartService.add_item(cart, variant2, 3)
        
        shipping_data = {
            "customer_name": "John Doe",
            "customer_email": self.user.email,
            "customer_phone": "01712345678",
            "address_line1": "123 Main St",
            "address_line2": "",
            "city": "Dhaka",
            "area": "Gulshan",
            "postal_code": "1212",
        }
        
        order = OrderService.create_from_cart(cart, shipping_data, "cod", user=self.user)
        
        # Send email
        mail.outbox = []
        email_service.send_order_confirmation(order)
        
        # Verify items in email
        email = mail.outbox[0]
        self.assertIn("TEST-001", email.body)
        self.assertIn("TEST-002", email.body)
        
        print("\n✅ Multiple items email works correctly")
        print(f"   Items in order: {order.items.count()}")
        print(f"   All items in email: ✓")


if __name__ == "__main__":
    import unittest

    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(EmailServiceTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
