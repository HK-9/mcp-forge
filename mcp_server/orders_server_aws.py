"""
MCP Server for Orders API — AWS Lambda version.

Differences from the local orders_server.py:
  1. API_BASE comes from the ORDERS_API_URL environment variable
     (pointing to the deployed API Gateway URL)
  2. stateless_http=True — Lambda can't maintain sessions across invocations,
     so each request is handled independently
  3. Uses a factory function create_mcp_server() instead of module-level mcp
     instance, because Mangum runs a full ASGI lifespan cycle per request
     (startup → handle → shutdown). The MCP SessionManager.run() can only
     be called once per instance, so we need a fresh one each time.

The MCP endpoint lives at /mcp (the SDK default).
"""

import os

import httpx
from mcp.server.fastmcp import FastMCP

# In Lambda, this will be the API Gateway URL for the Orders API
# e.g., "https://xk6pd99692.execute-api.ap-southeast-2.amazonaws.com/prod"
API_BASE = os.environ.get("ORDERS_API_URL", "http://localhost:8000")


def create_mcp_server() -> FastMCP:
    """Factory that builds a fresh FastMCP instance with all tools registered.

    Called once per Lambda invocation so the SessionManager is always new.
    """
    mcp = FastMCP(
        name="Orders MCP Server",
        instructions="MCP server that wraps the Orders REST API. Provides tools to manage orders.",
        stateless_http=True,
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

    return mcp
