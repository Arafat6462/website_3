"""
Orders service - business logic for cart, coupon, shipping, and tax operations.

This module provides thread-safe operations with validation:
- CartService: Shopping cart management
- CouponService: Coupon validation and discount calculation
- ShippingService: Shipping cost calculation
- TaxService: Tax calculation
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


class CouponService:
    """
    Service for managing coupon validation and discount calculations.

    Handles:
    - Coupon validation (eligibility, expiry, limits)
    - Discount calculation (percentage/fixed)
    - Usage tracking
    - Product/category restrictions

    All discount calculations respect minimum order and maximum discount limits.

    Usage:
        # Validate coupon
        result = CouponService.validate_coupon('SAVE10', user, cart)
        if not result['valid']:
            print(result['errors'])
        
        # Calculate discount
        discount = CouponService.calculate_discount(coupon, cart)
        
        # Apply coupon (track usage)
        usage = CouponService.apply_coupon(coupon, cart, user, discount)
    """

    @staticmethod
    def validate_coupon(
        code: str,
        cart: Cart,
        user: Any | None = None,
        guest_identifier: str | None = None,
    ) -> dict[str, Any]:
        """
        Validate if coupon can be applied to cart.

        Args:
            code: Coupon code to validate
            cart: Shopping cart
            user: User applying coupon (None for guest)
            guest_identifier: Email/phone for guest users

        Returns:
            Dictionary with 'valid' (bool), 'errors' (list), 'coupon' (Coupon | None)

        Validation checks:
            - Coupon exists and is active
            - Within validity period
            - Not exceeded usage limit
            - Not exceeded per-user limit
            - Cart meets minimum order amount
            - First order only restriction (if applicable)
            - Product/category restrictions (if applicable)

        Example:
            result = CouponService.validate_coupon('SAVE10', cart, user=user)
            if result['valid']:
                coupon = result['coupon']
                discount = CouponService.calculate_discount(coupon, cart)
        """
        from apps.orders.models import Coupon, CouponUsage

        errors = []

        # Check coupon exists
        try:
            coupon = Coupon.objects.get(code=code.upper(), is_deleted=False)
        except Coupon.DoesNotExist:
            return {"valid": False, "errors": ["Invalid coupon code"], "coupon": None}

        # Check active status
        if not coupon.is_active:
            errors.append("This coupon is not active")

        # Check validity period
        if not coupon.is_valid:
            errors.append("This coupon has expired or is not yet valid")

        # Check global usage limit
        if coupon.is_exhausted:
            errors.append("This coupon has reached its usage limit")

        # Check per-user usage limit
        if coupon.usage_limit_per_user is not None:
            if user:
                user_usage_count = CouponUsage.objects.filter(
                    coupon=coupon, user=user
                ).count()
            elif guest_identifier:
                user_usage_count = CouponUsage.objects.filter(
                    coupon=coupon, guest_identifier=guest_identifier
                ).count()
            else:
                user_usage_count = 0

            if user_usage_count >= coupon.usage_limit_per_user:
                errors.append(
                    f"You have already used this coupon {coupon.usage_limit_per_user} time(s)"
                )

        # Check minimum order amount
        cart_subtotal = cart.subtotal
        if cart_subtotal < coupon.minimum_order:
            errors.append(
                f"Minimum order amount of ৳{coupon.minimum_order} required (current: ৳{cart_subtotal})"
            )

        # Check first order only restriction
        if coupon.first_order_only and user:
            # Will be checked against Order model in Phase 10
            # For now, skip this check
            pass

        # Check product/category restrictions
        if coupon.applicable_categories or coupon.applicable_products:
            eligible_items = CouponService._get_eligible_items(cart, coupon)
            if not eligible_items:
                errors.append(
                    "This coupon is not applicable to items in your cart"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "coupon": coupon if len(errors) == 0 else None,
        }

    @staticmethod
    def calculate_discount(coupon: Any, cart: Cart) -> float:
        """
        Calculate discount amount for cart.

        Args:
            coupon: Coupon to apply
            cart: Shopping cart

        Returns:
            Discount amount (float)

        Calculation:
            - Percentage: (subtotal * percentage / 100), capped by maximum_discount
            - Fixed: Fixed amount, not exceeding subtotal
            - Respects product/category restrictions

        Example:
            coupon = Coupon.objects.get(code='SAVE10')
            discount = CouponService.calculate_discount(coupon, cart)
            final_total = cart.subtotal - discount
        """
        from decimal import Decimal

        # Get eligible items (if restrictions apply)
        if coupon.applicable_categories or coupon.applicable_products:
            eligible_items = CouponService._get_eligible_items(cart, coupon)
            eligible_subtotal = sum(item.line_total for item in eligible_items)
        else:
            eligible_subtotal = float(cart.subtotal)

        # Calculate discount based on type
        if coupon.discount_type == "percentage":
            discount = eligible_subtotal * (float(coupon.discount_value) / 100)

            # Apply maximum discount cap
            if coupon.maximum_discount:
                discount = min(discount, float(coupon.maximum_discount))
        else:  # fixed
            discount = float(coupon.discount_value)

        # Ensure discount doesn't exceed cart subtotal
        discount = min(discount, eligible_subtotal)

        return round(discount, 2)

    @staticmethod
    @transaction.atomic
    def apply_coupon(
        coupon: Any,
        cart: Cart,
        user: Any | None = None,
        guest_identifier: str | None = None,
        discount_amount: float | None = None,
    ) -> Any:
        """
        Apply coupon and track usage.

        This should be called when order is created (Phase 10).
        For now, it just creates a usage record.

        Args:
            coupon: Coupon to apply
            cart: Shopping cart
            user: User applying coupon
            guest_identifier: Email/phone for guests
            discount_amount: Calculated discount (if None, auto-calculate)

        Returns:
            CouponUsage instance

        Side effects:
            - Increments coupon.times_used
            - Creates CouponUsage record

        Example:
            usage = CouponService.apply_coupon(
                coupon, cart, user=user, discount_amount=50.00
            )
        """
        from apps.orders.models import CouponUsage

        if discount_amount is None:
            discount_amount = CouponService.calculate_discount(coupon, cart)

        # Create usage record
        usage = CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            guest_identifier=guest_identifier or "",
            discount_amount=discount_amount,
        )

        # Increment usage counter
        coupon.times_used += 1
        coupon.save(update_fields=["times_used", "updated_at"])

        return usage

    @staticmethod
    def _get_eligible_items(cart: Cart, coupon: Any) -> list[Any]:
        """
        Get cart items eligible for coupon discount.

        Args:
            cart: Shopping cart
            coupon: Coupon with restrictions

        Returns:
            List of eligible CartItem instances

        Filters items based on:
            - applicable_categories: Product category IDs
            - applicable_products: Product IDs
        """
        eligible_items = []

        for item in cart.items.select_related("variant__product"):
            product = item.variant.product
            category_id = product.category_id

            # Check category restriction
            if coupon.applicable_categories:
                if category_id not in coupon.applicable_categories:
                    continue

            # Check product restriction
            if coupon.applicable_products:
                if product.id not in coupon.applicable_products:
                    continue

            eligible_items.append(item)

        return eligible_items


class ShippingService:
    """
    Service for calculating shipping costs.

    Handles:
    - Zone detection by area
    - Free shipping threshold
    - Shipping cost calculation

    Usage:
        # Get zone by area
        zone = ShippingService.get_zone_for_area('Dhaka')
        
        # Calculate shipping
        cost = ShippingService.calculate_shipping(cart, 'Dhaka')
        
        # Check free shipping eligibility
        is_free = ShippingService.is_free_shipping_eligible(cart, zone)
    """

    @staticmethod
    def get_zone_for_area(area: str) -> Any | None:
        """
        Find shipping zone for given area.

        Args:
            area: City/area name (case-insensitive)

        Returns:
            ShippingZone instance or None if not found

        Search order:
            1. Exact match in areas list
            2. Case-insensitive partial match
            3. First active zone as fallback

        Example:
            zone = ShippingService.get_zone_for_area('Dhaka')
            if zone:
                cost = zone.calculate_shipping_cost(500.00)
        """
        from apps.orders.models import ShippingZone

        area_lower = area.lower().strip()

        # Try exact match first
        zones = ShippingZone.objects.filter(is_active=True)
        for zone in zones:
            if area_lower in [a.lower().strip() for a in zone.areas]:
                return zone

        # Fallback to first active zone
        return zones.first()

    @staticmethod
    def calculate_shipping(cart: Any, area: str) -> dict[str, Any]:
        """
        Calculate shipping cost for cart.

        Args:
            cart: Cart instance
            area: Delivery area

        Returns:
            Dictionary with:
                - zone: ShippingZone instance or None
                - cost: Shipping cost (float)
                - is_free: Whether free shipping applies (bool)
                - estimated_days: Delivery estimate (str)
                - error: Error message if zone not found (str or None)

        Example:
            result = ShippingService.calculate_shipping(cart, 'Dhaka')
            if result['error']:
                print(result['error'])
            else:
                print(f"Shipping: ৳{result['cost']} ({result['estimated_days']})")
        """
        zone = ShippingService.get_zone_for_area(area)

        if not zone:
            return {
                "zone": None,
                "cost": 0.0,
                "is_free": False,
                "estimated_days": "",
                "error": f"No shipping zone found for area: {area}",
            }

        cart_subtotal = float(cart.subtotal)
        shipping_cost = zone.calculate_shipping_cost(cart_subtotal)
        is_free = shipping_cost == 0.0 and zone.has_free_shipping

        return {
            "zone": zone,
            "cost": shipping_cost,
            "is_free": is_free,
            "estimated_days": zone.estimated_days,
            "error": None,
        }

    @staticmethod
    def is_free_shipping_eligible(cart: Any, zone: Any) -> bool:
        """
        Check if cart qualifies for free shipping.

        Args:
            cart: Cart instance
            zone: ShippingZone instance

        Returns:
            True if free shipping applies

        Example:
            if ShippingService.is_free_shipping_eligible(cart, zone):
                print('Free shipping!')
        """
        if not zone or not zone.has_free_shipping:
            return False

        return float(cart.subtotal) >= float(zone.free_shipping_threshold)


class TaxService:
    """
    Service for calculating order taxes.

    Handles:
    - Multiple tax rules
    - Priority-based application
    - Percentage and fixed taxes

    Usage:
        # Calculate total tax
        tax_amount = TaxService.calculate_order_tax(subtotal=1000.00)
        
        # Get breakdown
        breakdown = TaxService.get_tax_breakdown(subtotal=1000.00)
        for item in breakdown:
            print(f"{item['name']}: ৳{item['amount']}")
    """

    @staticmethod
    def calculate_order_tax(subtotal: float) -> float:
        """
        Calculate total tax for order subtotal.

        Applies all active tax rules in priority order.

        Args:
            subtotal: Order subtotal amount

        Returns:
            Total tax amount

        Example:
            tax = TaxService.calculate_order_tax(1000.00)
            total = 1000.00 + tax
        """
        from apps.orders.models import TaxRule

        total_tax = 0.0

        for rule in TaxRule.objects.filter(is_active=True):
            total_tax += rule.calculate_tax(subtotal)

        return round(total_tax, 2)

    @staticmethod
    def get_tax_breakdown(subtotal: float) -> list[dict[str, Any]]:
        """
        Get detailed tax breakdown.

        Args:
            subtotal: Order subtotal amount

        Returns:
            List of dictionaries with:
                - name: Tax name
                - type: Tax type (percentage/fixed)
                - rate: Tax rate
                - amount: Calculated amount

        Example:
            breakdown = TaxService.get_tax_breakdown(1000.00)
            # Returns: [
            #     {'name': 'VAT', 'type': 'percentage', 'rate': 15.0, 'amount': 150.0},
            #     {'name': 'Service Charge', 'type': 'fixed', 'rate': 10.0, 'amount': 10.0}
            # ]
        """
        from apps.orders.models import TaxRule

        breakdown = []

        for rule in TaxRule.objects.filter(is_active=True):
            tax_amount = rule.calculate_tax(subtotal)
            breakdown.append(
                {
                    "name": rule.name,
                    "type": rule.type,
                    "rate": float(rule.rate),
                    "amount": tax_amount,
                }
            )

        return breakdown


