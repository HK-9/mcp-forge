"""
FastAPI Orders Service — the REST API layer.

This is the HTTP layer. It:
1. Receives HTTP requests
2. Validates input (via Pydantic models)
3. Calls the database layer
4. Returns JSON responses

Run with:
    uvicorn api.main:app --reload

Then visit:
    http://localhost:8000/docs        ← Swagger UI (interactive API docs)
    http://localhost:8000/openapi.json ← Raw OpenAPI spec (this is what MCP will consume later)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from api.database import create_order, delete_order, get_order, init_db, list_orders
from api.models import CreateOrderRequest, OrderResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup: initialize the database."""
    init_db()
    yield


app = FastAPI(
    title="Orders API",
    description="Simple orders service for MCP Platform PoC",
    version="1.0.0",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────


@app.get("/")
def root():
    """Basic health endpoint for browser checks."""
    return {"service": "orders-api", "status": "ok"}


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order_by_id(order_id: str):
    """Get a single order by its ID."""
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order


@app.get("/orders", response_model=list[OrderResponse])
def list_all_orders(customer_id: str | None = None):
    """List all orders, optionally filtered by customer ID."""
    return list_orders(customer_id)


@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_new_order(request: CreateOrderRequest):
    """Create a new order."""
    order = create_order(
        customer_id=request.customer_id,
        product_id=request.product_id,
        quantity=request.quantity,
    )
    return order


@app.delete("/orders/{order_id}", status_code=204)
def delete_order_by_id(order_id: str):
    """Delete an order by its ID."""
    deleted = delete_order(order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
