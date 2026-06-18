"""Shopping cart endpoints — one open cart per user, items stored as embedded array."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..database import get_db
from ..utils import serialize, to_object_id

router = APIRouter(prefix="/carts", tags=["carts"])
db = get_db()


class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, default=1)


def _cart_with_products(user_oid):
    """Return the user's cart enriched with product details via $lookup."""
    pipeline = [
        {"$match": {"user_id": user_oid, "status": "open"}},
        {"$unwind": {"path": "$items", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "products",
                "localField": "items.product_id",
                "foreignField": "_id",
                "as": "product",
            }
        },
        {"$unwind": {"path": "$product", "preserveNullAndEmptyArrays": True}},
        {
            "$group": {
                "_id": "$_id",
                "user_id": {"$first": "$user_id"},
                "status": {"$first": "$status"},
                "items": {
                    "$push": {
                        "product_id": "$items.product_id",
                        "name": "$product.name",
                        "price": "$product.price",
                        "quantity": "$items.quantity",
                        "subtotal": {"$multiply": ["$product.price", "$items.quantity"]},
                    }
                },
            }
        },
        {"$addFields": {"total": {"$sum": "$items.subtotal"}}},
    ]
    docs = list(db.shopping_carts.aggregate(pipeline))
    return docs[0] if docs else None


@router.get("/{user_id}")
def get_cart(user_id: str):
    user_oid = to_object_id(user_id)
    cart = _cart_with_products(user_oid)
    if not cart:
        raise HTTPException(404, "No open cart for this user")
    return serialize(cart)


@router.post("/{user_id}/items")
def add_item(user_id: str, item: CartItem):
    """Upsert the open cart and push/merge the item.

    Uses upsert + $setOnInsert to create the cart on first use.
    """
    user_oid = to_object_id(user_id)
    product_oid = to_object_id(item.product_id)
    if not db.products.find_one({"_id": product_oid}):
        raise HTTPException(404, "Product not found")

    db.shopping_carts.update_one(
        {"user_id": user_oid, "status": "open"},
        {
            "$setOnInsert": {
                "user_id": user_oid,
                "status": "open",
                "created_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )
    # If the product is already in the cart, bump the quantity; otherwise push it.
    updated = db.shopping_carts.update_one(
        {"user_id": user_oid, "status": "open", "items.product_id": product_oid},
        {"$inc": {"items.$.quantity": item.quantity}},
    )
    if updated.modified_count == 0:
        db.shopping_carts.update_one(
            {"user_id": user_oid, "status": "open"},
            {"$push": {"items": {"product_id": product_oid, "quantity": item.quantity}}},
        )
    return serialize(_cart_with_products(user_oid))


@router.delete("/{user_id}/items/{product_id}")
def remove_item(user_id: str, product_id: str):
    """Pull an item out of the cart with $pull."""
    user_oid = to_object_id(user_id)
    db.shopping_carts.update_one(
        {"user_id": user_oid, "status": "open"},
        {"$pull": {"items": {"product_id": to_object_id(product_id)}}},
    )
    return serialize(_cart_with_products(user_oid))
