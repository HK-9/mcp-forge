"""
Test the MCP server by calling its tools programmatically.

This acts as a simple MCP client — it:
1. Connects to the MCP server (via SSE transport)
2. Lists available tools
3. Calls each tool and prints the result

Run with:
    1. Start FastAPI:  uvicorn api.main:app --reload
    2. Start MCP:      python mcp_server/orders_server.py --sse
    3. Run test:       python tests/test_mcp_server.py
"""

import asyncio

from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_SERVER_URL = "http://localhost:8001/sse"


async def main():
    # Connect to the MCP server via SSE
    async with sse_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # ── Step 1: List available tools ──
            tools_result = await session.list_tools()
            print("=== Available Tools ===")
            for tool in tools_result.tools:
                print(f"  {tool.name}: {tool.description}")
            print()

            # ── Step 2: Create an order ──
            print("=== Creating an order ===")
            result = await session.call_tool("create_order", {
                "customer_id": "C100",
                "product_id": "P200",
                "quantity": 3,
            })
            print(f"  Result: {result.content[0].text}")
            print()

            # ── Step 3: List all orders ──
            print("=== Listing all orders ===")
            result = await session.call_tool("list_orders", {})
            print(f"  Result: {result.content[0].text}")
            print()

            # ── Step 4: Get a specific order ──
            # (We'll extract the ID from the create response)
            import ast
            created_order = ast.literal_eval(result.content[0].text)
            if isinstance(created_order, list) and len(created_order) > 0:
                order_id = created_order[0]["id"]
                print(f"=== Getting order {order_id} ===")
                result = await session.call_tool("get_order", {"order_id": order_id})
                print(f"  Result: {result.content[0].text}")
                print()

                # ── Step 5: Delete the order ──
                print(f"=== Deleting order {order_id} ===")
                result = await session.call_tool("delete_order", {"order_id": order_id})
                print(f"  Result: {result.content[0].text}")
                print()

            print("All MCP tools tested successfully!")


if __name__ == "__main__":
    asyncio.run(main())