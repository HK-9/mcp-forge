"""
Database layer — SQLite operations for orders.

This is the lowest layer. It knows nothing about HTTP or APIs.
It just stores and retrieves orders from a SQLite file.
"""

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Database file lives next to this module
DB_PATH = Path(__file__).parent / "orders.db"


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database.

    sqlite3.Row lets us access columns by name (row["id"]) instead of index (row[0]).
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the orders table if it doesn't exist.

    Called once at app startup. Safe to call multiple times.
    """
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id          TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            product_id  TEXT NOT NULL,
            quantity    INTEGER NOT NULL,
            status      TEXT NOT NULL DEFAULT 'pending',
            created_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def create_order(customer_id: str, product_id: str, quantity: int) -> dict:
    """Insert a new order and return it."""
    conn = get_connection()
    order_id = str(uuid.uuid4())[:8]  # Short ID for readability in PoC
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT INTO orders (id, customer_id, product_id, quantity, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (order_id, customer_id, product_id, quantity, "pending", now),
    )
    conn.commit()

    order = get_order(order_id, conn)
    conn.close()
    return order


def get_order(order_id: str, conn: sqlite3.Connection | None = None) -> dict | None:
    """Fetch a single order by ID. Returns None if not found."""
    should_close = conn is None
    if conn is None:
        conn = get_connection()

    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    if should_close:
        conn.close()

    return dict(row) if row else None


def list_orders(customer_id: str | None = None) -> list[dict]:
    """List orders, optionally filtered by customer_id."""
    conn = get_connection()

    if customer_id:
        rows = conn.execute(
            "SELECT * FROM orders WHERE customer_id = ?", (customer_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM orders").fetchall()

    conn.close()
    return [dict(row) for row in rows]


def delete_order(order_id: str) -> bool:
    """Delete an order by ID. Returns True if deleted, False if not found."""
    conn = get_connection()
    cursor = conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
