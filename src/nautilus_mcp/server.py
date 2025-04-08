import logging
from functools import partial
from mcp.server import Server
from nautilus_trader.common.component import LiveClock, Logger

# Import trading tools
from .tools.trading import initialize_trading_node, connect_venue

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("nautilus-mcp")

class NautilusMCPServer(Server):
    def __init__(self):
        # Remove transport handling from init; it's managed by stdio_server context
        # Provide the required server name to the base class constructor
        # Capabilities are likely handled by the transport/serve lifecycle, not set directly here.
        # capabilities = {
        #     "tools": True,
        #     "resources": True, # Assuming we will add resources later
        #     "prompts": True,
        #     "logging": True
        # }
        super().__init__(name="nautilus-trader") # Pass server name only

        # Server identification - this might be redundant now if base class handles name
        # self.server_info("nautilus-trader", "0.1.0") # Initial version

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

    def log_info(self, message: str):
        """Helper to use the server's logger for INFO level."""
        self.logger.info(message)

    def log_error(self, message, *args, **kwargs):
        """Helper to use the server's logger for ERROR level."""
        self.logger.error(message, *args, **kwargs)

    def log_warning(self, message, *args, **kwargs):
        """Helper to use the server's logger for WARNING level."""
        self.logger.warning(message, *args, **kwargs)

    def _register_tools(self):
        """Register all trading and backtesting tools."""
        self.log_info("[Setup] Registering tools...")

        # Store tool functions using partial to bind the server instance.
        # NOTE: This currently bypasses the standard MCP metadata registration.
        # We need to find the correct mcp.Server method to register tools with metadata.
        self.tools = {}
        self.tools["initialize_trading_node"] = partial(initialize_trading_node, self)
        self.tools["connect_venue"] = partial(connect_venue, self)

        self.log_info(f"[Setup] Registered {len(self.tools)} tools (metadata pending correct registration method).")

        # Placeholder for backtesting tools
        # self._register_backtest_tools()

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
