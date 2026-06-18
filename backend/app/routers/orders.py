"""Orders endpoints — creates an order plus order_items, decrements stock, and joins via $lookup."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import require_admin
from ..database import get_db
from ..utils import serialize, to_object_id

router = APIRouter(prefix="/orders", tags=["orders"])
db = get_db()


class OrderLine(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class OrderIn(BaseModel):
    user_id: str
    address_id: str | None = None
    lines: list[OrderLine]


@router.get("")
def list_orders(user_id: str | None = None, status: str | None = None):
    query: dict = {}
    if user_id:
        query["user_id"] = to_object_id(user_id)
    if status:
        query["status"] = status
    return serialize(list(db.orders.find(query).sort("created_at", -1)))


@router.get("/{order_id}")
def get_order(order_id: str):
    """Order detail joined with user, items and payment."""
    pipeline = [
        {"$match": {"_id": to_object_id(order_id)}},
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user",
            }
        },
        {
            "$lookup": {
                "from": "order_items",
                "localField": "_id",
                "foreignField": "order_id",
                "as": "items",
            }
        },
        {
            "$lookup": {
                "from": "payments",
                "localField": "_id",
                "foreignField": "order_id",
                "as": "payment",
            }
        },
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
        {"$unwind": {"path": "$payment", "preserveNullAndEmptyArrays": True}},
    ]
    docs = list(db.orders.aggregate(pipeline))
    if not docs:
        raise HTTPException(404, "Order not found")
    return serialize(docs[0])


@router.post("", status_code=201)
def create_order(payload: OrderIn):
    """Create an order: validate stock, write order + order_items, decrement stock."""
    user_oid = to_object_id(payload.user_id)
    if not db.users.find_one({"_id": user_oid}):
        raise HTTPException(404, "User not found")

    # Build line items with current prices and validate stock.
    line_docs = []
    total = 0.0
    for line in payload.lines:
        product = db.products.find_one({"_id": to_object_id(line.product_id)})
        if not product:
            raise HTTPException(404, f"Product {line.product_id} not found")
        if product["stock"] < line.quantity:
            raise HTTPException(409, f"Not enough stock for {product['name']}")
        subtotal = product["price"] * line.quantity
        total += subtotal
        line_docs.append(
            {
                "product_id": product["_id"],
                "name": product["name"],
                "unit_price": product["price"],
                "quantity": line.quantity,
                "subtotal": subtotal,
            }
        )

    order_doc = {
        "user_id": user_oid,
        "address_id": to_object_id(payload.address_id) if payload.address_id else None,
        "status": "pending",
        "total": round(total, 2),
        "created_at": datetime.now(timezone.utc),
    }
    order_id = db.orders.insert_one(order_doc).inserted_id

    # Persist the order_items collection (relational-style split) and decrement stock.
    for line in line_docs:
        line["order_id"] = order_id
        db.products.update_one(
            {"_id": line["product_id"]}, {"$inc": {"stock": -line["quantity"]}}
        )
    db.order_items.insert_many(line_docs)

    # Close the user's open cart, if any.
    db.shopping_carts.update_one(
        {"user_id": user_oid, "status": "open"},
        {"$set": {"status": "converted", "converted_at": datetime.now(timezone.utc)}},
    )
    return serialize(db.orders.find_one({"_id": order_id}))


@router.patch("/{order_id}/status", dependencies=[Depends(require_admin)])
def update_status(order_id: str, status: str):
    """Changement de statut d'une commande — réservé aux administrateurs."""
    if status not in {"pending", "paid", "shipped", "delivered", "cancelled"}:
        raise HTTPException(400, "Invalid status")
    result = db.orders.update_one(
        {"_id": to_object_id(order_id)}, {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Order not found")
    return serialize(db.orders.find_one({"_id": to_object_id(order_id)}))
