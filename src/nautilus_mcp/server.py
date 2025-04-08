import logging
from functools import partial
from mcp.server import Server
from nautilus_trader.common.clock import LiveClock
from nautilus_trader.common.logging import Logger

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("nautilus-mcp")

class NautilusMCPServer(Server):
    def __init__(self):
        # Remove transport handling from init; it's managed by stdio_server context
        super().__init__()

        # Server identification
        self.server_info("nautilus-trader", "0.1.0") # Initial version

        # Configure capabilities (can be adjusted later)
        self.set_capabilities({
            "tools": True,
            "resources": True, # Assuming we will add resources later
            "prompts": True,
            "logging": True
        })

        # Initialize clock and logger for potential NautilusTrader use
        # Note: NautilusTrader instance itself is not created here yet
        self.clock = LiveClock()
        # Using MCP's logger for now, can integrate Nautilus specific logger later if needed
        self.logger = logger # Use the module-level logger

        # Placeholder for the actual NautilusTrader TradingNode instance
        self.trading_node = None
        self.initialized = False # Flag to track if trading_node is initialized

        self.log_info("[Setup] NautilusMCPServer initialized, ready for configuration.")

        # Register tools and resources (placeholders for now)
        self._register_tools()
        self._register_resources()

    def log_info(self, message, *args, **kwargs):
        """Helper to use the server's logger for INFO level."""
        self.logger.info(message, *args, **kwargs)

    def log_error(self, message, *args, **kwargs):
        """Helper to use the server's logger for ERROR level."""
        self.logger.error(message, *args, **kwargs)

    def log_warning(self, message, *args, **kwargs):
        """Helper to use the server's logger for WARNING level."""
        self.logger.warning(message, *args, **kwargs)

    def _register_tools(self):
        """Register all trading and backtesting tools."""
        self.log_info("[Setup] Registering tools...")

        # Import tool functions
        from .tools.trading import (
            initialize_trading_node,
            connect_venue,
            get_instruments,
            submit_market_order,
            submit_limit_order,
            cancel_order,
            get_account_info,
            get_positions,
            get_order_status
        )
        # Other imports will go here later (e.g., from .tools.backtest import ...)

        # Register trading tools
        self.register_tool(
            "initialize_trading_node",
            partial(initialize_trading_node, self)
        )
        self.register_tool(
            "connect_venue",
            partial(connect_venue, self)
        )
        self.register_tool(
            "get_instruments",
            partial(get_instruments, self)
        )
        self.register_tool(
            "submit_market_order",
            partial(submit_market_order, self)
        )
        self.register_tool(
            "submit_limit_order",
            partial(submit_limit_order, self)
        )
        self.register_tool(
            "cancel_order",
            partial(cancel_order, self)
        )
        self.register_tool(
            "get_account_info",
            partial(get_account_info, self)
        )
        self.register_tool(
            "get_positions",
            partial(get_positions, self)
        )
        self.register_tool(
            "get_order_status",
            partial(get_order_status, self)
        )

        self.log_info("[Setup] Trading tools registered.")

    def _register_resources(self):
        """Register all data resources."""
        self.log_info("[Setup] Registering resources...")
        # Resource registration will happen in Phase 3
        # Example: from .resources.market_data import MarketDataResource
        # Example: self.add_resource(MarketDataResource("historical_data", "application/json"))
        self.log_info("[Setup] Resource registration complete.")
        pass

    # --- Placeholder for Core Tool Methods (to be implemented in Phase 2) ---

    # Example placeholder:
    # def initialize_trading_node(self, config):
    #     pass
