import logging
from nautilus_trader.live.node import TradingNode
from nautilus_trader.config import TradingNodeConfig # Import config type if needed for type hinting or validation

# Get a logger specific to this module if desired, or rely on the server's logger
logger = logging.getLogger(__name__)

def initialize_trading_node(server_instance, config: dict) -> dict:
    """
    Initialize the embedded NautilusTrader trading node.

    Expects the server instance to have `trading_node`, `initialized`,
    `clock`, `logger` (Nautilus compatible logger), `log_info`, `log_warning`,
    and `log_error` attributes/methods.

    Args:
        server_instance: The instance of NautilusMCPServer.
        config: A dictionary containing the configuration for the TradingNode.
                This should match the structure expected by nautilus_trader.

    Returns:
        A dictionary with 'status' ('success', 'warning', or 'error') and 'message'.
    """
    if server_instance.initialized:
        server_instance.log_warning("[Initialize] Trading node already initialized.")
        # Return a warning status if already initialized
        return {"status": "warning", "message": "Trading node already initialized."}

    try:
        # Log the attempt, consider redacting sensitive parts of config in production
        server_instance.log_info(f"[Initialize] Attempting to initialize TradingNode...") # Config logged separately if needed

        # Validate or parse config if necessary - TradingNode might do this internally
        # For now, assume the passed dict `config` is valid TradingNodeConfig structure

        # Create trading node using the server's clock and logger instance
        # This follows the pattern shown in the technical spec appendix
        server_instance.trading_node = TradingNode(
            config=config,
            # Pass the clock and logger instance from the server
            # Ensure the server's logger is compatible or adapt if needed
            clock=server_instance.clock,
            logger=server_instance.logger
        )

        # Note: TradingNode might take some time to initialize fully,
        # depending on config (e.g., connecting to components like Redis).
        # This call is synchronous here. Consider async if startup is long.

        server_instance.initialized = True
        server_instance.log_info("[Initialize] Trading node initialized successfully.")
        return {"status": "success", "message": "Trading node initialized successfully."}

    except Exception as e:
        server_instance.log_error(f"[Error][Initialize] Failed to initialize trading node: {str(e)}", exc_info=True)
        # Ensure node and flag are reset on failure
        server_instance.trading_node = None
        server_instance.initialized = False
        return {"status": "error", "message": f"Failed to initialize trading node: {str(e)}"}

# --- Trading Tools Implementation ---

def connect_venue(server_instance, venue_name: str, credentials: dict) -> dict:
    """
    Connect to a specific trading venue using the initialized TradingNode.

    Args:
        server_instance: The instance of NautilusMCPServer.
        venue_name: The name of the venue to connect to (e.g., 'BINANCE').
        credentials: A dictionary containing the API key, secret, etc.

    Returns:
        A dictionary with status and message.
    """
    if not server_instance.initialized or not server_instance.trading_node:
        server_instance.log_error("[ConnectVenue] Error: Trading node not initialized.")
        return {"status": "error", "message": "Trading node not initialized. Call initialize_trading_node first."}

    try:
        server_instance.log_info(f"[ConnectVenue] Attempting to connect to venue: {venue_name}...")

        # NautilusTrader expects a venue configuration dictionary.
        # Adapt the incoming credentials dict to the format Nautilus needs if necessary.
        # The exact structure depends on the specific venue adapter in Nautilus.
        # Assuming a simple direct pass-through for now, but might need adjustment.
        venue_config = {
            "venue": venue_name.upper(), # Ensure venue name is uppercase if required
            "credentials": credentials
        }

        # Call the TradingNode's connect_venue method.
        # This is typically a synchronous call, but check Nautilus docs.
        # It might raise exceptions on connection failure or bad credentials.
        server_instance.trading_node.connect_venue(venue_config)

        server_instance.log_info(f"[ConnectVenue] Successfully connected to venue: {venue_name}")
        return {"status": "success", "message": f"Successfully connected to {venue_name}"}

    except Exception as e:
        server_instance.log_error(f"[Error][ConnectVenue] Failed to connect to venue {venue_name}: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Failed to connect to venue {venue_name}: {str(e)}"}

def get_instruments(server_instance, venue: str, symbol_filter: str = None) -> dict:
    """
    Retrieve the list of tradable instruments for a given venue.

    Args:
        server_instance: The instance of NautilusMCPServer.
        venue: The name of the venue (e.g., 'BINANCE').
        symbol_filter: Optional filter to apply to instrument symbols (implementation TBD).

    Returns:
        A dictionary with status and a list of instruments (or error message).
    """
    if not server_instance.initialized or not server_instance.trading_node:
        server_instance.log_error("[GetInstruments] Error: Trading node not initialized.")
        return {"status": "error", "message": "Trading node not initialized."}

    try:
        venue_name = venue.upper()
        server_instance.log_info(f"[GetInstruments] Retrieving instruments for venue: {venue_name}...")

        # Check if the venue is connected/available in the trading node
        # Nautilus might manage this implicitly or require an explicit check.
        # For now, assume connect_venue was called.

        # Retrieve instruments using the TradingNode's method
        # Note: The return type and structure from Nautilus need verification.
        # It likely returns a list of Instrument objects.
        instruments = server_instance.trading_node.instruments(venue=venue_name)

        # Convert Instrument objects to a serializable format (e.g., list of dicts)
        instrument_list = []
        for inst in instruments:
            instrument_list.append({
                "id": str(inst.id), # e.g., "BTCUSDT.BINANCE"
                "symbol": inst.symbol,
                "venue": str(inst.venue),
                "precision_price": inst.precision_price,
                "precision_qty": inst.precision_qty,
                "multiplier": str(inst.multiplier), # Decimal needs conversion
                "lot_size": str(inst.lot_size), # Decimal needs conversion
                # Add other relevant fields as needed
            })

        # Apply filtering if symbol_filter is provided (basic example)
        if symbol_filter:
            server_instance.log_info(f"[GetInstruments] Applying filter: {symbol_filter}")
            filtered_list = [inst for inst in instrument_list if symbol_filter.upper() in inst["symbol"].upper()]
        else:
            filtered_list = instrument_list

        server_instance.log_info(f"[GetInstruments] Retrieved {len(filtered_list)} instruments for {venue_name}.")
        return {"status": "success", "instruments": filtered_list}

    except Exception as e:
        server_instance.log_error(f"[Error][GetInstruments] Failed to retrieve instruments for {venue}: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Failed to retrieve instruments for {venue}: {str(e)}"}

def submit_market_order(server_instance, params: dict) -> dict:
    """
    Submit a market order to the specified venue.

    Args:
        server_instance: The instance of NautilusMCPServer.
        params: Dictionary containing order details:
            - instrument_id (str): e.g., "BTCUSDT.BINANCE"
            - side (str): "BUY" or "SELL"
            - quantity (str or float): Order quantity
            - client_order_id (str, optional): Client-provided order ID

    Returns:
        A dictionary with status, message, and order_id if successful.
    """
    if not server_instance.initialized or not server_instance.trading_node:
        server_instance.log_error("[SubmitMarketOrder] Error: Trading node not initialized.")
        return {"status": "error", "message": "Trading node not initialized."}

    try:
        instrument_id_str = params.get("instrument_id")
        side_str = params.get("side")
        quantity_str = params.get("quantity") # Keep as string initially for Decimal conversion
        client_order_id_str = params.get("client_order_id") # Optional

        # Basic validation
        if not all([instrument_id_str, side_str, quantity_str]):
            return {"status": "error", "message": "Missing required parameters (instrument_id, side, quantity)"}

        server_instance.log_info(f"[SubmitMarketOrder] Attempting for {instrument_id_str}, Side: {side_str}, Qty: {quantity_str}")

        # Convert parameters to Nautilus types
        from nautilus_trader.model.identifiers import InstrumentId, ClientOrderId
        from nautilus_trader.model.orders import MarketOrder
        from nautilus_trader.model.enums import OrderSide
        from nautilus_trader.model.objects import Quantity, Price # Use for type safety if needed
        import time
        from decimal import Decimal

        instrument_id = InstrumentId.from_str(instrument_id_str)
        side = OrderSide.BUY if side_str.upper() == "BUY" else OrderSide.SELL

        # Use Decimal for quantity
        try:
            quantity = Quantity(Decimal(str(quantity_str)))
        except Exception as q_err:
             return {"status": "error", "message": f"Invalid quantity format: {quantity_str}. Error: {q_err}"}

        # Generate a unique client order ID if not provided
        # Using timestamp ensures uniqueness for this session
        if client_order_id_str:
            client_order_id = ClientOrderId(client_order_id_str)
        else:
            client_order_id = ClientOrderId(f"mcp-{instrument_id.symbol}-{int(time.time()*1000)}")

        # Create the MarketOrder object
        # Requires trader_id and default_strategy_id from the node
        # Ensure these are available/configured in the TradingNode
        order = MarketOrder(
            trader_id=server_instance.trading_node.trader_id,
            strategy_id=server_instance.trading_node.default_strategy_id, # Assuming default strategy
            instrument_id=instrument_id,
            client_order_id=client_order_id,
            order_side=side,
            quantity=quantity
        )

        # Submit the order via the trading node
        # This call might raise exceptions (e.g., insufficient funds, venue errors)
        server_instance.trading_node.submit_order(order)

        server_instance.log_info(f"[SubmitMarketOrder] Successfully submitted {instrument_id_str}, CID: {client_order_id.value}")
        return {
            "status": "success",
            "order_id": client_order_id.value,
            "message": "Market order submitted successfully."
        }

    except Exception as e:
        server_instance.log_error(f"[Error][SubmitMarketOrder] Failed for {params.get('instrument_id')}: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Failed to submit market order: {str(e)}"}

def submit_limit_order(server_instance, params: dict) -> dict:
    """
    Submit a limit order to the specified venue.

    Args:
        server_instance: The instance of NautilusMCPServer.
        params: Dictionary containing order details:
            - instrument_id (str): e.g., "BTCUSDT.BINANCE"
            - side (str): "BUY" or "SELL"
            - quantity (str or float): Order quantity
            - price (str or float): Limit price
            - client_order_id (str, optional): Client-provided order ID
            - time_in_force (str, optional): e.g., "GTC", "IOC", "FOK" (default: GTC)

    Returns:
        A dictionary with status, message, and order_id if successful.
    """
    if not server_instance.initialized or not server_instance.trading_node:
        server_instance.log_error("[SubmitLimitOrder] Error: Trading node not initialized.")
        return {"status": "error", "message": "Trading node not initialized."}

    try:
        instrument_id_str = params.get("instrument_id")
        side_str = params.get("side")
        quantity_str = params.get("quantity")
        price_str = params.get("price")
        client_order_id_str = params.get("client_order_id")
        time_in_force_str = params.get("time_in_force", "GTC") # Default to GTC

        # Basic validation
        if not all([instrument_id_str, side_str, quantity_str, price_str]):
            return {"status": "error", "message": "Missing required parameters (instrument_id, side, quantity, price)"}

        server_instance.log_info(f"[SubmitLimitOrder] Attempting for {instrument_id_str}, Side: {side_str}, Qty: {quantity_str}, Price: {price_str}, TIF: {time_in_force_str}")

        # Convert parameters to Nautilus types
        from nautilus_trader.model.identifiers import InstrumentId, ClientOrderId
        from nautilus_trader.model.orders import LimitOrder
        from nautilus_trader.model.enums import OrderSide, TimeInForce
        from nautilus_trader.model.objects import Quantity, Price
        import time
        from decimal import Decimal

        instrument_id = InstrumentId.from_str(instrument_id_str)
        side = OrderSide.BUY if side_str.upper() == "BUY" else OrderSide.SELL

        # Use Decimal for quantity and price
        try:
            quantity = Quantity(Decimal(str(quantity_str)))
            price = Price(Decimal(str(price_str)))
        except Exception as num_err:
            return {"status": "error", "message": f"Invalid quantity/price format: Qty='{quantity_str}', Price='{price_str}'. Error: {num_err}"}

        # Convert TimeInForce string to enum
        try:
            time_in_force = TimeInForce[time_in_force_str.upper()]
        except KeyError:
            valid_tifs = ", ".join(tif.name for tif in TimeInForce)
            return {"status": "error", "message": f"Invalid time_in_force: '{time_in_force_str}'. Valid options: {valid_tifs}"}

        # Generate Client Order ID if needed
        if client_order_id_str:
            client_order_id = ClientOrderId(client_order_id_str)
        else:
            client_order_id = ClientOrderId(f"mcp-L-{instrument_id.symbol}-{int(time.time()*1000)}")

        # Create the LimitOrder object
        order = LimitOrder(
            trader_id=server_instance.trading_node.trader_id,
            strategy_id=server_instance.trading_node.default_strategy_id,
            instrument_id=instrument_id,
            client_order_id=client_order_id,
            order_side=side,
            quantity=quantity,
            limit_price=price,
            time_in_force=time_in_force
        )

        # Submit the order
        server_instance.trading_node.submit_order(order)

        server_instance.log_info(f"[SubmitLimitOrder] Successfully submitted {instrument_id_str}, CID: {client_order_id.value}")
        return {
            "status": "success",
            "order_id": client_order_id.value,
            "message": "Limit order submitted successfully."
        }

    except Exception as e:
        server_instance.log_error(f"[Error][SubmitLimitOrder] Failed for {params.get('instrument_id')}: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Failed to submit limit order: {str(e)}"}

def cancel_order(server_instance, params: dict) -> dict:
    """
    Cancel an existing order using its client order ID.

    Args:
        server_instance: The instance of NautilusMCPServer.
        params: Dictionary containing:
            - client_order_id (str): The client ID of the order to cancel.

    Returns:
        A dictionary with status and message.
    """
    if not server_instance.initialized or not server_instance.trading_node:
        server_instance.log_error("[CancelOrder] Error: Trading node not initialized.")
        return {"status": "error", "message": "Trading node not initialized."}

    try:
        client_order_id_str = params.get("client_order_id")

        if not client_order_id_str:
            return {"status": "error", "message": "Missing required parameter: client_order_id"}

        server_instance.log_info(f"[CancelOrder] Attempting to cancel order CID: {client_order_id_str}")

        # Convert parameters to Nautilus types
        from nautilus_trader.model.identifiers import ClientOrderId
        from nautilus_trader.model.orders import CancelOrder

        client_order_id = ClientOrderId(client_order_id_str)

        # Create the CancelOrder command
        # Requires trader_id and default_strategy_id
        cancel_command = CancelOrder(
            trader_id=server_instance.trading_node.trader_id,
            strategy_id=server_instance.trading_node.default_strategy_id, # Use default strategy
            client_order_id=client_order_id
        )

        # Submit the cancellation command
        # Note: Nautilus uses submit_order_command for cancellations
        server_instance.trading_node.submit_order_command(cancel_command)

        server_instance.log_info(f"[CancelOrder] Cancellation request submitted for CID: {client_order_id.value}")
        return {
            "status": "success",
            "message": f"Cancellation request submitted for order {client_order_id.value}"
        }

    except Exception as e:
        server_instance.log_error(f"[Error][CancelOrder] Failed for CID {params.get('client_order_id')}: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Failed to cancel order: {str(e)}"}

def get_account_info(server_instance, params: dict) -> dict:
    """
    Retrieve account balance information for a specific venue.

    Args:
        server_instance: The instance of NautilusMCPServer.
        params: Dictionary containing:
            - venue (str): The name of the venue (e.g., 'BINANCE').

    Returns:
        A dictionary with status and account balance information (or error message).
    """
    if not server_instance.initialized or not server_instance.trading_node:
        server_instance.log_error("[GetAccountInfo] Error: Trading node not initialized.")
        return {"status": "error", "message": "Trading node not initialized."}

    try:
        venue_str = params.get("venue")
        if not venue_str:
            return {"status": "error", "message": "Missing required parameter: venue"}

        venue_name = venue_str.upper()
        server_instance.log_info(f"[GetAccountInfo] Retrieving account info for venue: {venue_name}...")

        # Retrieve account balances using the TradingNode
        # Note: The exact method and return type need verification in Nautilus docs.
        # Assuming a method like `account_balances` exists and returns a list of AccountBalance objects.
        balances = server_instance.trading_node.account_balances(venue=venue_name)

        # Convert balance objects to a serializable format
        balance_list = []
        if balances: # Check if the result is not None or empty
            for balance in balances:
                balance_list.append({
                    "asset": str(balance.asset),
                    "currency": str(balance.currency), # Or relevant asset identifier
                    "total": str(balance.total), # Use str for Decimal
                    "available": str(balance.available), # Use str for Decimal
                    # Add other relevant fields (e.g., locked, last_updated)
                })

        server_instance.log_info(f"[GetAccountInfo] Retrieved {len(balance_list)} balance entries for {venue_name}.")
        return {"status": "success", "account_info": {"balances": balance_list}}

    except AttributeError as ae:
        # Handle case where the method might not exist on the node
        server_instance.log_error(f"[Error][GetAccountInfo] TradingNode might not support 'account_balances' for {venue_name}: {str(ae)}", exc_info=True)
        return {"status": "error", "message": f"Feature potentially not supported or venue not connected properly: {str(ae)}"}
    except Exception as e:
        server_instance.log_error(f"[Error][GetAccountInfo] Failed to retrieve account info for {venue_name}: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Failed to retrieve account info for {venue_name}: {str(e)}"}

def get_positions(server_instance, params: dict) -> dict:
    """
    Retrieve current open positions for a specific venue, optionally filtered by instrument.

    Args:
        server_instance: The instance of NautilusMCPServer.
        params: Dictionary containing:
            - venue (str): The name of the venue (e.g., 'BINANCE').
            - instrument_id (str, optional): Filter by a specific instrument ID.

    Returns:
        A dictionary with status and a list of positions (or error message).
    """
    if not server_instance.initialized or not server_instance.trading_node:
        server_instance.log_error("[GetPositions] Error: Trading node not initialized.")
        return {"status": "error", "message": "Trading node not initialized."}

    try:
        venue_str = params.get("venue")
        instrument_id_str = params.get("instrument_id") # Optional

        if not venue_str:
            return {"status": "error", "message": "Missing required parameter: venue"}

        venue_name = venue_str.upper()
        server_instance.log_info(f"[GetPositions] Retrieving positions for venue: {venue_name}{f' (Instrument: {instrument_id_str})' if instrument_id_str else ''}...")

        # Retrieve positions using the TradingNode
        # Nautilus likely provides a method like `positions` or similar.
        # The filtering might happen via arguments or post-retrieval.
        # Assuming a method `positions` returning a list/dict of Position objects.
        all_positions = server_instance.trading_node.positions(venue=venue_name)

        # Filter if instrument_id is provided
        if instrument_id_str:
            from nautilus_trader.model.identifiers import InstrumentId
            target_instrument_id = InstrumentId.from_str(instrument_id_str)
            # Filter logic depends on how Nautilus returns positions (list vs dict)
            # Assuming list of Position objects with an `instrument_id` attribute:
            filtered_positions = [pos for pos in all_positions if pos.instrument_id == target_instrument_id]
        else:
            filtered_positions = all_positions

        # Convert Position objects to a serializable format
        position_list = []
        if filtered_positions: # Check if the result is not None or empty
            for pos in filtered_positions:
                position_list.append({
                    "instrument_id": str(pos.instrument_id),
                    "quantity": str(pos.quantity), # Use str for Decimal
                    "average_entry_price": str(pos.average_entry_price), # Use str for Decimal/Price
                    "unrealized_pnl": str(pos.unrealized_pnl), # Use str for Decimal
                    "realized_pnl": str(pos.realized_pnl), # Use str for Decimal
                    # Add other relevant fields (e.g., margin, liquidation_price)
                })

        server_instance.log_info(f"[GetPositions] Retrieved {len(position_list)} positions for {venue_name}{f' matching {instrument_id_str}' if instrument_id_str else ''}.")
        return {"status": "success", "positions": position_list}

    except AttributeError as ae:
        server_instance.log_error(f"[Error][GetPositions] TradingNode might not support 'positions' for {venue_name}: {str(ae)}", exc_info=True)
        return {"status": "error", "message": f"Feature potentially not supported or venue not connected properly: {str(ae)}"}
    except Exception as e:
        server_instance.log_error(f"[Error][GetPositions] Failed for {venue_name}: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Failed to retrieve positions for {venue_name}: {str(e)}"}

def get_order_status(server_instance, params: dict) -> dict:
    """
    Retrieve the status of one or more orders using their client order IDs.

    Args:
        server_instance: The instance of NautilusMCPServer.
        params: Dictionary containing:
            - client_order_ids (list[str]): A list of client order IDs to query.

    Returns:
        A dictionary with status and a list/dict of order statuses (or error message).
    """
    if not server_instance.initialized or not server_instance.trading_node:
        server_instance.log_error("[GetOrderStatus] Error: Trading node not initialized.")
        return {"status": "error", "message": "Trading node not initialized."}

    try:
        client_order_ids_list = params.get("client_order_ids")

        if not client_order_ids_list or not isinstance(client_order_ids_list, list):
            return {"status": "error", "message": "Missing or invalid parameter: client_order_ids (must be a list of strings)"}

        server_instance.log_info(f"[GetOrderStatus] Retrieving status for {len(client_order_ids_list)} order(s): {client_order_ids_list}")

        from nautilus_trader.model.identifiers import ClientOrderId

        # Convert string IDs to ClientOrderId objects
        client_order_ids = [ClientOrderId(cid) for cid in client_order_ids_list]

        # Retrieve order statuses using the TradingNode
        # Note: Verify the exact method in Nautilus. It might return Order objects or specific status objects.
        # Assuming a method `orders` or `order_status` that accepts a list of CIDs.
        # The return type might be a list or dict keyed by CID.
        # For simplicity, assume it returns a list of Order objects matching the CIDs.
        queried_orders = server_instance.trading_node.orders(client_order_ids=client_order_ids)

        # Convert Order objects to a serializable format
        order_status_list = []
        if queried_orders: # Check if the result is not None or empty
            for order in queried_orders:
                order_status_list.append({
                    "client_order_id": str(order.client_order_id),
                    "server_order_id": str(order.server_order_id) if order.server_order_id else None,
                    "instrument_id": str(order.instrument_id),
                    "side": order.order_side.name,
                    "type": order.order_type.name,
                    "status": order.order_status.name, # e.g., ACCEPTED, FILLED, CANCELED
                    "quantity": str(order.quantity),
                    "price": str(order.limit_price) if hasattr(order, 'limit_price') else None, # For limit orders
                    "filled_quantity": str(order.filled_quantity),
                    "average_filled_price": str(order.average_filled_price) if order.average_filled_price is not None else None,
                    "created_ts": order.ts_created,
                    "updated_ts": order.ts_updated,
                    # Add other relevant fields (e.g., time_in_force, reason for rejection/cancel)
                })

        # Handle orders not found? Nautilus might return fewer orders than requested.
        found_ids = {status["client_order_id"] for status in order_status_list}
        not_found_ids = [cid for cid in client_order_ids_list if cid not in found_ids]
        if not_found_ids:
            server_instance.log_warning(f"[GetOrderStatus] Could not find status for CIDs: {not_found_ids}")
            # Optionally add a note about missing orders in the response

        server_instance.log_info(f"[GetOrderStatus] Retrieved status for {len(order_status_list)} order(s).")
        return {"status": "success", "order_statuses": order_status_list}

    except AttributeError as ae:
        server_instance.log_error(f"[Error][GetOrderStatus] TradingNode might not support querying orders: {str(ae)}", exc_info=True)
        return {"status": "error", "message": f"Feature potentially not supported: {str(ae)}"}
    except Exception as e:
        server_instance.log_error(f"[Error][GetOrderStatus] Failed for CIDs {params.get('client_order_ids')}: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Failed to retrieve order status: {str(e)}"}

# --- End of Trading Tools ---
