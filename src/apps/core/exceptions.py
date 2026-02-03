"""
Core Application Exceptions.

This module defines custom exceptions used throughout the e-commerce platform.
These exceptions provide clear error messages and can be caught specifically
in views and API endpoints for proper error handling.

Usage:
    from apps.core.exceptions import (
        ValidationError,
        InsufficientStockError,
        InvalidOperationError,
    )

    raise InsufficientStockError("Only 2 items available")
"""

from typing import Any


class EcomBaseException(Exception):
    """
    Base exception for all e-commerce application exceptions.

    All custom exceptions should inherit from this class to allow
    catching all application-specific exceptions with a single handler.

    Attributes:
        message: Human-readable error message.
        code: Machine-readable error code for API responses.
        details: Additional context about the error.
    """

    default_message: str = "An error occurred"
    default_code: str = "error"

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: Human-readable error message. Defaults to class default.
            code: Machine-readable error code. Defaults to class default.
            details: Additional context dictionary.
        """
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert exception to dictionary for API responses.

        Returns:
            Dictionary containing error information.
        """
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(EcomBaseException):
    """
    Raised when data validation fails.

    Use this for business logic validation, not Django form/serializer
    validation which has its own ValidationError.

    Example:
        if price < 0:
            raise ValidationError("Price cannot be negative")
    """

    default_message = "Validation failed"
    default_code = "validation_error"


class InsufficientStockError(EcomBaseException):
    """
    Raised when requested quantity exceeds available stock.

    Example:
        raise InsufficientStockError(
            message="Only 2 items available",
            details={"available": 2, "requested": 5}
        )
    """

    default_message = "Insufficient stock available"
    default_code = "insufficient_stock"


class InvalidOperationError(EcomBaseException):
    """
    Raised when an operation is not allowed in the current state.

    Example:
        if order.status == "shipped":
            raise InvalidOperationError("Cannot modify shipped orders")
    """

    default_message = "Operation not allowed"
    default_code = "invalid_operation"


class NotFoundError(EcomBaseException):
    """
    Raised when a requested resource is not found.

    Example:
        raise NotFoundError(
            message="Product not found",
            details={"product_id": 123}
        )
    """

    default_message = "Resource not found"
    default_code = "not_found"


class PermissionDeniedError(EcomBaseException):
    """
    Raised when user lacks permission for an operation.

    Example:
        raise PermissionDeniedError("Only order owner can cancel")
    """

    default_message = "Permission denied"
    default_code = "permission_denied"


class PaymentError(EcomBaseException):
    """
    Raised when payment processing fails.

    Example:
        raise PaymentError(
            message="Payment declined",
            details={"gateway_response": "insufficient_funds"}
        )
    """

    default_message = "Payment processing failed"
    default_code = "payment_error"


class CouponError(EcomBaseException):
    """
    Raised when coupon validation or application fails.

    Example:
        raise CouponError("Coupon has expired")
    """

    default_message = "Coupon is not valid"
    default_code = "coupon_error"


class CartError(EcomBaseException):
    """
    Raised when cart operations fail.

    Example:
        raise CartError("Cart is empty")
    """

    default_message = "Cart operation failed"
    default_code = "cart_error"
