"""
cli.py
~~~~~~
Command-line interface entry point.
Parses arguments, validates inputs, calls the orders layer, and prints results.
This module only handles I/O — no business logic lives here.
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from .client import BinanceClient
from .logging_config import setup_logger
from .orders import place_limit_order, place_market_order, place_stop_market_order
from .validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

# ── Banner ────────────────────────────────────────────────────────────────────

BANNER = r"""
╔══════════════════════════════════════════════╗
║       Binance Futures Testnet Trading Bot    ║
║              USDT-M Perpetuals               ║
╚══════════════════════════════════════════════╝
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place Market, Limit, or Stop-Market orders on Binance Futures Testnet.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  Market BUY  0.01 BTC:
    python -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

  Limit SELL  0.01 BTC @ 65000:
    python -m bot.cli --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 65000

  Stop-Market BUY  0.01 BTC if price hits 67000:
    python -m bot.cli --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.01 --stop-price 67000
        """,
    )

    parser.add_argument(
        "--symbol",
        required=True,
        metavar="SYMBOL",
        help="Trading pair symbol (e.g. BTCUSDT, ETHUSDT)",
    )
    parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        metavar="SIDE",
        help="Order side: BUY or SELL",
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        metavar="TYPE",
        help="Order type: MARKET, LIMIT, or STOP_MARKET",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        metavar="QTY",
        help="Order quantity (e.g. 0.01)",
    )
    parser.add_argument(
        "--price",
        default=None,
        metavar="PRICE",
        help="Limit price — required for LIMIT orders",
    )
    parser.add_argument(
        "--stop-price",
        dest="stop_price",
        default=None,
        metavar="STOP_PRICE",
        help="Stop trigger price — required for STOP_MARKET orders",
    )
    parser.add_argument(
        "--tif",
        dest="time_in_force",
        default="GTC",
        choices=["GTC", "IOC", "FOK"],
        help="Time-in-force for LIMIT orders (default: GTC)",
    )
    return parser


def main() -> None:
    load_dotenv()

    logger = setup_logger()
    print(BANNER)

    # ── Parse CLI arguments ──────────────────────────────────────────────────
    parser = _build_parser()
    args = parser.parse_args()

    # ── Validate inputs ──────────────────────────────────────────────────────
    try:
        symbol     = validate_symbol(args.symbol)
        side       = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity   = validate_quantity(args.quantity)
        price      = validate_price(args.price, order_type)
        stop_price = validate_stop_price(args.stop_price, order_type)
    except ValidationError as exc:
        print(f"\n[ERROR] {exc}\n")
        logger.error("Validation failed: %s", exc)
        sys.exit(1)

    # ── Print order request summary ──────────────────────────────────────────
    print("  ORDER REQUEST SUMMARY")
    print("─" * 50)
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {quantity}")
    if price:
        print(f"  Price      : {price}")
    if stop_price:
        print(f"  Stop Price : {stop_price}")
    print("─" * 50)

    logger.info(
        "Order request → symbol=%s side=%s type=%s qty=%s price=%s stop_price=%s",
        symbol, side, order_type, quantity, price, stop_price,
    )

    # ── Load credentials from environment ────────────────────────────────────
    api_key    = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print("\n[ERROR] BINANCE_API_KEY and BINANCE_API_SECRET must be set in your .env file.\n")
        logger.error("Missing API credentials in environment.")
        sys.exit(1)

    # ── Initialise client ────────────────────────────────────────────────────
    try:
        client = BinanceClient(api_key=api_key, api_secret=api_secret)
    except ValueError as exc:
        print(f"\n[ERROR] {exc}\n")
        sys.exit(1)

    # ── Dispatch to appropriate order function ───────────────────────────────
    print("\n  Submitting order to Binance Futures Testnet …\n")

    if order_type == "MARKET":
        result = place_market_order(client, symbol, side, quantity)
    elif order_type == "LIMIT":
        result = place_limit_order(client, symbol, side, quantity, price, args.time_in_force)
    else:  # STOP_MARKET
        result = place_stop_market_order(client, symbol, side, quantity, stop_price)

    # ── Print result ─────────────────────────────────────────────────────────
    if result["success"]:
        print(result["summary"])
        print("\n  ✅  Order placed successfully!\n")
        logger.info("Order placed successfully. Raw response: %s", result["raw"])
    else:
        print(f"\n  ❌  Order failed: {result['summary']}\n")
        logger.error("Order failed. Reason: %s", result["summary"])
        sys.exit(1)


if __name__ == "__main__":
    main()
