"""
Pydantic models — define the shape of requests and responses.

These are NOT database models. They're contracts:
- What the client sends (CreateOrderRequest)
- What the server returns (OrderResponse)

FastAPI uses these to:
1. Validate incoming JSON automatically
2. Generate OpenAPI schema automatically
"""

from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    """What the client sends when creating an order."""

    customer_id: str = Field(..., example="C100", description="Customer identifier")
    product_id: str = Field(..., example="P100", description="Product identifier")
    quantity: int = Field(..., gt=0, example=2, description="Number of items to order")


class OrderResponse(BaseModel):
    """What the server returns for an order."""

    id: str
    customer_id: str
    product_id: str
    quantity: int
    status: str
    created_at: str
