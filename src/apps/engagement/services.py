"""
Engagement Application Services - Phase 11: Reviews & Wishlist Logic.

This module contains business logic for engagement features:
- ReviewService: Product review validation and average rating calculation
- WishlistService: Wishlist management (add, remove, move to cart)
"""

from contextlib import ContextDecorator
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg, Count


class ReviewService:
    """
    Service for managing product reviews.

    Handles:
    - Review validation (one review per user per product)
    - Average rating calculation
    - Review approval workflow
    
    Usage:
        # Validate review
        ReviewService.validate_review(user, product)
        
        # Calculate average
        avg = ReviewService.calculate_average_rating(product)
    """

    @staticmethod
    def validate_review(user: Any, product: Any) -> None:
        """
        Validate if user can review this product.
        
        Ensures:
        - User hasn't already reviewed this product
        - Product is published
        
        Args:
            user: User attempting to review
            product: Product being reviewed
            
        Raises:
            ValidationError: If validation fails
            
        Example:
            ReviewService.validate_review(user, product)
            # Proceed with review creation
        """
        from apps.engagement.models import ProductReview

        # Check if product is published
        if product.status != "published":
            raise ValidationError("Cannot review unpublished products")

        # Check for existing review
        if ProductReview.objects.filter(user=user, product=product).exists():
            raise ValidationError(
                "You have already reviewed this product. "
                "You can edit your existing review."
            )

    @staticmethod
    def calculate_average_rating(product: Any) -> Decimal:
        """
        Calculate average rating for a product.
        
        Only counts approved reviews.
        
        Args:
            product: Product to calculate rating for
            
        Returns:
            Average rating as Decimal (0.0 if no reviews)
            
        Example:
            avg = ReviewService.calculate_average_rating(product)
            print(f"Average: {avg:.1f}★")
        """
        from apps.engagement.models import ProductReview

        result = ProductReview.objects.filter(
            product=product, is_approved=True
        ).aggregate(avg_rating=Avg("rating"), count=Count("id"))

        if result["count"] == 0:
            return Decimal("0.0")

        return Decimal(str(result["avg_rating"])).quantize(Decimal("0.1"))

    @staticmethod
    def get_review_stats(product: Any) -> dict[str, Any]:
        """
        Get comprehensive review statistics for a product.
        
        Args:
            product: Product to get stats for
            
        Returns:
            Dictionary with:
            - average_rating: Average star rating
            - total_reviews: Total approved review count
            - rating_distribution: Count per rating (1-5 stars)
            
        Example:
            stats = ReviewService.get_review_stats(product)
            print(f"{stats['average_rating']}★ ({stats['total_reviews']} reviews)")
        """
        from apps.engagement.models import ProductReview

        approved_reviews = ProductReview.objects.filter(
            product=product, is_approved=True
        )

        # Calculate distribution
        distribution = {i: 0 for i in range(1, 6)}
        for review in approved_reviews:
            distribution[review.rating] += 1

        avg_rating = ReviewService.calculate_average_rating(product)

        return {
            "average_rating": avg_rating,
            "total_reviews": approved_reviews.count(),
            "rating_distribution": distribution,
        }


class WishlistService:
    """
    Service for managing user wishlists.

    Handles:
    - Wishlist creation (one per user)
    - Add/remove items
    - Toggle variant (add if not present, remove if present)
    - Move items to cart
    
    Usage:
        # Add to wishlist
        WishlistService.add_item(user, variant)
        
        # Move to cart
        cart_item = WishlistService.move_to_cart(user, variant)
    """

    @staticmethod
    def get_or_create_wishlist(user: Any) -> Any:
        """
        Get or create wishlist for user.
        
        Each user has exactly one wishlist.
        
        Args:
            user: User to get wishlist for
            
        Returns:
            Wishlist instance
            
        Example:
            wishlist = WishlistService.get_or_create_wishlist(user)
        """
        from apps.engagement.models import Wishlist

        wishlist, created = Wishlist.objects.get_or_create(user=user)
        return wishlist

    @staticmethod
    @transaction.atomic
    def add_item(user: Any, variant: Any) -> Any:
        """
        Add variant to user's wishlist.
        
        Creates wishlist if it doesn't exist.
        Idempotent - won't duplicate if already present.
        
        Args:
            user: User adding item
            variant: ProductVariant to add
            
        Returns:
            WishlistItem instance (created or existing)
            
        Raises:
            ValidationError: If variant is inactive or deleted
            
        Example:
            item = WishlistService.add_item(user, variant)
        """
        from apps.engagement.models import WishlistItem

        # Validate variant
        if not variant.is_active or variant.is_deleted:
            raise ValidationError(f"Variant {variant.sku} is not available")

        if variant.product.status != "published":
            raise ValidationError(f"Product {variant.product.name} is not available")

        # Get or create wishlist
        wishlist = WishlistService.get_or_create_wishlist(user)

        # Add item (idempotent due to unique constraint)
        item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist, variant=variant
        )

        return item

    @staticmethod
    def remove_item(user: Any, variant: Any) -> bool:
        """
        Remove variant from user's wishlist.
        
        Args:
            user: User removing item
            variant: ProductVariant to remove
            
        Returns:
            True if item was removed, False if it wasn't in wishlist
            
        Example:
            removed = WishlistService.remove_item(user, variant)
        """
        from apps.engagement.models import WishlistItem

        try:
            wishlist = user.wishlist
            item = WishlistItem.objects.get(wishlist=wishlist, variant=variant)
            item.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def toggle_item(user: Any, variant: Any) -> dict[str, Any]:
        """
        Toggle variant in wishlist (add if absent, remove if present).
        
        Args:
            user: User toggling item
            variant: ProductVariant to toggle
            
        Returns:
            Dictionary with:
            - added: True if added, False if removed
            - item: WishlistItem if added, None if removed
            
        Example:
            result = WishlistService.toggle_item(user, variant)
            if result['added']:
                print("Added to wishlist")
            else:
                print("Removed from wishlist")
        """
        from apps.engagement.models import WishlistItem

        try:
            wishlist = user.wishlist
            item = WishlistItem.objects.get(wishlist=wishlist, variant=variant)
            item.delete()
            return {"added": False, "item": None}
        except Exception:
            item = WishlistService.add_item(user, variant)
            return {"added": True, "item": item}

    @staticmethod
    @transaction.atomic
    def move_to_cart(user: Any, variant: Any) -> Any:
        """
        Move variant from wishlist to cart.
        
        Removes from wishlist and adds to cart in single transaction.
        
        Args:
            user: User moving item
            variant: ProductVariant to move
            
        Returns:
            CartItem instance
            
        Raises:
            ValidationError: If variant not in wishlist or cart operation fails
            
        Example:
            cart_item = WishlistService.move_to_cart(user, variant)
        """
        from apps.orders.services import CartService

        # Remove from wishlist
        removed = WishlistService.remove_item(user, variant)
        if not removed:
            raise ValidationError("Item not in wishlist")

        # Add to cart
        cart = CartService.get_or_create_cart(user=user)
        cart_item = CartService.add_item(cart, variant, quantity=1)

        return cart_item

    @staticmethod
    def clear_wishlist(user: Any) -> int:
        """
        Clear all items from user's wishlist.
        
        Args:
            user: User whose wishlist to clear
            
        Returns:
            Number of items removed
            
        Example:
            count = WishlistService.clear_wishlist(user)
            print(f"Removed {count} items")
        """
        try:
            wishlist = user.wishlist
            count = wishlist.items.count()
            wishlist.items.all().delete()
            return count
        except Exception:
            return 0
