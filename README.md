# 📈 Binance Futures Testnet Trading Bot

A clean, production-structured Python CLI application for placing orders on
the **Binance USDT-M Futures Testnet**.  Built with separation of concerns,
structured logging, robust input validation, and full exception handling.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Order Examples](#order-examples)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [Assumptions & Design Decisions](#assumptions--design-decisions)

---

## Features

| Feature | Details |
|---|---|
| **Order Types** | `MARKET`, `LIMIT`, `STOP_MARKET` (bonus) |
| **Sides** | `BUY` and `SELL` |
| **CLI** | Clean `argparse`-based interface with `--help` |
| **Validation** | All inputs validated before any network call |
| **Logging** | Per-session timestamped log files + console output |
| **Error Handling** | Catches API errors, network failures, and bad input |
| **Structure** | Layered: `client` → `orders` → `validators` → `cli` |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package marker
│   ├── client.py            # Binance REST API wrapper (auth, signing, HTTP)
│   ├── orders.py            # Order placement logic (Market / Limit / Stop)
│   ├── validators.py        # Input validation (symbol, side, qty, price…)
│   ├── logging_config.py    # Structured logger (file + console)
│   └── cli.py               # CLI entry point (argparse, I/O, dispatch)
├── logs/                    # Auto-created; one log file per session
├── .env.example             # Template for API credentials
├── requirements.txt
└── README.md
```

---

## Setup

### 1 — Get Testnet credentials

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in / register and go to **API Management**
3. Create a new API key — copy the **key** and **secret**

### 2 — Clone and install

```bash
git clone https://github.com/<your-username>/trading-bot.git
cd trading-bot

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3 — Configure credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your testnet credentials:

```dotenv
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

> ⚠️ **Never commit your `.env` file to git.** It is already in `.gitignore`.

---

## Configuration

All configuration is read from environment variables (loaded from `.env`
via `python-dotenv`).

| Variable | Required | Description |
|---|---|---|
| `BINANCE_API_KEY` | ✅ | Your Binance Futures Testnet API key |
| `BINANCE_API_SECRET` | ✅ | Your Binance Futures Testnet API secret |

---

## Running the Bot

Run from the repository root:

```bash
python -m bot.cli [options]
```

### Options

```
  --symbol   SYMBOL      Trading pair (e.g. BTCUSDT)           [required]
  --side     BUY|SELL    Order side                             [required]
  --type     TYPE        MARKET, LIMIT, or STOP_MARKET          [required]
  --quantity QTY         Order quantity (e.g. 0.01)             [required]
  --price    PRICE       Limit price — required for LIMIT orders
  --stop-price PRICE     Stop trigger — required for STOP_MARKET orders
  --tif      GTC|IOC|FOK Time-in-force for LIMIT (default: GTC)
  -h, --help             Show this help message and exit
```

---

## Order Examples

### Market BUY

```bash
python -m bot.cli \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.01
```

**Output:**
```
╔══════════════════════════════════════════════╗
║       Binance Futures Testnet Trading Bot    ║
║              USDT-M Perpetuals               ║
╚══════════════════════════════════════════════╝

  ORDER REQUEST SUMMARY
──────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.01
──────────────────────────────────────────────────

  Submitting order to Binance Futures Testnet …

──────────────────────────────────────────────────
  ORDER CONFIRMATION
──────────────────────────────────────────────────
  Order ID     : 4751823901
  Symbol       : BTCUSDT
  Side         : BUY
  Type         : MARKET
  Status       : FILLED
  Quantity     : 0.01
  Executed Qty : 0.01
  Avg Price    : 65312.40000
──────────────────────────────────────────────────

  ✅  Order placed successfully!
```

---

### Limit SELL

```bash
python -m bot.cli \
  --symbol BTCUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.01 \
  --price 67000
```

---

### Stop-Market BUY (Bonus order type)

```bash
python -m bot.cli \
  --symbol ETHUSDT \
  --side BUY \
  --type STOP_MARKET \
  --quantity 0.1 \
  --stop-price 3500
```

---

### Validation error example

```bash
python -m bot.cli --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01
# [ERROR] Price is required for LIMIT orders.
```

---

## Logging

Every run creates a new timestamped log file under `logs/`:

```
logs/trading_bot_20250710_142201.log
```

- **File** — captures `DEBUG` and above (full request params, raw responses)
- **Console** — captures `INFO` and above (human-readable milestones only)

Sample log entries are included in `logs/` for a market order and a limit order.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing / invalid input | Caught by `validators.py`; prints clear message and exits with code 1 |
| Missing credentials | Detected before any network call; prints instructions |
| Binance API error (e.g. -1121 invalid symbol) | `BinanceAPIError` caught; error code + message printed and logged |
| Network timeout / connection refused | `NetworkError` caught; friendly message printed and logged |
| Non-JSON API response | Caught and reported with HTTP status code |

---

## Assumptions & Design Decisions

- **Testnet only** — the base URL is hardcoded to `https://testnet.binancefuture.com`.
  Switching to mainnet requires changing `BASE_URL` in `client.py`.
- **No third-party Binance SDK** — uses only `requests` for full transparency
  over authentication and request construction.
- **Decimal arithmetic** — all quantity and price values use Python's `Decimal`
  to avoid floating-point precision issues.
- **One log file per session** — named with a timestamp so old logs are never
  overwritten and debugging is easier.
- **`STOP_MARKET` as the bonus order type** — chosen because it is the most
  practical risk-management tool for a futures bot.
- **Credentials via `.env`** — keeps secrets out of the command line (which can
  appear in shell history) and out of the source code.
