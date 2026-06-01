

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


class ValidationError(ValueError):
    """Raised when user-supplied input fails validation."""



def validate_symbol(symbol: str) -> str:
    """Return upper-cased symbol or raise ValidationError."""
    symbol = symbol.strip().upper()
    if not symbol.isalpha() or len(symbol) < 5:
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Expected format: BTCUSDT, ETHUSDT, etc."
        )
    return symbol


def validate_side(side: str) -> str:
    """Return upper-cased side or raise ValidationError."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Return upper-cased order type or raise ValidationError."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str) -> Decimal:
    """Parse and validate quantity; must be a positive number."""
    try:
        qty = Decimal(str(quantity).strip())
    except InvalidOperation:
        raise ValidationError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than zero, got {qty}.")
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[Decimal]:
    """
    Validate price field.
    - LIMIT orders → price is required and must be positive.
    - MARKET orders → price is ignored (returns None).
    """
    order_type = order_type.strip().upper()

    if order_type == "MARKET":
        return None  # price not needed

    if price is None or str(price).strip() == "":
        raise ValidationError("Price is required for LIMIT orders.")

    try:
        p = Decimal(str(price).strip())
    except InvalidOperation:
        raise ValidationError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValidationError(f"Price must be greater than zero, got {p}.")
    return p


def validate_stop_price(stop_price: Optional[str], order_type: str) -> Optional[Decimal]:
    """Validate stop price for STOP_MARKET orders."""
    if order_type != "STOP_MARKET":
        return None
    if stop_price is None or str(stop_price).strip() == "":
        raise ValidationError("Stop price is required for STOP_MARKET orders.")
    try:
        sp = Decimal(str(stop_price).strip())
    except InvalidOperation:
        raise ValidationError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
    if sp <= 0:
        raise ValidationError(f"Stop price must be greater than zero, got {sp}.")
    return sp
