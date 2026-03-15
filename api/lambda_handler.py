"""
Lambda handler — wraps the FastAPI app for AWS Lambda.

Mangum translates between:
  - API Gateway's event format (what Lambda receives)
  - ASGI (what FastAPI speaks)

This file is the Lambda entry point. It imports the same FastAPI app
you've been running locally.
"""

import logging

from mangum import Mangum
from api.main import app
from api.database import init_db

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_mangum = Mangum(app, lifespan="off", api_gateway_base_path="/prod")


def handler(event, context):
    """Lambda entry point."""
    # Ensure table exists for each invocation in Lambda (/tmp can be ephemeral)
    init_db()
    return _mangum(event, context)