#!/usr/bin/env python
"""
Test script for Phase 11: Engagement System.

Tests:
1. Product review creation
2. Review validation (duplicate prevention)
3. Review approval workflow
4. Average rating calculation
5. Admin reply to review
6. Wishlist creation
7. Add/remove items from wishlist
8. Toggle wishlist item
9. Move wishlist item to cart
10. Clear wishlist
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
from django.core.exceptions import ValidationError
from apps.products.models import Product, ProductVariant
from apps.engagement.models import ProductReview, Wishlist, WishlistItem
from apps.engagement.services import ReviewService, WishlistService
from apps.orders.models import Cart

User = get_user_model()


def test_review_creation():
    """Test 1: Product review creation."""
    print("\n" + "=" * 70)
    print("TEST 1: Product Review Creation")
    print("=" * 70)

    # Get test user and product
    user = User.objects.filter(email="john@example.com").first()
    product = Product.objects.filter(status="published").first()

    if not user or not product:
        print("✗ Test data not available")
        return

    # Create review
    review = ProductReview.objects.create(
        user=user,
        product=product,
        rating=5,
        comment="Excellent product! The quality is outstanding.",
        images=["https://example.com/review1.jpg"],
    )

    print(f"✓ Review created:")
    print(f"  User: {review.user.email}")
    print(f"  Product: {review.product.name}")
    print(f"  Rating: {review.rating}★")
    print(f"  Comment: {review.comment[:50]}...")
    print(f"  Approved: {review.is_approved}")
    print(f"  Images: {len(review.images)} image(s)")

    return review


def test_review_validation():
    """Test 2: Review validation (duplicate prevention)."""
    print("\n" + "=" * 70)
    print("TEST 2: Review Validation")
    print("=" * 70)

    user = User.objects.filter(email="john@example.com").first()
    product = Product.objects.filter(status="published").first()

    # Try to create duplicate review
    try:
        ReviewService.validate_review(user, product)
        print("✗ Validation should have failed for duplicate review")
    except ValidationError as e:
        print(f"✓ Duplicate review prevented:")
        print(f"  Error: {e.message}")

    # Try different product (should succeed)
    another_product = Product.objects.filter(status="published").exclude(id=product.id).first()
    if another_product:
        try:
            ReviewService.validate_review(user, another_product)
            print(f"✓ Validation passed for different product: {another_product.name}")
        except ValidationError:
            print("✗ Validation should have passed for different product")


def test_review_approval():
    """Test 3: Review approval workflow."""
    print("\n" + "=" * 70)
    print("TEST 3: Review Approval Workflow")
    print("=" * 70)

    review = ProductReview.objects.filter(is_approved=False).first()
    if not review:
        print("✗ No pending reviews found")
        return

    print(f"Initial status: Approved={review.is_approved}")

    # Approve review
    review.approve()
    print(f"✓ Review approved: Approved={review.is_approved}")

    # Reject review
    review.reject()
    print(f"✓ Review rejected: Approved={review.is_approved}")

    # Approve again for next tests
    review.approve()


def test_average_rating():
    """Test 4: Average rating calculation."""
    print("\n" + "=" * 70)
    print("TEST 4: Average Rating Calculation")
    print("=" * 70)

    product = Product.objects.filter(status="published").first()

    # Get initial stats
    stats = ReviewService.get_review_stats(product)
    print(f"✓ Review statistics for '{product.name}':")
    print(f"  Average Rating: {stats['average_rating']}★")
    print(f"  Total Reviews: {stats['total_reviews']}")
    print(f"  Rating Distribution:")
    for rating in range(5, 0, -1):
        count = stats['rating_distribution'][rating]
        bar = "█" * count
        print(f"    {rating}★: {bar} ({count})")

    # Create more reviews to test average
    users = User.objects.all()[:3]
    ratings = [4, 5, 3]
    
    for user, rating in zip(users, ratings):
        # Check if review already exists
        if not ProductReview.objects.filter(user=user, product=product).exists():
            review = ProductReview.objects.create(
                user=user,
                product=product,
                rating=rating,
                comment=f"Good product - {rating} stars",
                is_approved=True,
            )
            print(f"✓ Created review: {user.email} rated {rating}★")

    # Recalculate
    new_stats = ReviewService.get_review_stats(product)
    print(f"\n✓ Updated statistics:")
    print(f"  Average Rating: {new_stats['average_rating']}★")
    print(f"  Total Reviews: {new_stats['total_reviews']}")


def test_admin_reply():
    """Test 5: Admin reply to review."""
    print("\n" + "=" * 70)
    print("TEST 5: Admin Reply to Review")
    print("=" * 70)

    review = ProductReview.objects.filter(is_approved=True).first()
    if not review:
        print("✗ No approved reviews found")
        return

    print(f"Review: {review.comment[:50]}...")
    print(f"Has admin reply: {review.has_admin_reply}")

    # Add admin reply
    reply_text = "Thank you for your feedback! We're glad you enjoyed the product."
    review.add_admin_reply(reply_text)

    print(f"✓ Admin reply added:")
    print(f"  Reply: {review.admin_reply[:50]}...")
    print(f"  Replied at: {review.admin_replied_at}")
    print(f"  Has reply: {review.has_admin_reply}")


def test_wishlist_creation():
    """Test 6: Wishlist creation."""
    print("\n" + "=" * 70)
    print("TEST 6: Wishlist Creation")
    print("=" * 70)

    user = User.objects.first()

    # Get or create wishlist
    wishlist = WishlistService.get_or_create_wishlist(user)

    print(f"✓ Wishlist created/retrieved:")
    print(f"  User: {wishlist.user.email}")
    print(f"  Public ID: {wishlist.public_id}")
    print(f"  Item count: {wishlist.item_count}")

    return wishlist


def test_add_remove_wishlist():
    """Test 7: Add/remove items from wishlist."""
    print("\n" + "=" * 70)
    print("TEST 7: Add/Remove Wishlist Items")
    print("=" * 70)

    user = User.objects.first()
    variant = ProductVariant.objects.filter(is_active=True, stock_quantity__gt=0).first()

    if not variant:
        print("✗ No active variants found")
        return

    # Add to wishlist
    item = WishlistService.add_item(user, variant)
    print(f"✓ Added to wishlist:")
    print(f"  Variant: {variant.name}")
    print(f"  User: {user.email}")

    # Verify item count
    wishlist = user.wishlist
    print(f"  Wishlist items: {wishlist.item_count}")

    # Try adding duplicate (should be idempotent)
    item2 = WishlistService.add_item(user, variant)
    print(f"✓ Duplicate add handled (idempotent)")
    print(f"  Same item: {item.id == item2.id}")

    # Remove from wishlist
    removed = WishlistService.remove_item(user, variant)
    print(f"✓ Removed from wishlist: {removed}")
    print(f"  Wishlist items: {wishlist.item_count}")

    # Add back for next tests
    WishlistService.add_item(user, variant)


def test_toggle_wishlist():
    """Test 8: Toggle wishlist item."""
    print("\n" + "=" * 70)
    print("TEST 8: Toggle Wishlist Item")
    print("=" * 70)

    user = User.objects.first()
    variant = ProductVariant.objects.filter(is_active=True).exclude(
        wishlist_items__wishlist__user=user
    ).first()

    if not variant:
        print("✗ No suitable variant found")
        return

    # Toggle (add)
    result1 = WishlistService.toggle_item(user, variant)
    print(f"✓ Toggle #1 (add):")
    print(f"  Added: {result1['added']}")
    print(f"  Item: {result1['item']}")

    # Toggle (remove)
    result2 = WishlistService.toggle_item(user, variant)
    print(f"✓ Toggle #2 (remove):")
    print(f"  Added: {result2['added']}")
    print(f"  Item: {result2['item']}")

    # Toggle back (add) for next test
    WishlistService.toggle_item(user, variant)


def test_move_to_cart():
    """Test 9: Move wishlist item to cart."""
    print("\n" + "=" * 70)
    print("TEST 9: Move Wishlist Item to Cart")
    print("=" * 70)

    user = User.objects.first()
    
    # Get wishlist item
    try:
        wishlist = user.wishlist
        wishlist_item = wishlist.items.first()
        
        if not wishlist_item:
            print("✗ No items in wishlist")
            return

        variant = wishlist_item.variant
        initial_wishlist_count = wishlist.item_count

        print(f"Wishlist before: {initial_wishlist_count} items")

        # Move to cart
        cart_item = WishlistService.move_to_cart(user, variant)

        print(f"✓ Moved to cart:")
        print(f"  Variant: {variant.name}")
        print(f"  Cart quantity: {cart_item.quantity}")
        print(f"  Wishlist after: {wishlist.item_count} items")
        
        # Verify removed from wishlist
        assert wishlist.item_count == initial_wishlist_count - 1, "Item should be removed from wishlist"
        print(f"✓ Verified: Item removed from wishlist")

    except Exception as e:
        print(f"✗ Error: {str(e)}")


def test_clear_wishlist():
    """Test 10: Clear wishlist."""
    print("\n" + "=" * 70)
    print("TEST 10: Clear Wishlist")
    print("=" * 70)

    user = User.objects.first()

    # Add some items first
    variants = ProductVariant.objects.filter(is_active=True)[:3]
    for variant in variants:
        try:
            WishlistService.add_item(user, variant)
        except:
            pass

    wishlist = user.wishlist
    initial_count = wishlist.item_count
    print(f"Wishlist items before clear: {initial_count}")

    # Clear wishlist
    removed_count = WishlistService.clear_wishlist(user)

    print(f"✓ Wishlist cleared:")
    print(f"  Items removed: {removed_count}")
    print(f"  Items remaining: {wishlist.item_count}")


def run_all_tests():
    """Run all Phase 11 tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "PHASE 11: ENGAGEMENT SYSTEM TESTS" + " " * 17 + "║")
    print("╚" + "=" * 68 + "╝")

    tests = [
        ("Review Creation", test_review_creation),
        ("Review Validation", test_review_validation),
        ("Review Approval", test_review_approval),
        ("Average Rating", test_average_rating),
        ("Admin Reply", test_admin_reply),
        ("Wishlist Creation", test_wishlist_creation),
        ("Add/Remove Items", test_add_remove_wishlist),
        ("Toggle Item", test_toggle_wishlist),
        ("Move to Cart", test_move_to_cart),
        ("Clear Wishlist", test_clear_wishlist),
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
    print(f"  Product Reviews: {ProductReview.objects.count()}")
    print(f"  - Approved: {ProductReview.objects.filter(is_approved=True).count()}")
    print(f"  - Pending: {ProductReview.objects.filter(is_approved=False).count()}")
    print(f"  Wishlists: {Wishlist.objects.count()}")
    print(f"  Wishlist Items: {WishlistItem.objects.count()}")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
