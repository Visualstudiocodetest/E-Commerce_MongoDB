"""Payments endpoints — simulates payment processing for an order."""
import random
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import get_db
from ..utils import serialize, to_object_id

router = APIRouter(prefix="/payments", tags=["payments"])
db = get_db()


class PaymentIn(BaseModel):
    order_id: str
    method: str = "card"  # card | paypal | transfer


@router.get("")
def list_payments(status: str | None = None):
    query = {"status": status} if status else {}
    return serialize(list(db.payments.find(query).sort("created_at", -1)))


@router.post("", status_code=201)
def create_payment(payload: PaymentIn):
    """Simulate a payment: 85% chance of success. Marks the order as paid on success."""
    order = db.orders.find_one({"_id": to_object_id(payload.order_id)})
    if not order:
        raise HTTPException(404, "Order not found")
    if db.payments.find_one({"order_id": order["_id"], "status": "succeeded"}):
        raise HTTPException(409, "Order already paid")

    succeeded = random.random() < 0.85
    payment = {
        "order_id": order["_id"],
        "amount": order["total"],
        "method": payload.method,
        "status": "succeeded" if succeeded else "failed",
        "transaction_ref": f"TX-{random.randint(100000, 999999)}",
        "created_at": datetime.now(timezone.utc),
    }
    payment_id = db.payments.insert_one(payment).inserted_id
    if succeeded:
        db.orders.update_one({"_id": order["_id"]}, {"$set": {"status": "paid"}})
    return serialize(db.payments.find_one({"_id": payment_id}))
