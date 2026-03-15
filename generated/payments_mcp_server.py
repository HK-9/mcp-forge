"""
Auto-generated MCP Server for Payments MCP Server.
"""

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = "http://localhost:8002"

mcp = FastMCP(
    name="Payments MCP Server",
    host="127.0.0.1",
    port=8003,
)



@mcp.tool()
def create_payment(order_id: str, amount: str, method: str) -> str:
    """Create Payment"""
    response = httpx.post(
        f"{API_BASE}/payments",
        json={"order_id": order_id, "amount": amount, "method": method},
    )
    if response.status_code == 201:
        return str(response.json())
    return f"Error {response.status_code}: {response.text}"


@mcp.tool()
def list_payments(order_id: str | None = None) -> str:
    """List Payments"""
    params = {}
    if order_id is not None:
        params["order_id"] = order_id
    response = httpx.get(f"{API_BASE}/payments", params=params)
    if response.status_code == 200:
        return str(response.json())
    return f"Error {response.status_code}: {response.text}"


@mcp.tool()
def get_payment(payment_id: str) -> str:
    """Get Payment"""
    response = httpx.get(f"{API_BASE}/payments/{payment_id}")
    if response.status_code == 200:
        return str(response.json())
    return f"Error {response.status_code}: {response.text}"


if __name__ == "__main__":
    mcp.run()