import pytest
from functools import partial
from src.nautilus_mcp.server import NautilusMCPServer
from src.nautilus_mcp.tools.trading import initialize_trading_node, connect_venue, get_instruments
from nautilus_trader.config import TradingNodeConfig, LiveDataEngineConfig, LiveRiskEngineConfig, LiveExecEngineConfig
from nautilus_trader.model.identifiers import TraderId, InstrumentId
from unittest.mock import AsyncMock, MagicMock, patch

# --- Pytest Fixtures (Setup) ---

# Fixture for valid config
@pytest.fixture
def valid_trading_config() -> TradingNodeConfig:
    """Provides a minimal valid configuration dictionary for TradingNode."""
    # Create instances of the required nested config objects
    data_engine_config = LiveDataEngineConfig()
    risk_engine_config = LiveRiskEngineConfig()
    exec_engine_config = LiveExecEngineConfig()

    # Return a fully formed TradingNodeConfig object
    return TradingNodeConfig(
        data_engine=data_engine_config,
        risk_engine=risk_engine_config,
        exec_engine=exec_engine_config,
        # Optionally set other fields like trader_id if needed for specific tests
        # trader_id=TraderId("SIM-001"), # Example
    )

@pytest.fixture
def mcp_server() -> NautilusMCPServer:
    """Provides a fresh instance of NautilusMCPServer for each test."""
    # We instantiate it directly, bypassing transport/serve for unit testing tools
    server = NautilusMCPServer()
    return server

# --- Test Cases ---

@pytest.mark.asyncio
async def test_initialize_trading_node_success(mcp_server: NautilusMCPServer, valid_trading_config: TradingNodeConfig):
    """Tests successful first-time initialization of the trading node."""
    # Prepare the tool function bound to the server instance
    init_tool = partial(initialize_trading_node, mcp_server)

    # Call the tool function
    result = init_tool(config=valid_trading_config) # Use the fixture

    # Assertions
    assert mcp_server.initialized is True, "Server should be marked as initialized."
    assert result["status"] == "success", f"Expected status 'success', got {result.get('status')}"
    assert "trader_id" in result, "Result should contain the trader_id." # Use the updated key name
    assert mcp_server.trading_node is not None, "Server should have a trading_node instance."
    # Check that trader_id is a TraderId instance and is truthy (i.e., not empty/default)
    assert isinstance(mcp_server.trading_node.trader_id, TraderId) and mcp_server.trading_node.trader_id # Use TraderId type
    assert result["trader_id"] == mcp_server.trading_node.trader_id.value, "Result trader_id should match node trader_id."


@pytest.mark.asyncio
async def test_initialize_trading_node_already_initialized(mcp_server: NautilusMCPServer, valid_trading_config: TradingNodeConfig):
    """Tests calling initialize_trading_node when already initialized."""
    # Arrange: Initialize the node first
    init_tool = partial(initialize_trading_node, mcp_server)
    first_result = init_tool(config=valid_trading_config) # Use the fixture for first init
    assert first_result["status"] == "success", "Initial setup failed."
    assert mcp_server.initialized is True, "Server should be initialized after first call."
    original_node = mcp_server.trading_node # Keep reference to original node

    # Act: Call initialize again with the same or different config (shouldn't matter)
    # Use the same fixture again for the second call
    second_result = init_tool(config=valid_trading_config)

    # Assertions for second call (should be a warning)
    assert second_result["status"] == "warning", "Second call should return a warning status."
    assert mcp_server.initialized is True, "Server should still be marked as initialized."
    assert mcp_server.trading_node.trader_id == original_node.trader_id, "Trading node trader_id object should not change on re-initialization."


# === Tests for connect_venue ===

def test_connect_venue_not_initialized(mcp_server):
    """Tests calling connect_venue before initialize_trading_node."""
    # Arrange
    venue_name = "FAKE_VENUE"
    credentials = {"api_key": "fake_key", "secret": "fake_secret"}

    # Act
    result = connect_venue(mcp_server, venue_name, credentials)

    # Assert
    assert mcp_server.initialized is False, "Server should not be initialized."
    assert result["status"] == "error", "Expected status 'error' when not initialized."
    assert "not initialized" in result["message"].lower(), "Message should indicate node not initialized."


def test_connect_venue_success(mcp_server, valid_trading_config):
    """Tests calling connect_venue after successful initialization (placeholder success)."""
    # Arrange - Initialize first
    init_result = initialize_trading_node(mcp_server, valid_trading_config)
    assert init_result["status"] == "success", "Initialization failed, cannot proceed with connect test."
    assert mcp_server.initialized is True, "Server should be initialized after successful init call."

    venue_name = "FAKE_VENUE"
    credentials = {"api_key": "fake_key", "secret": "fake_secret"}

    # Act
    connect_result = connect_venue(mcp_server, venue_name, credentials)

    # Assert (based on placeholder logic)
    assert connect_result["status"] == "success", "Expected status 'success' from placeholder logic."
    assert f"connected to venue {venue_name}".lower() in connect_result["message"].lower(), "Message should indicate successful connection (case-insensitive)."


# --- Tests for get_instruments ---

@pytest.mark.asyncio
async def test_get_instruments_not_initialized(mcp_server):
    """Test get_instruments when the trading node is not initialized."""
    # Call the tool function directly for testing its logic
    result = get_instruments(mcp_server)
    assert result["status"] == "error"
    assert "not initialized" in result["message"]

@pytest.mark.asyncio
async def test_get_instruments_success(mcp_server, valid_trading_config):
    """Test successful retrieval of instruments after initialization."""
    # Initialize the server - this creates the self.trading_node instance
    init_result = initialize_trading_node(mcp_server, valid_trading_config)
    assert init_result["status"] == "success", "Initialization failed, cannot proceed with get_instruments test."
    assert mcp_server.initialized is True, "Server should be initialized after successful init call."
    assert hasattr(mcp_server, 'trading_node') and mcp_server.trading_node is not None, "Trading node should exist after init."

    # Define mock instruments
    mock_instrument_1 = MagicMock()
    mock_instrument_1.id = InstrumentId.from_str("SIM-BTC/USDT.NAUTILUS")
    mock_instrument_2 = MagicMock()
    mock_instrument_2.id = InstrumentId.from_str("SIM-ETH/USDT.NAUTILUS")

    # Configure the mock trading node to return these instruments
    # We need to mock the instruments() method on the *instance* of the trading_node
    mcp_server.trading_node.instruments = MagicMock(return_value=[mock_instrument_1, mock_instrument_2])

    # Use the get_instruments tool function
    result = get_instruments(mcp_server)

    assert result["status"] == "success"
    assert isinstance(result["instruments"], list)
    assert len(result["instruments"]) == 2
    assert "SIM-BTC/USDT.NAUTILUS" in result["instruments"]
    assert "SIM-ETH/USDT.NAUTILUS" in result["instruments"]
    # Verify the mock was called
    mcp_server.trading_node.instruments.assert_called_once()

# --- Placeholder for Future Tool Tests ---
