"""
Handwritten MCP Server for the Orders API.

This is a MANUAL implementation — we're hardcoding 4 tools that map to our 4 API endpoints.
Later (Task 9), we'll auto-generate this from the OpenAPI spec.

The MCP server does 3 things:
  1. Register tools (name, description, input schema)
  2. Handle tool calls (receive args, make HTTP request to the API)
  3. Return results (send the API response back to the client)

Run with:
    python mcp_server/orders_server.py
"""

import httpx
from mcp.server.fastmcp import FastMCP

# The base URL of our running REST API
API_BASE = "http://localhost:8000"

# Create the MCP server instance
# Port 8001 so it doesn't conflict with FastAPI on 8000
mcp = FastMCP(
    name="Orders MCP Server",
    instructions="MCP server that wraps the Orders REST API. Provides tools to manage orders.",
    host="127.0.0.1",
    port=8001,
)


# ──────────────────────────────────────────────
# Tool 1: get_order
# ──────────────────────────────────────────────
@mcp.tool()
def get_order(order_id: str) -> str:
    """Get a single order by its ID."""
    response = httpx.get(f"{API_BASE}/orders/{order_id}")
    if response.status_code == 200:
        return str(response.json())
    return f"Error {response.status_code}: {response.text}"


# ──────────────────────────────────────────────
# Tool 2: list_orders
# ──────────────────────────────────────────────
@mcp.tool()
def list_orders(customer_id: str | None = None) -> str:
    """List all orders, optionally filtered by customer ID."""
    params = {}
    if customer_id:
        params["customer_id"] = customer_id
    response = httpx.get(f"{API_BASE}/orders", params=params)
    return str(response.json())


# ──────────────────────────────────────────────
# Tool 3: create_order
# ──────────────────────────────────────────────
@mcp.tool()
def create_order(customer_id: str, product_id: str, quantity: int) -> str:
    """Create a new order."""
    response = httpx.post(
        f"{API_BASE}/orders",
        json={
            "customer_id": customer_id,
            "product_id": product_id,
            "quantity": quantity,
        },
    )
    if response.status_code == 201:
        return str(response.json())
    return f"Error {response.status_code}: {response.text}"


# ──────────────────────────────────────────────
# Tool 4: delete_order
# ──────────────────────────────────────────────
@mcp.tool()
def delete_order(order_id: str) -> str:
    """Delete an order by its ID."""
    response = httpx.delete(f"{API_BASE}/orders/{order_id}")
    if response.status_code == 204:
        return "Order deleted successfully"
    return f"Error {response.status_code}: {response.text}"


# ──────────────────────────────────────────────
# Start the server
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if "--sse" in sys.argv:
        # SSE transport: runs as an HTTP server (for Inspector and HTTP clients)
        mcp.run(transport="sse")
    else:
        # Default: stdio transport (for MCP clients like Claude Desktop)
        mcp.run()