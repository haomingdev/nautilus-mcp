# NautilusTrader MCP Server Overview

## Introduction

This document outlines the implementation of a Model Context Protocol (MCP) server for [nautilus_trader](https://github.com/nautechsystems/nautilus_trader), an open-source, high-performance algorithmic trading platform. The MCP server enables seamless integration between nautilus_trader's capabilities and any application supporting the Model Context Protocol.

## About NautilusTrader

NautilusTrader is a Python-native algorithmic trading platform with:

- Core written in Rust for high performance with asynchronous networking using tokio
- Event-driven architecture for both backtesting and live trading
- Support for multiple venues and asset classes (FX, Equities, Futures, Options, Crypto and Betting)
- Advanced order types (IOC, FOK, GTC, GTD, DAY, AT_THE_OPEN, AT_THE_CLOSE) and execution capabilities
- Redis-backed performant state persistence (optional)
- AI-first design philosophy for developing and training AI trading agents

## MCP Server Implementation

### Architecture Overview

For this implementation, we'll run NautilusTrader directly within the MCP server process. This embedded architecture provides several advantages:

- No need for a separate bridge component or inter-process communication
- Lower latency for trading operations
- Simpler deployment and configuration
- Direct access to all NautilusTrader API capabilities

The MCP server will instantiate a NautilusTrader `TradingNode` instance when initialized and expose its functionality through the MCP tools interface.

### Setup and Installation

```bash
# Install MCP
pip install mcp
# Or with uv (recommended as nautilus_trader uses uv)
uv add "mcp[cli]"

# Install nautilus_trader
pip install -U nautilus_trader
# Or with uv
uv add nautilus_trader
```

### Core Components

The NautilusTrader MCP server implements these key functions:

1. **Trading Node Initialization**: Configure and initialize the trading environment
2. **Venue Connection**: Establish connections to trading venues with authentication
3. **Instrument Management**: Retrieve and manage tradable instruments
4. **Order Management**: Submit, modify, and cancel orders with advanced order types
5. **Account Information**: Access account balances and positions
6. **Backtesting**: Run simulations on historical data using both high-level and low-level APIs

#### Backtesting API Levels

NautilusTrader provides two different API levels for backtesting that our MCP server should support:

- **Low-level API (BacktestEngine)**: For loading raw data using data loaders and wranglers, providing fine-grained control over the backtest process
- **High-level API (BacktestNode)**: For loading data into the data catalog and running backtests with a more streamlined interface

### MCP Server Configuration

The server can be registered with MCP using:

```bash
mcp install nautilus_trader_server.py -v API_KEY=your_api_key
```

Or by manually editing settings.json:

```json
{
  "mcpServers": {
    "nautilus-trader": {
      "command": "python",
      "args": ["nautilus_trader_server.py"],
      "env": {
        "API_KEY": "your_api_key",
        "OTHER_CONFIG": "value"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### MCP Capabilities

The server should explicitly define its capabilities to the MCP client:

```python
# Define server capabilities
server_capabilities = {
    "tools": True,       # Enable tool support for trading operations
    "resources": True,   # Enable resource support for market data
    "prompts": True,     # Enable prompt support
    "logging": True      # Enable logging support
}
```

### Transport Configuration

MCP supports multiple transport providers. For a Python-based server, we can implement:

```python
# For standard input/output transport
from mcp.transport import StdioTransport
transport = StdioTransport()

# For Server-Sent Events (SSE) transport (for web-based clients)
from mcp.transport import SSETransport
sse_transport = SSETransport(port=8080)
```

## Implementation Details

The server can be implemented using Python and the MCP SDK with both synchronous and asynchronous API options:

### Synchronous Implementation

```python
from mcp.server import MCPServer
from mcp.transport import StdioTransport
from nautilus_trader.live.node import TradingNode
from nautilus_trader.common.clock import LiveClock
from nautilus_trader.common.logging import Logger

class NautilusMCPServer(MCPServer):
    def __init__(self):
        # Initialize with transport provider
        super().__init__(StdioTransport())

        # Server identification and capabilities
        self.server_info("nautilus-trader", "1.0.0")
        self.set_capabilities({
            "tools": True,
            "resources": True,
            "prompts": True,
            "logging": True
        })

        # Initialize components - NautilusTrader will run in the same process
        self.clock = LiveClock()
        self.logger = Logger(clock=self.clock)
        self.trading_node = None  # Will be initialized on first use

        # Register trading functions as tools
        self.register_tool("initialize_trading_node", self.initialize_trading_node)
        self.register_tool("submit_order", self.submit_order)
        # ... other tools

    def initialize_trading_node(self, config):
        """Initialize the embedded NautilusTrader instance"""
        try:
            # Create and configure the trading node directly in this process
            self.trading_node = TradingNode(
                config=config,
                clock=self.clock,
                logger=self.logger
            )
            return {"status": "success", "message": "Trading node initialized"}
        except Exception as e:
            self.log_error(f"[Error] Failed to initialize: {str(e)}")
            return {"status": "error", "message": str(e)}
```

### Asynchronous Implementation

```python
import asyncio
from mcp.server import AsyncMCPServer

class AsyncNautilusMCPServer(AsyncMCPServer):
    async def initialize_trading_node(self, config):
        # Async implementation
        pass

    async def submit_order(self, order_params):
        # Async implementation
        pass
```

### Key Features

- **Type Safety**: Comprehensive parameter validation for trading operations
- **Error Handling**: Robust error catching and reporting with contextual information
- **Logging**: Detailed logging using MCP's structured logging capabilities
- **Configuration**: Flexible configuration options for different trading environments
- **Authentication**: Secure handling of API credentials for trading venues
- **Session Management**: Support for managing multiple client sessions
- **Concurrency**: Handle multiple simultaneous trading operations

## Error Handling

The MCP server should implement robust error handling for trading operations:

```python
def submit_order(self, params):
    try:
        # Attempt to submit order
        order = self.trading_node.submit_order(params)
        return {"status": "success", "order_id": order.id.value}
    except ConnectionError as e:
        self.log_error("[Connection] Failed to reach venue", e)
        return {"status": "error", "type": "connection", "message": str(e)}
    except ValidationError as e:
        self.log_error("[Validation] Invalid order parameters", e)
        return {"status": "error", "type": "validation", "message": str(e)}
    except Exception as e:
        self.log_error("[System] Unexpected error submitting order", e)
        return {"status": "error", "type": "system", "message": str(e)}
```

## Testing Requirements

Before using in production:

1. Test initialization and venue connection with both real and simulated venues
2. Verify instrument data retrieval across different asset classes
3. Test order submission with small test orders using various order types
4. Validate both low-level (BacktestEngine) and high-level (BacktestNode) backtesting APIs
5. Confirm proper error handling with comprehensive error scenarios
6. Benchmark performance under load conditions
7. Verify logging output and notification handling

## Future Enhancements

- Strategy management functions for loading and configuring trading strategies
- Portfolio analytics with risk metrics and performance visualization
- Performance optimization for high-frequency trading scenarios
- Additional venue adapters for more trading venues and asset classes
- Advanced risk management features including position sizing and risk controls
- Machine learning integration for strategy optimization
- Streaming market data resources for real-time analysis

## References

- [NautilusTrader Documentation](https://nautilustrader.io/docs/)
- [NautilusTrader Getting Started](https://nautilustrader.io/docs/latest/getting_started/)
- [MCP Plugin Development Protocol](.clinerules)
- [MCP Server Documentation](https://modelcontextprotocol.io/sdk/java/mcp-server)
- [MCP for Server Developers](https://modelcontextprotocol.io/quickstart/server)
- [NautilusTrader GitHub Repository](https://github.com/nautechsystems/nautilus_trader)
