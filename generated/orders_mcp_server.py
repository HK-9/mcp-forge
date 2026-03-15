"""
Auto-generated MCP Server for Orders MCP Server. using Jinja2 template and the OpenAPI spec from specs/orders.yaml.
"""

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = "http://localhost:8000"

mcp = FastMCP(
    name="Orders MCP Server",
    host="127.0.0.1",
    port=8001,
)



@mcp.tool()
def get_order(order_id: str) -> str:
    """Get Order By Id"""
    response = httpx.get(f"{API_BASE}/orders/{order_id}")
    if response.status_code == 200:
        return str(response.json())
    return f"Error {response.status_code}: {response.text}"


@mcp.tool()
def delete_order(order_id: str) -> str:
    """Delete Order By Id"""
    response = httpx.delete(f"{API_BASE}/orders/{order_id}")
    if response.status_code == 204:
        return "Deleted successfully"
    return f"Error {response.status_code}: {response.text}"


@mcp.tool()
def list_orders(customer_id: str | None = None) -> str:
    """List All Orders"""
    params = {}
    if customer_id is not None:
        params["customer_id"] = customer_id
    response = httpx.get(f"{API_BASE}/orders", params=params)
    if response.status_code == 200:
        return str(response.json())
    return f"Error {response.status_code}: {response.text}"


@mcp.tool()
def create_order(customer_id: str, product_id: str, quantity: int) -> str:
    """Create New Order"""
    response = httpx.post(
        f"{API_BASE}/orders",
        json={"customer_id": customer_id, "product_id": product_id, "quantity": quantity},
    )
    if response.status_code == 201:
        return str(response.json())
    return f"Error {response.status_code}: {response.text}"


if __name__ == "__main__":
    mcp.run()