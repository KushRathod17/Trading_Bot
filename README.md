# Binance Futures Testnet Trading Bot

A Python CLI tool to place orders on Binance Futures Testnet (USDT-M). Built as part of an internship assignment.

---

## What it does

- Places Market and Limit orders on Binance Futures Testnet
- Supports BUY and SELL on any futures pair (BTCUSDT, ETHUSDT, etc.)
- Takes all inputs from the command line
- Logs every request and response to a file
- Handles bad inputs and API errors cleanly

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── client.py          # handles API calls and request signing
│   ├── orders.py          # market, limit, stop order logic
│   ├── validators.py      # checks user input before sending anything
│   ├── logging_config.py  # sets up file + console logging
│   └── cli.py             # entry point, reads CLI args
├── logs/                  # log files get saved here automatically
├── .env.example           # copy this to .env and add your keys
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get testnet API keys

Go to https://testnet.binancefuture.com, log in with GitHub, and generate an API key. Save both the key and secret somewhere — the secret only shows once.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your keys

```bash
cp .env.example .env
```

Open `.env` and fill in:

```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

Don't commit this file — it's already in `.gitignore`.

---

## How to run

```bash
python -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a limit order

```bash
python -m bot.cli --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 67000
```

### Place a stop-market order (bonus)

```bash
python -m bot.cli --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.01 --stop-price 95000
```

### See all options

```bash
python -m bot.cli --help
```

---

## Logging

Each run creates a new log file in `logs/` named with the timestamp. The file logs everything including raw API responses. Console only shows the important stuff.

---

## Error handling

- Wrong input (e.g. missing price for limit order) → caught before any API call is made
- API errors → error code and message printed clearly
- Network issues → friendly message, no crash
- Missing `.env` keys → tells you exactly what's missing

---

## Assumptions

- Only works with Binance Futures Testnet — base URL is hardcoded in `client.py`
- Used `requests` directly instead of the python-binance library — easier to see what's happening with auth
- Prices and quantities use Python's `Decimal` to avoid floating point issues
- Chose STOP_MARKET as the bonus order type since it's the most useful for risk management
