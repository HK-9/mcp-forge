"""
MCP Gateway — aggregates tools from multiple OpenAPI specs into one MCP server.

Instead of running one MCP server per API, the gateway combines all tools
from all registered APIs into a single server.

Usage:
    python gateway/gateway_server.py
"""

import sys
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

# Add parser to path
sys.path.insert(0, str(Path(__file__).parent.parent / "parser"))
from openapi_parser import parse_openapi
from tool_generator import generate_tools, ToolDefinition

mcp = FastMCP(
    name="MCP Gateway",
    instructions="Unified gateway providing tools from multiple APIs.",
    host="127.0.0.1",
    port=9000,
)

# ── Registry: which APIs are registered ──
REGISTERED_APIS: list[dict] = [
    {
        "name": "orders",
        "spec_path": "specs/orders.yaml",
        "api_base": "http://localhost:8000",
    },
    {
        "name": "payments",
        "spec_path": "specs/payments.yaml",
        "api_base": "http://localhost:8002",
    },
]


def _make_tool_caller(tool: ToolDefinition, api_base: str):
    """Create a function that calls the correct API endpoint for a tool.

    We need this factory because Python closures capture variables by reference.
    Without it, all tools would use the last tool/api_base from the loop.
    """

    def call_tool(**kwargs) -> str:
        path = tool.path
        method = tool.method

        # Separate params by location
        path_params = {p.name: kwargs[p.name] for p in tool.parameters if p.location == "path" and p.name in kwargs}
        query_params = {p.name: kwargs[p.name] for p in tool.parameters if p.location == "query" and p.name in kwargs and kwargs[p.name] is not None}
        body_params = {p.name: kwargs[p.name] for p in tool.parameters if p.location == "body" and p.name in kwargs}

        # Fill path parameters
        for name, value in path_params.items():
            path = path.replace(f"{{{name}}}", str(value))

        url = f"{api_base}{path}"

        # Make the HTTP request
        if method == "GET":
            response = httpx.get(url, params=query_params)
        elif method == "POST":
            response = httpx.post(url, json=body_params)
        elif method == "PUT":
            response = httpx.put(url, json=body_params)
        elif method == "PATCH":
            response = httpx.patch(url, json=body_params)
        elif method == "DELETE":
            response = httpx.delete(url)
        else:
            return f"Unsupported method: {method}"

        if response.status_code in (200, 201):
            return str(response.json())
        elif response.status_code == 204:
            return "Deleted successfully"
        else:
            return f"Error {response.status_code}: {response.text}"

    # Set function metadata for MCP
    call_tool.__name__ = tool.name
    call_tool.__doc__ = tool.description

    # Build type annotations for MCP to discover parameters
    annotations = {}
    for p in tool.parameters:
        py_type = int if p.param_type == "integer" else float if p.param_type == "number" else str
        if not p.required:
            py_type = py_type | None
        annotations[p.name] = py_type
    annotations["return"] = str
    call_tool.__annotations__ = annotations

    # Set defaults for optional params
    import types
    defaults = tuple(None for p in tool.parameters if not p.required)
    if defaults:
        call_tool.__defaults__ = defaults

    return call_tool


def register_apis():
    """Parse all registered API specs and register their tools with the gateway."""
    for api_config in REGISTERED_APIS:
        name = api_config["name"]
        spec_path = api_config["spec_path"]
        api_base = api_config["api_base"]

        print(f"Registering API: {name} ({spec_path})")
        endpoints = parse_openapi(spec_path)
        tools = generate_tools(endpoints)

        for tool in tools:
            # Prefix tool name with API name to avoid collisions
            # e.g., "orders_get_order", "payments_create_payment"
            tool.name = f"{name}_{tool.name}"

            caller = _make_tool_caller(tool, api_base)
            mcp.tool()(caller)
            print(f"  Registered tool: {tool.name}")


# Register all APIs at import time
register_apis()


if __name__ == "__main__":
    print("\nStarting MCP Gateway on port 9000...")
    mcp.run()