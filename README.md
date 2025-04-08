# NautilusTrader MCP Server

MCP Server integration for the NautilusTrader algorithmic trading platform.

## Overview

This project provides a Model Context Protocol (MCP) server that allows AI agents and other MCP clients to interact with NautilusTrader for:

- Live trading operations (order management, account info, positions)
- Backtesting trading strategies
- Accessing market data

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd nautilus-mcp
    ```
2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    # Or for development:
    # pip install -e .[dev]  <- Assuming a setup.py with dev extras is added later
    ```

## Usage

1.  **Configure the server:** (Details TBD - likely via MCP settings or a config file)
2.  **Run the server:**
    ```bash
    python -m nautilus_mcp
    ```
3.  **Register with MCP CLI (Optional but recommended):**
    ```bash
    mcp install src/nautilus_mcp/server.py --name nautilus-trader -v # Add env vars if needed
    ```

## Project Structure

```
nautilus-mcp/
├── .venv/                  # Virtual environment
├── docs/                   # Documentation files
├── src/
│   └── nautilus_mcp/
│       ├── __init__.py
│       ├── __main__.py     # Entry point for `python -m nautilus_mcp`
│       ├── server.py       # Core MCP Server class
│       ├── tools/          # MCP tools implementations
│       │   ├── __init__.py
│       │   └── (e.g., trading.py, backtest.py)
│       └── resources/      # MCP resource implementations
│           ├── __init__.py
│           └── (e.g., market_data.py)
├── tests/                  # Unit and integration tests
│   ├── __init__.py
│   └── (e.g., test_server.py)
├── .gitignore
├── README.md
└── requirements.txt
```

## Development

(Add details about running tests, linting, contributing guidelines later)

## License

(Specify license)
