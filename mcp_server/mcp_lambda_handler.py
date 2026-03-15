"""
Lambda handler for the MCP server.

Similar pattern to api/lambda_handler.py, but wraps the MCP server
instead of FastAPI.

How it works:
  1. orders_server_aws.create_mcp_server() builds a fresh FastMCP instance
  2. FastMCP.streamable_http_app() returns a Starlette ASGI app
     with the MCP endpoint at /mcp
  3. Mangum translates API Gateway events <-> ASGI

Why a fresh instance per invocation?
  Mangum runs a full ASGI lifespan cycle per request (startup → handle →
  shutdown). The MCP SessionManager.run() can only be called once per
  instance. Creating a new FastMCP each time ensures a fresh SessionManager.

The MCP client sends POST requests to /mcp with JSON-RPC payloads.
The server responds with SSE events containing tool results.
"""

import logging

from mangum import Mangum
from mcp_server.orders_server_aws import create_mcp_server

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Lambda entry point for the MCP server.

    Creates a fresh FastMCP + Starlette + Mangum stack each invocation
    to avoid the 'run() can only be called once' limitation.
    """
    logger.info("MCP request: %s %s", event.get("httpMethod"), event.get("path"))

    mcp = create_mcp_server()
    app = mcp.streamable_http_app()

    # lifespan="auto" — the MCP session manager initializes during
    # ASGI lifespan startup (task group for async sessions)
    mangum_handler = Mangum(app, lifespan="auto", api_gateway_base_path="/prod")
    return mangum_handler(event, context)
