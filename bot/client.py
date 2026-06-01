"""
client.py
~~~~~~~~~
Low-level Binance Futures Testnet REST client.
Handles authentication (HMAC-SHA256), request signing, and raw HTTP calls.
All API communication is isolated here — higher layers never touch requests directly.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")

BASE_URL = "https://testnet.binancefuture.com"

# Endpoints
EP_NEW_ORDER = "/fapi/v1/order"
EP_ACCOUNT   = "/fapi/v2/account"
EP_EXCHANGE_INFO = "/fapi/v1/exchangeInfo"


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error [{code}]: {message}")


class NetworkError(Exception):
    """Raised when a network-level failure occurs."""


class BinanceClient:
    """
    Thin wrapper around the Binance USDT-M Futures Testnet REST API.

    Parameters
    ----------
    api_key:    Testnet API key.
    api_secret: Testnet API secret.
    timeout:    HTTP request timeout in seconds (default 10).
    """

    def __init__(self, api_key: str, api_secret: str, timeout: int = 10) -> None:
        if not api_key or not api_secret:
            raise ValueError("Both api_key and api_secret must be provided.")

        self._api_key = api_key
        self._api_secret = api_secret
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.info("BinanceClient initialised (base URL: %s)", BASE_URL)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append server timestamp and HMAC-SHA256 signature to params dict."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request and return the parsed JSON body.

        Raises
        ------
        BinanceAPIError  – non-2xx API responses with a Binance error code.
        NetworkError     – connection / timeout issues.
        """
        params = params or {}
        if signed:
            params = self._sign(params)

        url = BASE_URL + endpoint
        logger.debug("→ %s %s | params: %s", method.upper(), url, params)

        try:
            if method.upper() == "GET":
                response = self._session.get(url, params=params, timeout=self._timeout)
            else:
                response = self._session.post(url, data=params, timeout=self._timeout)
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out: %s", exc)
            raise NetworkError(f"Request timed out after {self._timeout}s.") from exc
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error: %s", exc)
            raise NetworkError("Unable to reach Binance Testnet. Check your internet connection.") from exc

        logger.debug("← HTTP %s | body: %s", response.status_code, response.text[:500])

        try:
            data = response.json()
        except ValueError:
            raise BinanceAPIError(-1, f"Non-JSON response (HTTP {response.status_code}): {response.text[:200]}")

        if not response.ok:
            code = data.get("code", response.status_code)
            msg  = data.get("msg", response.reason)
            logger.error("API error [%s]: %s", code, msg)
            raise BinanceAPIError(code, msg)

        return data

    # ── Public API methods ────────────────────────────────────────────────────

    def place_order(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Place a futures order.  All keyword arguments are forwarded directly
        to the /fapi/v1/order endpoint (e.g. symbol, side, type, quantity, price).
        """
        logger.info(
            "Placing order → symbol=%s side=%s type=%s qty=%s price=%s",
            kwargs.get("symbol"),
            kwargs.get("side"),
            kwargs.get("type"),
            kwargs.get("quantity"),
            kwargs.get("price", "N/A"),
        )
        return self._request("POST", EP_NEW_ORDER, params=dict(kwargs), signed=True)

    def get_account(self) -> Dict[str, Any]:
        """Fetch account information (balances, positions)."""
        return self._request("GET", EP_ACCOUNT, signed=True)

    def get_exchange_info(self) -> Dict[str, Any]:
        """Fetch exchange trading rules and symbol information."""
        return self._request("GET", EP_EXCHANGE_INFO, signed=False)
