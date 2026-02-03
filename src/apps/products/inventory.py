"""
Inventory management service for products.

This module provides thread-safe inventory operations with proper locking
to prevent race conditions during stock updates.

Key Features:
- SELECT FOR UPDATE locking to prevent overselling
- Complete audit trail via InventoryLog
- Support for reservations (pending orders)
- Stock availability checks
"""

from typing import Any

from django.db import transaction
from django.db.models import F

from apps.core.exceptions import InsufficientStockError
from apps.products.models import InventoryLog, ProductVariant


class InventoryService:
    """
    Service for managing product inventory with race condition prevention.

    This service ensures thread-safe stock updates using database-level
    row locking (SELECT FOR UPDATE). This prevents two customers from
    buying the last item simultaneously.

    Usage:
        # Adjust stock manually
        InventoryService.adjust_stock(
            variant=variant,
            quantity=50,
            change_type='restocked',
            reference='PO-2026-001',
            user=admin_user,
            notes='Received from supplier'
        )

        # Reserve stock for order
        InventoryService.reserve_stock(
            variant=variant,
            quantity=2,
            order_id='ORD-2026-00123'
        )

        # Release stock (cancelled order)
        InventoryService.release_stock(
            variant=variant,
            quantity=2,
            order_id='ORD-2026-00123'
        )

    Critical: All stock-changing operations must be wrapped in @transaction.atomic
    and use SELECT FOR UPDATE to prevent race conditions.
    """

    @staticmethod
    @transaction.atomic
    def adjust_stock(
        variant: ProductVariant,
        quantity: int,
        change_type: str,
        reference: str = "",
        user: Any = None,
        notes: str = "",
    ) -> ProductVariant:
        """
        Adjust variant stock with full locking and logging.

        This is the core method for all inventory changes. It:
        1. Locks the variant row (SELECT FOR UPDATE)
        2. Validates the change
        3. Updates stock
        4. Creates audit log

        Args:
            variant: The ProductVariant to adjust.
            quantity: Change amount (positive=increase, negative=decrease).
            change_type: Type from InventoryLog.ChangeType choices.
            reference: Optional reference ID (order, PO, etc.).
            user: User making the change (null for system).
            notes: Optional notes.

        Returns:
            Updated ProductVariant instance.

        Raises:
            InsufficientStockError: If trying to reduce below zero.
            ValueError: If variant doesn't track inventory.

        Example:
            # Restock 50 units
            variant = InventoryService.adjust_stock(
                variant=variant,
                quantity=50,
                change_type='restocked',
                reference='PO-2026-001',
                user=admin_user
            )

            # Deduct 2 units (sale)
            variant = InventoryService.adjust_stock(
                variant=variant,
                quantity=-2,
                change_type='sold',
                reference='ORD-2026-00123'
            )
        """
        # Lock the variant row to prevent concurrent modifications
        # This is CRITICAL for preventing overselling
        variant = ProductVariant.objects.select_for_update().get(pk=variant.pk)

        if not variant.product.track_inventory:
            raise ValueError(
                f"Variant {variant.sku} does not track inventory. "
                "Set product.track_inventory=True first."
            )

        quantity_before = variant.stock_quantity
        quantity_after = quantity_before + quantity

        # Prevent negative stock (unless backorders allowed)
        if quantity_after < 0:
            if not variant.product.allow_backorder:
                raise InsufficientStockError(
                    f"Insufficient stock for {variant.sku}. "
                    f"Requested: {abs(quantity)}, Available: {quantity_before}"
                )

        # Update stock
        variant.stock_quantity = quantity_after
        variant.save(update_fields=["stock_quantity", "updated_at"])

        # Create audit log
        InventoryLog.objects.create(
            variant=variant,
            change_type=change_type,
            quantity_change=quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reference=reference,
            notes=notes,
            created_by=user,
        )

        return variant

    @staticmethod
    @transaction.atomic
    def reserve_stock(
        variant: ProductVariant, quantity: int, order_id: str
    ) -> ProductVariant:
        """
        Reserve stock for a pending order.

        This deducts stock and logs it as 'reserved'. Use this when
        an order is confirmed but not yet shipped.

        Args:
            variant: The ProductVariant to reserve.
            quantity: Amount to reserve (must be positive).
            order_id: Order reference ID.

        Returns:
            Updated ProductVariant instance.

        Raises:
            InsufficientStockError: If not enough stock available.
            ValueError: If quantity is not positive.

        Example:
            # Reserve 2 units for order
            variant = InventoryService.reserve_stock(
                variant=variant,
                quantity=2,
                order_id='ORD-2026-00123'
            )
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        return InventoryService.adjust_stock(
            variant=variant,
            quantity=-quantity,  # Negative = deduction
            change_type=InventoryLog.ChangeType.RESERVED,
            reference=order_id,
            notes=f"Reserved for order {order_id}",
        )

    @staticmethod
    @transaction.atomic
    def release_stock(
        variant: ProductVariant, quantity: int, order_id: str
    ) -> ProductVariant:
        """
        Release reserved stock (e.g., cancelled order).

        This restores stock and logs it as 'released'. Use this when
        a reserved order is cancelled before shipping.

        Args:
            variant: The ProductVariant to release.
            quantity: Amount to release (must be positive).
            order_id: Order reference ID.

        Returns:
            Updated ProductVariant instance.

        Raises:
            ValueError: If quantity is not positive.

        Example:
            # Release 2 units from cancelled order
            variant = InventoryService.release_stock(
                variant=variant,
                quantity=2,
                order_id='ORD-2026-00123'
            )
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        return InventoryService.adjust_stock(
            variant=variant,
            quantity=quantity,  # Positive = addition
            change_type=InventoryLog.ChangeType.RELEASED,
            reference=order_id,
            notes=f"Released from cancelled order {order_id}",
        )

    @staticmethod
    @transaction.atomic
    def process_sale(
        variant: ProductVariant, quantity: int, order_id: str
    ) -> ProductVariant:
        """
        Process a sale (final deduction for shipped order).

        This deducts stock and logs it as 'sold'. Use this when
        an order is actually shipped/delivered.

        Note: If stock was already reserved, this will double-deduct.
        Use reserve_stock() first, then DON'T call this. Or skip reserve
        and call this directly for COD orders.

        Args:
            variant: The ProductVariant sold.
            quantity: Amount sold (must be positive).
            order_id: Order reference ID.

        Returns:
            Updated ProductVariant instance.

        Raises:
            InsufficientStockError: If not enough stock.
            ValueError: If quantity is not positive.

        Example:
            # Process sale (COD order workflow)
            variant = InventoryService.process_sale(
                variant=variant,
                quantity=2,
                order_id='ORD-2026-00123'
            )
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        return InventoryService.adjust_stock(
            variant=variant,
            quantity=-quantity,  # Negative = deduction
            change_type=InventoryLog.ChangeType.SOLD,
            reference=order_id,
            notes=f"Sold via order {order_id}",
        )

    @staticmethod
    @transaction.atomic
    def process_return(
        variant: ProductVariant, quantity: int, order_id: str, user: Any = None
    ) -> ProductVariant:
        """
        Process a customer return (restore stock).

        This restores stock and logs it as 'return'. Use this when
        a customer returns items.

        Args:
            variant: The ProductVariant being returned.
            quantity: Amount returned (must be positive).
            order_id: Original order reference ID.
            user: Staff member processing the return.

        Returns:
            Updated ProductVariant instance.

        Raises:
            ValueError: If quantity is not positive.

        Example:
            # Process return
            variant = InventoryService.process_return(
                variant=variant,
                quantity=1,
                order_id='ORD-2026-00123',
                user=admin_user
            )
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        return InventoryService.adjust_stock(
            variant=variant,
            quantity=quantity,  # Positive = addition
            change_type=InventoryLog.ChangeType.RETURN,
            reference=order_id,
            notes=f"Customer return from order {order_id}",
            user=user,
        )

    @staticmethod
    def check_availability(variant: ProductVariant, quantity: int) -> bool:
        """
        Check if sufficient stock is available.

        This is a read-only check. For atomic check-and-deduct, use
        adjust_stock() which locks the row.

        Args:
            variant: The ProductVariant to check.
            quantity: Requested quantity.

        Returns:
            True if available, False otherwise.

        Example:
            if InventoryService.check_availability(variant, 5):
                # Proceed with order
            else:
                # Show out of stock message
        """
        if not variant.product.track_inventory:
            return True  # Inventory not tracked, always available

        if variant.product.allow_backorder:
            return True  # Backorders allowed, always available

        return variant.stock_quantity >= quantity

    @staticmethod
    @transaction.atomic
    def bulk_adjust_stock(
        adjustments: list[dict[str, Any]], user: Any = None
    ) -> list[ProductVariant]:
        """
        Bulk adjust stock for multiple variants.

        Useful for receiving large shipments or doing inventory counts.

        Args:
            adjustments: List of dicts with keys: variant, quantity, change_type, reference, notes.
            user: User making the changes.

        Returns:
            List of updated ProductVariant instances.

        Example:
            adjustments = [
                {
                    'variant': variant1,
                    'quantity': 50,
                    'change_type': 'restocked',
                    'reference': 'PO-2026-001'
                },
                {
                    'variant': variant2,
                    'quantity': 30,
                    'change_type': 'restocked',
                    'reference': 'PO-2026-001'
                },
            ]
            variants = InventoryService.bulk_adjust_stock(adjustments, user=admin_user)
        """
        updated_variants = []

        for adjustment in adjustments:
            variant = InventoryService.adjust_stock(
                variant=adjustment["variant"],
                quantity=adjustment["quantity"],
                change_type=adjustment["change_type"],
                reference=adjustment.get("reference", ""),
                notes=adjustment.get("notes", ""),
                user=user,
            )
            updated_variants.append(variant)

        return updated_variants

    @staticmethod
    def get_low_stock_variants(threshold: int | None = None) -> list[ProductVariant]:
        """
        Get all variants with low stock.

        Args:
            threshold: Custom threshold (uses variant.low_stock_threshold if None).

        Returns:
            QuerySet of ProductVariant instances with low stock.

        Example:
            # Get all low stock variants
            low_stock = InventoryService.get_low_stock_variants()
            for variant in low_stock:
                print(f'{variant.sku}: {variant.stock_quantity} units left')

            # Get variants with less than 5 units
            critical = InventoryService.get_low_stock_variants(threshold=5)
        """
        if threshold is not None:
            return list(
                ProductVariant.objects.filter(
                    product__track_inventory=True,
                    is_active=True,
                    is_deleted=False,
                    stock_quantity__lte=threshold,
                    stock_quantity__gt=0,
                )
            )
        else:
            # Use each variant's own threshold
            return list(
                ProductVariant.objects.filter(
                    product__track_inventory=True,
                    is_active=True,
                    is_deleted=False,
                    stock_quantity__lte=F("low_stock_threshold"),
                    stock_quantity__gt=0,
                )
            )
