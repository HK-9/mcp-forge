"""
CDK Stack — deploys the Orders API + MCP Server to Lambda + API Gateway.

Pre-bundle dependencies:
    python infra/bundle.py       # Orders API bundle
    python infra/bundle_mcp.py   # MCP server bundle
Then deploy:
    cd infra && cdk deploy
"""

from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
)
from constructs import Construct


class McpForgeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ──────────────────────────────────────────────
        # 1. Orders REST API (FastAPI on Lambda)
        # ──────────────────────────────────────────────

        # Pre-bundled Lambda package (created by infra/bundle.py)
        bundle_dir = str(Path(__file__).parent.parent / "lambda_bundle")

        orders_lambda = _lambda.Function(
            self,
            "McpForgeOrdersApiLambda",
            function_name="mcp-forge-orders-api",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="api.lambda_handler.handler",
            code=_lambda.Code.from_asset(bundle_dir),
            timeout=Duration.seconds(30),
            memory_size=256,
        )

        orders_api = apigw.LambdaRestApi(
            self,
            "McpForgeOrdersApiGateway",
            rest_api_name="mcp-forge-orders-api",
            handler=orders_lambda,
            proxy=True,
            description="MCP Forge — Orders REST API",
        )

        # ──────────────────────────────────────────────
        # 2. MCP Server (FastMCP on Lambda)
        # ──────────────────────────────────────────────

        # Pre-bundled Lambda package (created by infra/bundle_mcp.py)
        mcp_bundle_dir = str(Path(__file__).parent.parent / "mcp_lambda_bundle")

        mcp_lambda = _lambda.Function(
            self,
            "McpForgeMcpServerLambda",
            function_name="mcp-forge-mcp-server",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="mcp_server.mcp_lambda_handler.handler",
            code=_lambda.Code.from_asset(mcp_bundle_dir),
            timeout=Duration.seconds(60),   # MCP calls chain to the Orders API
            memory_size=512,                 # MCP SDK needs more memory
            environment={
                # Tell the MCP server where the Orders API lives
                "ORDERS_API_URL": orders_api.url.rstrip("/"),
            },
        )

        mcp_api = apigw.LambdaRestApi(
            self,
            "McpForgeMcpServerGateway",
            rest_api_name="mcp-forge-mcp-server",
            handler=mcp_lambda,
            proxy=True,
            description="MCP Forge — MCP Server (Streamable HTTP)",
        )

        # Output the MCP server URL for easy access
        CfnOutput(
            self,
            "McpServerUrl",
            value=f"{mcp_api.url}mcp",
            description="MCP Server endpoint (POST JSON-RPC here)",
        )