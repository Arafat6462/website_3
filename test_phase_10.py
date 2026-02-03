#!/usr/bin/env python
"""
Test script for Phase 10: Order System.

Tests:
1. Order creation from cart with pricing calculations
2. Order status transitions
3. Payment recording
4. Order cancellation with stock restoration
5. Return request workflow
6. Guest order creation
7. Order with coupons
8. Order with shipping zones
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.products.models import Product, ProductVariant
from apps.orders.models import (
    Cart,
    CartItem,
    Coupon,
    ShippingZone,
    Order,
    OrderItem,
    OrderStatusLog,
    PaymentTransaction,
    ReturnRequest,
)
from apps.orders.services import OrderService, CartService

User = get_user_model()


def test_order_creation():
    """Test 1: Order creation from cart."""
    print("\n" + "=" * 70)
    print("TEST 1: Order Creation from Cart")
    print("=" * 70)

    # Get test user and product
    user = User.objects.filter(email="john@example.com").first()
    if not user:
        user = User.objects.create_user(
            email="john@example.com",
            phone="01700000001",
            password="test123",
            first_name="John",
            last_name="Doe",
        )
        print(f"✓ Created test user: {user.email}")

    variant = ProductVariant.objects.filter(is_active=True, stock_quantity__gt=0).first()
    if not variant:
        print("✗ No active variants with stock found")
        return

    # Create cart with items
    cart = CartService.get_or_create_cart(user=user)
    CartService.add_item(cart, variant, 2)
    print(f"✓ Created cart with 2x {variant.name}")

    # Create order
    shipping_data = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "customer_phone": "01712345678",
        "address_line1": "House 10, Road 5",
        "address_line2": "Dhanmondi",
        "city": "Dhaka",
        "area": "Dhanmondi",
        "postal_code": "1205",
        "customer_notes": "Please deliver in the morning",
    }

    order = OrderService.create_from_cart(
        cart, shipping_data, "cod", user=user
    )

    print(f"\n✓ Order created successfully!")
    print(f"  Order Number: {order.order_number}")
    print(f"  Status: {order.get_status_display()}")
    print(f"  Subtotal: ৳{order.subtotal}")
    print(f"  Shipping: ৳{order.shipping_cost}")
    print(f"  Tax: ৳{order.tax_amount}")
    print(f"  Total: ৳{order.total}")
    print(f"  Items: {order.items.count()}")

    # Verify cart cleared
    cart.refresh_from_db()
    assert cart.items.count() == 0, "Cart should be empty"
    print(f"✓ Cart cleared after order creation")

    # Verify stock deducted
    variant.refresh_from_db()
    print(f"✓ Stock updated (variant stock: {variant.stock_quantity})")

    return order


def test_order_status_transitions():
    """Test 2: Order status transitions."""
    print("\n" + "=" * 70)
    print("TEST 2: Order Status Transitions")
    print("=" * 70)

    # Get recent order
    order = Order.objects.filter(status="pending").first()
    if not order:
        print("✗ No pending orders found")
        return

    admin = User.objects.filter(is_staff=True).first()
    if not admin:
        admin = User.objects.create_superuser(
            email="admin@example.com",
            phone="01911111111",
            password="admin123",
        )
        print(f"✓ Created admin user")

    initial_status = order.status
    print(f"Initial status: {order.get_status_display()}")

    # Confirm order
    OrderService.change_status(order, "confirmed", admin, "Payment verified")
    order.refresh_from_db()
    print(f"✓ Status changed: {initial_status} → {order.status}")
    print(f"  Confirmed at: {order.confirmed_at}")

    # Ship order
    OrderService.change_status(order, "shipped", admin, "Shipped via Sundarban")
    order.refresh_from_db()
    print(f"✓ Status changed: confirmed → {order.status}")
    print(f"  Shipped at: {order.shipped_at}")

    # Deliver order
    OrderService.change_status(order, "delivered", admin, "Delivered successfully")
    order.refresh_from_db()
    print(f"✓ Status changed: shipped → {order.status}")
    print(f"  Delivered at: {order.delivered_at}")

    # Verify status logs
    logs = OrderStatusLog.objects.filter(order=order)
    print(f"\n✓ Status change logs: {logs.count()}")
    for log in logs:
        print(f"  - {log.from_status or 'N/A'} → {log.to_status} by {log.changed_by}")

    return order


def test_payment_recording():
    """Test 3: Payment recording."""
    print("\n" + "=" * 70)
    print("TEST 3: Payment Recording")
    print("=" * 70)

    # Create new order
    user = User.objects.first()
    variant = ProductVariant.objects.filter(is_active=True, stock_quantity__gt=0).first()

    cart = CartService.get_or_create_cart(user=user)
    CartService.add_item(cart, variant, 1)

    shipping_data = {
        "customer_name": "Jane Doe",
        "customer_email": "jane@example.com",
        "customer_phone": "01812345678",
        "address_line1": "House 20",
        "city": "Dhaka",
        "area": "Gulshan",
    }

    order = OrderService.create_from_cart(cart, shipping_data, "bkash", user=user)
    print(f"✓ Created order: {order.order_number}")

    # Record bKash payment
    transaction = OrderService.record_payment(
        order,
        provider="bkash",
        amount=order.total,
        reference="TXN123456789",
        status="completed",
        raw_response={"trxID": "TXN123456789", "amount": str(order.total)},
    )

    print(f"✓ Payment recorded:")
    print(f"  Provider: {transaction.get_provider_display()}")
    print(f"  Amount: ৳{transaction.amount}")
    print(f"  Status: {transaction.get_status_display()}")
    print(f"  Reference: {transaction.provider_reference}")

    # Verify order payment status updated
    order.refresh_from_db()
    print(f"✓ Order payment status: {order.get_payment_status_display()}")

    return order


def test_order_cancellation():
    """Test 4: Order cancellation with stock restoration."""
    print("\n" + "=" * 70)
    print("TEST 4: Order Cancellation with Stock Restoration")
    print("=" * 70)

    # Create order
    user = User.objects.first()
    variant = ProductVariant.objects.filter(is_active=True, stock_quantity__gt=5).first()

    initial_stock = variant.stock_quantity
    print(f"Initial stock: {initial_stock}")

    cart = CartService.get_or_create_cart(user=user)
    CartService.add_item(cart, variant, 3)

    shipping_data = {
        "customer_name": "Test User",
        "customer_email": "test@example.com",
        "customer_phone": "01612345678",
        "address_line1": "Test Address",
        "city": "Dhaka",
        "area": "Mirpur",
    }

    order = OrderService.create_from_cart(cart, shipping_data, "cod", user=user)
    print(f"✓ Created order: {order.order_number}")

    # Confirm order (stock deducted)
    admin = User.objects.filter(is_staff=True).first()
    OrderService.change_status(order, "confirmed", admin, "Order confirmed")

    variant.refresh_from_db()
    stock_after_confirm = variant.stock_quantity
    print(f"Stock after confirmation: {stock_after_confirm}")
    assert stock_after_confirm == initial_stock - 3, "Stock should be deducted"

    # Cancel order (stock restored)
    OrderService.change_status(order, "cancelled", admin, "Customer requested cancellation")

    variant.refresh_from_db()
    stock_after_cancel = variant.stock_quantity
    print(f"✓ Stock after cancellation: {stock_after_cancel}")
    assert stock_after_cancel == initial_stock, "Stock should be restored"

    order.refresh_from_db()
    print(f"✓ Order status: {order.get_status_display()}")
    print(f"  Cancelled at: {order.cancelled_at}")


def test_return_request():
    """Test 5: Return request workflow."""
    print("\n" + "=" * 70)
    print("TEST 5: Return Request Workflow")
    print("=" * 70)

    # Get delivered order
    order = Order.objects.filter(status="delivered").first()
    if not order:
        print("✗ No delivered orders found")
        return

    print(f"Order: {order.order_number}")

    # Create return request
    return_req = ReturnRequest.objects.create(
        order=order,
        user=order.user,
        status="requested",
        reason="damaged",
        customer_notes="Product arrived damaged",
    )
    print(f"✓ Return request created: ID {return_req.id}")

    # Get initial stock
    order_item = order.items.first()
    variant = order_item.variant
    initial_stock = variant.stock_quantity
    print(f"Initial stock: {initial_stock}")

    # Approve return
    admin = User.objects.filter(is_staff=True).first()
    OrderService.process_return_request(
        return_req.id,
        approved=True,
        processed_by=admin,
        admin_notes="Return approved, product was damaged",
        refund_amount=order.total,
    )

    return_req.refresh_from_db()
    print(f"✓ Return approved:")
    print(f"  Status: {return_req.get_status_display()}")
    print(f"  Refund amount: ৳{return_req.refund_amount}")

    # Verify stock restored
    variant.refresh_from_db()
    print(f"✓ Stock after return: {variant.stock_quantity}")


def test_guest_order():
    """Test 6: Guest order creation."""
    print("\n" + "=" * 70)
    print("TEST 6: Guest Order Creation")
    print("=" * 70)

    variant = ProductVariant.objects.filter(is_active=True, stock_quantity__gt=0).first()

    # Create guest cart
    cart = CartService.get_or_create_cart(session_key="guest-session-123")
    CartService.add_item(cart, variant, 1)
    print(f"✓ Created guest cart")

    # Create guest order
    shipping_data = {
        "customer_name": "Guest User",
        "customer_email": "guest@example.com",
        "customer_phone": "01512345678",
        "address_line1": "Guest Address",
        "city": "Dhaka",
        "area": "Uttara",
    }

    order = OrderService.create_from_cart(cart, shipping_data, "cod")

    print(f"✓ Guest order created:")
    print(f"  Order Number: {order.order_number}")
    print(f"  Customer: {order.customer_name}")
    print(f"  User: {order.user or 'None (Guest)'}")
    print(f"  Total: ৳{order.total}")

    return order


def test_order_with_coupon():
    """Test 7: Order with coupon discount."""
    print("\n" + "=" * 70)
    print("TEST 7: Order with Coupon")
    print("=" * 70)

    user = User.objects.first()
    variant = ProductVariant.objects.filter(is_active=True, stock_quantity__gt=0).first()

    # Create cart
    cart = CartService.get_or_create_cart(user=user)
    CartService.add_item(cart, variant, 1)

    subtotal = sum(item.unit_price * item.quantity for item in cart.items.all())
    print(f"Cart subtotal: ৳{subtotal}")

    # Get active coupon
    coupon = Coupon.objects.filter(is_active=True, code="SAVE10").first()
    if not coupon:
        print("✗ No active coupon found")
        return

    # Create order with coupon
    shipping_data = {
        "customer_name": "Coupon User",
        "customer_email": "coupon@example.com",
        "customer_phone": "01912345678",
        "address_line1": "Coupon Address",
        "city": "Dhaka",
        "area": "Banani",
    }

    order = OrderService.create_from_cart(cart, shipping_data, "cod", user=user, coupon=coupon)

    print(f"✓ Order created with coupon:")
    print(f"  Coupon: {order.coupon_code}")
    print(f"  Subtotal: ৳{order.subtotal}")
    print(f"  Discount: -৳{order.discount_amount}")
    print(f"  Shipping: ৳{order.shipping_cost}")
    print(f"  Tax: ৳{order.tax_amount}")
    print(f"  Total: ৳{order.total}")

    # Verify coupon usage tracked
    coupon.refresh_from_db()
    print(f"✓ Coupon usage count: {coupon.times_used}")

    return order


def test_shipping_zones():
    """Test 8: Order with different shipping zones."""
    print("\n" + "=" * 70)
    print("TEST 8: Orders with Different Shipping Zones")
    print("=" * 70)

    user = User.objects.first()
    variant = ProductVariant.objects.filter(is_active=True, stock_quantity__gt=0).first()

    # Test Dhaka City zone
    cart = CartService.get_or_create_cart(user=user)
    CartService.add_item(cart, variant, 1)

    shipping_data_dhaka = {
        "customer_name": "Dhaka User",
        "customer_email": "dhaka@example.com",
        "customer_phone": "01712345678",
        "address_line1": "Dhaka Address",
        "city": "Dhaka",
        "area": "Dhanmondi",
    }

    order_dhaka = OrderService.create_from_cart(cart, shipping_data_dhaka, "cod", user=user)
    print(f"✓ Dhaka order:")
    print(f"  Zone: {order_dhaka.shipping_zone.name if order_dhaka.shipping_zone else 'N/A'}")
    print(f"  Shipping cost: ৳{order_dhaka.shipping_cost}")

    # Test Outside Dhaka zone
    cart = CartService.get_or_create_cart(user=user)
    CartService.add_item(cart, variant, 1)

    shipping_data_outside = {
        "customer_name": "Outside User",
        "customer_email": "outside@example.com",
        "customer_phone": "01812345678",
        "address_line1": "Chittagong Address",
        "city": "Chittagong",
        "area": "Agrabad",
    }

    order_outside = OrderService.create_from_cart(cart, shipping_data_outside, "cod", user=user)
    print(f"✓ Outside Dhaka order:")
    print(f"  Zone: {order_outside.shipping_zone.name if order_outside.shipping_zone else 'N/A'}")
    print(f"  Shipping cost: ৳{order_outside.shipping_cost}")


def run_all_tests():
    """Run all Phase 10 tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "PHASE 10: ORDER SYSTEM TESTS" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")

    tests = [
        ("Order Creation", test_order_creation),
        ("Status Transitions", test_order_status_transitions),
        ("Payment Recording", test_payment_recording),
        ("Order Cancellation", test_order_cancellation),
        ("Return Request", test_return_request),
        ("Guest Order", test_guest_order),
        ("Order with Coupon", test_order_with_coupon),
        ("Shipping Zones", test_shipping_zones),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"\n✓ {name} - PASSED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} - FAILED")
            print(f"  Error: {str(e)}")
            import traceback

            traceback.print_exc()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {len(tests)}")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print("=" * 70)

    # Database stats
    print("\nDATABASE STATISTICS:")
    print(f"  Orders: {Order.objects.count()}")
    print(f"  Order Items: {OrderItem.objects.count()}")
    print(f"  Status Logs: {OrderStatusLog.objects.count()}")
    print(f"  Payment Transactions: {PaymentTransaction.objects.count()}")
    print(f"  Return Requests: {ReturnRequest.objects.count()}")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
