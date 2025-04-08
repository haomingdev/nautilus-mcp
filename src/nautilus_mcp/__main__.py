import asyncio
import logging
import signal
import sys
import os

# Add the parent directory (src) to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.stdio import stdio_server 
from nautilus_mcp.server import NautilusMCPServer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("nautilus-mcp-main")

async def run_server():
    """Initializes and runs the Nautilus MCP server using stdio transport."""
    logger.info("Starting Nautilus MCP Server...")
    # Instantiate the server (no transport needed here)
    server = NautilusMCPServer()

    # Use the stdio_server context manager
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Stdio transport established. Running server...")
        # Assuming the server has a `run` method that takes streams
        # If the base Server class doesn't have `run`, this needs adjustment
        # based on how mcp expects servers to interact with transport streams.
        await server.serve(read_stream, write_stream) 

    logger.info("Server shutdown complete.")

def handle_shutdown(sig, frame):
    """Handles graceful shutdown signals."""
    logger.info(f"Received signal {sig}, shutting down...")
    # You might need more sophisticated shutdown logic here, e.g., canceling tasks
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down...")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)
