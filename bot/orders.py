"""
orders.py
~~~~~~~~~
Order-placement logic layer.
Translates validated user intent into Binance API calls and formats results
for human-readable output.  Never performs I/O or argparse directly.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from .client import BinanceClient, BinanceAPIError, NetworkError

logger = logging.getLogger("trading_bot.orders")


# ── Result dataclass (plain dict for simplicity) ─────────────────────────────

def _build_result(success: bool, summary: str, raw: Optional[Dict] = None) -> Dict[str, Any]:
    return {"success": success, "summary": summary, "raw": raw or {}}


# ── Order builders ────────────────────────────────────────────────────────────

def place_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
) -> Dict[str, Any]:
    """Place a MARKET order and return a result dict."""
    logger.info("[MARKET] %s %s qty=%s", side, symbol, quantity)

    params = {
        "symbol":   symbol,
        "side":     side,
        "type":     "MARKET",
        "quantity": str(quantity),
    }

    try:
        response = client.place_order(**params)
        logger.info("[MARKET] Order accepted — orderId=%s status=%s", response.get("orderId"), response.get("status"))
        return _build_result(True, _format_order_response(response), response)
    except (BinanceAPIError, NetworkError) as exc:
        logger.error("[MARKET] Order failed: %s", exc)
        return _build_result(False, str(exc))


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    """Place a LIMIT order and return a result dict."""
    logger.info("[LIMIT] %s %s qty=%s price=%s tif=%s", side, symbol, quantity, price, time_in_force)

    params = {
        "symbol":      symbol,
        "side":        side,
        "type":        "LIMIT",
        "quantity":    str(quantity),
        "price":       str(price),
        "timeInForce": time_in_force,
    }

    try:
        response = client.place_order(**params)
        logger.info("[LIMIT] Order accepted — orderId=%s status=%s", response.get("orderId"), response.get("status"))
        return _build_result(True, _format_order_response(response), response)
    except (BinanceAPIError, NetworkError) as exc:
        logger.error("[LIMIT] Order failed: %s", exc)
        return _build_result(False, str(exc))


def place_stop_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    stop_price: Decimal,
) -> Dict[str, Any]:
    """Place a STOP_MARKET order (bonus order type) and return a result dict."""
    logger.info("[STOP_MARKET] %s %s qty=%s stopPrice=%s", side, symbol, quantity, stop_price)

    params = {
        "symbol":    symbol,
        "side":      side,
        "type":      "STOP_MARKET",
        "quantity":  str(quantity),
        "stopPrice": str(stop_price),
    }

    try:
        response = client.place_order(**params)
        logger.info("[STOP_MARKET] Order accepted — orderId=%s status=%s", response.get("orderId"), response.get("status"))
        return _build_result(True, _format_order_response(response), response)
    except (BinanceAPIError, NetworkError) as exc:
        logger.error("[STOP_MARKET] Order failed: %s", exc)
        return _build_result(False, str(exc))


# ── Formatting helpers ────────────────────────────────────────────────────────

def _format_order_response(resp: Dict[str, Any]) -> str:
    """Return a clean, readable string from a raw Binance order response."""
    lines = [
        "─" * 50,
        "  ORDER CONFIRMATION",
        "─" * 50,
        f"  Order ID     : {resp.get('orderId', 'N/A')}",
        f"  Client OID   : {resp.get('clientOrderId', 'N/A')}",
        f"  Symbol       : {resp.get('symbol', 'N/A')}",
        f"  Side         : {resp.get('side', 'N/A')}",
        f"  Type         : {resp.get('type', 'N/A')}",
        f"  Status       : {resp.get('status', 'N/A')}",
        f"  Quantity     : {resp.get('origQty', 'N/A')}",
        f"  Executed Qty : {resp.get('executedQty', 'N/A')}",
        f"  Avg Price    : {resp.get('avgPrice') or resp.get('price') or 'N/A'}",
        f"  Time in Force: {resp.get('timeInForce', 'N/A')}",
        "─" * 50,
    ]
    return "\n".join(lines)
