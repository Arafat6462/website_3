"""
Cart service - business logic for shopping cart operations.

This module provides thread-safe cart operations with stock validation.
"""

from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import InsufficientStockError, ValidationError
from apps.orders.models import Cart, CartItem
from apps.products.inventory import InventoryService
from apps.products.models import ProductVariant


class CartService:
    """
    Service for managing shopping cart operations.

    Handles:
    - Adding/updating/removing items
    - Stock validation
    - Cart merging (guest → user)
    - Cart cleanup

    All operations are atomic and validate stock availability.

    Usage:
        # Get or create cart
        cart = CartService.get_or_create_cart(user=user)
        
        # Add item
        item = CartService.add_item(cart, variant, quantity=2)
        
        # Update quantity
        item = CartService.update_item(item, quantity=5)
        
        # Remove item
        CartService.remove_item(item)
        
        # Merge guest cart on login
        CartService.merge_carts(guest_cart, user_cart)
    """

    @staticmethod
    def get_or_create_cart(
        user: Any | None = None, session_key: str | None = None
    ) -> Cart:
        """
        Get or create cart for user or session.

        Args:
            user: Authenticated user (optional).
            session_key: Session identifier for guests (optional).

        Returns:
            Cart instance.

        Raises:
            ValidationError: If neither user nor session_key provided.

        Example:
            # User cart
            cart = CartService.get_or_create_cart(user=request.user)
            
            # Guest cart
            cart = CartService.get_or_create_cart(
                session_key=request.session.session_key
            )
        """
        if user and user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=user)
            return cart

        if session_key:
            # Get or create guest cart
            cart, created = Cart.objects.get_or_create(
                session_key=session_key,
                defaults={
                    "expires_at": timezone.now() + timedelta(days=30)
                },
            )

            # Refresh expiry if cart exists but almost expired
            if not created and cart.expires_at:
                days_left = (cart.expires_at - timezone.now()).days
                if days_left < 7:
                    cart.expires_at = timezone.now() + timedelta(days=30)
                    cart.save(update_fields=["expires_at"])

            return cart

        raise ValidationError("Either user or session_key must be provided")

    @staticmethod
    @transaction.atomic
    def add_item(
        cart: Cart, variant: ProductVariant, quantity: int = 1
    ) -> CartItem:
        """
        Add item to cart or update quantity if already exists.

        Validates:
        - Variant is active and not deleted
        - Product is published
        - Sufficient stock available (if tracked)

        Args:
            cart: The cart to add to.
            variant: The product variant to add.
            quantity: Number of units (must be positive).

        Returns:
            CartItem instance (created or updated).

        Raises:
            ValidationError: If variant inactive or product unpublished.
            InsufficientStockError: If not enough stock available.

        Example:
            item = CartService.add_item(cart, variant, quantity=2)
        """
        # Validate variant
        if not variant.is_active or variant.is_deleted:
            raise ValidationError(f"Variant {variant.sku} is not available")

        if variant.product.status != "published":
            raise ValidationError(f"Product {variant.product.name} is not available")

        # Check stock availability
        if not InventoryService.check_availability(variant, quantity):
            raise InsufficientStockError(
                f"Only {variant.stock_quantity} units available for {variant.sku}"
            )

        # Get or create cart item
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={
                "quantity": quantity,
                "unit_price": variant.effective_price,
            },
        )

        if not created:
            # Item exists, update quantity
            new_quantity = item.quantity + quantity

            # Re-validate stock for new quantity
            if not InventoryService.check_availability(variant, new_quantity):
                raise InsufficientStockError(
                    f"Cannot add {quantity} more. Only {variant.stock_quantity} units available"
                )

            item.quantity = new_quantity
            item.unit_price = variant.effective_price  # Update to current price
            item.save()

        return item

    @staticmethod
    @transaction.atomic
    def update_item(item: CartItem, quantity: int) -> CartItem:
        """
        Update cart item quantity.

        Args:
            item: The CartItem to update.
            quantity: New quantity (must be positive).

        Returns:
            Updated CartItem instance.

        Raises:
            ValidationError: If quantity is not positive.
            InsufficientStockError: If not enough stock for new quantity.

        Example:
            item = CartService.update_item(item, quantity=5)
        """
        if quantity <= 0:
            raise ValidationError("Quantity must be positive")

        # Validate stock for new quantity
        if not InventoryService.check_availability(item.variant, quantity):
            raise InsufficientStockError(
                f"Only {item.variant.stock_quantity} units available"
            )

        item.quantity = quantity
        item.unit_price = item.variant.effective_price  # Update to current price
        item.save()

        return item

    @staticmethod
    def remove_item(item: CartItem) -> None:
        """
        Remove item from cart.

        Args:
            item: The CartItem to remove.

        Example:
            CartService.remove_item(item)
        """
        item.delete()

    @staticmethod
    def clear_cart(cart: Cart) -> int:
        """
        Remove all items from cart.

        Args:
            cart: The cart to clear.

        Returns:
            Number of items removed.

        Example:
            count = CartService.clear_cart(cart)
        """
        count = cart.items.count()
        cart.items.all().delete()
        return count

    @staticmethod
    @transaction.atomic
    def merge_carts(guest_cart: Cart, user_cart: Cart) -> Cart:
        """
        Merge guest cart into user cart (called on login).

        Logic:
        - For each item in guest cart:
          - If item exists in user cart: keep higher quantity
          - If item not in user cart: move to user cart
        - Delete guest cart after merging

        Args:
            guest_cart: The guest session cart.
            user_cart: The authenticated user's cart.

        Returns:
            The user cart (with merged items).

        Example:
            merged_cart = CartService.merge_carts(guest_cart, user_cart)
        """
        for guest_item in guest_cart.items.all():
            try:
                # Check if user cart already has this variant
                user_item = user_cart.items.get(variant=guest_item.variant)

                # Keep higher quantity
                if guest_item.quantity > user_item.quantity:
                    # Validate stock for higher quantity
                    if InventoryService.check_availability(
                        guest_item.variant, guest_item.quantity
                    ):
                        user_item.quantity = guest_item.quantity
                        user_item.unit_price = guest_item.variant.effective_price
                        user_item.save()

            except CartItem.DoesNotExist:
                # Item not in user cart, move it
                if InventoryService.check_availability(
                    guest_item.variant, guest_item.quantity
                ):
                    CartItem.objects.create(
                        cart=user_cart,
                        variant=guest_item.variant,
                        quantity=guest_item.quantity,
                        unit_price=guest_item.variant.effective_price,
                    )

        # Delete guest cart
        guest_cart.delete()

        return user_cart

    @staticmethod
    def refresh_prices(cart: Cart) -> int:
        """
        Update all item prices to current variant prices.

        Useful before checkout to ensure prices are current.

        Args:
            cart: The cart to refresh.

        Returns:
            Number of items updated.

        Example:
            updated = CartService.refresh_prices(cart)
        """
        count = 0
        for item in cart.items.all():
            item.update_price()
            count += 1
        return count

    @staticmethod
    def validate_cart(cart: Cart) -> dict[str, Any]:
        """
        Validate cart before checkout.

        Checks:
        - All variants are active and in stock
        - All products are published
        - Prices are current

        Args:
            cart: The cart to validate.

        Returns:
            Dict with 'valid' (bool) and 'errors' (list) keys.

        Example:
            result = CartService.validate_cart(cart)
            if not result['valid']:
                for error in result['errors']:
                    print(error)
        """
        errors = []

        for item in cart.items.all():
            # Check variant active
            if not item.variant.is_active or item.variant.is_deleted:
                errors.append(
                    f"{item.variant.sku}: Product variant no longer available"
                )
                continue

            # Check product published
            if item.variant.product.status != "published":
                errors.append(
                    f"{item.variant.product.name}: Product no longer available"
                )
                continue

            # Check stock
            if not InventoryService.check_availability(item.variant, item.quantity):
                errors.append(
                    f"{item.variant.sku}: Only {item.variant.stock_quantity} units available (requested {item.quantity})"
                )

            # Check price changed significantly (>10%)
            current_price = float(item.variant.effective_price)
            cart_price = float(item.unit_price)
            price_diff_pct = abs((current_price - cart_price) / cart_price * 100)

            if price_diff_pct > 10:
                errors.append(
                    f"{item.variant.sku}: Price changed from ৳{cart_price} to ৳{current_price}"
                )

        return {"valid": len(errors) == 0, "errors": errors}

    @staticmethod
    def cleanup_expired_carts() -> int:
        """
        Delete expired guest carts.

        Should be run as a scheduled task (cron job).

        Returns:
            Number of carts deleted.

        Example:
            count = CartService.cleanup_expired_carts()
            print(f'Deleted {count} expired carts')
        """
        expired = Cart.objects.filter(
            user__isnull=True,  # Guest carts only
            expires_at__lt=timezone.now(),
        )
        count = expired.count()
        expired.delete()
        return count
