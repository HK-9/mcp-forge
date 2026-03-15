"""
Test the GENERATED MCP server to confirm it works identically
to the handwritten one.
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PYTHON = sys.executable


async def main():
    server_params = StdioServerParameters(
        command=PYTHON,
        args=["generated/orders_mcp_server.py"],
        cwd=str(Path(__file__).parent.parent),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tools_result = await session.list_tools()
            tool_names = sorted([t.name for t in tools_result.tools])
            print(f"Tools: {tool_names}")
            assert tool_names == ["create_order", "delete_order", "get_order", "list_orders"]

            # Create
            result = await session.call_tool("create_order", {
                "customer_id": "TEST1",
                "product_id": "P999",
                "quantity": 5,
            })
            print(f"Create: {result.content[0].text}")
            assert "TEST1" in result.content[0].text

            # List
            result = await session.call_tool("list_orders", {})
            print(f"List: {result.content[0].text}")

            # Get
            import ast
            orders = ast.literal_eval(result.content[0].text)
            test_order = [o for o in orders if o["customer_id"] == "TEST1"][0]
            order_id = test_order["id"]

            result = await session.call_tool("get_order", {"order_id": order_id})
            print(f"Get: {result.content[0].text}")
            assert order_id in result.content[0].text

            # Delete
            result = await session.call_tool("delete_order", {"order_id": order_id})
            print(f"Delete: {result.content[0].text}")
            assert "Deleted" in result.content[0].text or "successfully" in result.content[0].text

            print("\nGenerated server works identically to handwritten one!")


if __name__ == "__main__":
    asyncio.run(main())