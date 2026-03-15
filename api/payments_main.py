"""
FastAPI Payments Service — a second API to test multi-API support.

Run with:
    uvicorn api.payments_main:app --reload --port 8002
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Payments API",
    description="Simple payments service for MCP Platform PoC",
    version="1.0.0",
)

# In-memory store (no DB needed for this simple PoC)
payments_db: dict[str, dict] = {}
_counter = 0


class CreatePaymentRequest(BaseModel):
    order_id: str = Field(..., description="The order this payment is for")
    amount: float = Field(..., gt=0, description="Payment amount")
    method: str = Field(..., description="Payment method (card, bank, wallet)")


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    amount: float
    method: str
    status: str


@app.post("/payments", response_model=PaymentResponse, status_code=201)
def create_payment(request: CreatePaymentRequest):
    """Process a new payment."""
    global _counter
    _counter += 1
    payment_id = f"PAY-{_counter:04d}"
    payment = {
        "id": payment_id,
        "order_id": request.order_id,
        "amount": request.amount,
        "method": request.method,
        "status": "completed",
    }
    payments_db[payment_id] = payment
    return payment


@app.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: str):
    """Get a payment by ID."""
    if payment_id not in payments_db:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payments_db[payment_id]


@app.get("/payments", response_model=list[PaymentResponse])
def list_payments(order_id: str | None = None):
    """List all payments, optionally filtered by order ID."""
    results = list(payments_db.values())
    if order_id:
        results = [p for p in results if p["order_id"] == order_id]
    return results