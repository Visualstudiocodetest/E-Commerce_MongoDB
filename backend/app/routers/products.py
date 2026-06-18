"""Products endpoints — showcases advanced filters, projections, sorting and $lookup joins."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import get_db
from ..utils import serialize, to_object_id

router = APIRouter(prefix="/products", tags=["products"])
db = get_db()


class ProductIn(BaseModel):
    name: str
    description: str | None = None
    price: float = Field(gt=0)
    stock: int = Field(ge=0, default=0)
    category_id: str
    supplier_id: str
    tags: list[str] = []


@router.get("")
def list_products(
    search: str | None = Query(None, description="Text search on name/description"),
    category_id: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock: bool | None = None,
    tag: str | None = None,
    sort_by: str = Query("name", pattern="^(name|price|stock|created_at|rating_avg)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    skip: int = 0,
    limit: int = 24,
):
    """Filtered + sorted + paginated product listing.

    Demonstrates: range filters ($gte/$lte), $regex text search, $in/array match,
    projection, sort and skip/limit pagination.
    """
    query: dict = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]
    if category_id:
        query["category_id"] = to_object_id(category_id)
    if tag:
        query["tags"] = tag  # matches if `tag` is an element of the tags array
    price_filter: dict = {}
    if min_price is not None:
        price_filter["$gte"] = min_price
    if max_price is not None:
        price_filter["$lte"] = max_price
    if price_filter:
        query["price"] = price_filter
    if in_stock is True:
        query["stock"] = {"$gt": 0}
    elif in_stock is False:
        query["stock"] = {"$lte": 0}

    direction = 1 if order == "asc" else -1
    cursor = (
        db.products.find(query)
        .sort(sort_by, direction)
        .skip(skip)
        .limit(limit)
    )
    return {
        "total": db.products.count_documents(query),
        "items": serialize(list(cursor)),
    }


@router.get("/{product_id}")
def get_product(product_id: str):
    """Single product enriched with its category, supplier and reviews via $lookup."""
    pipeline = [
        {"$match": {"_id": to_object_id(product_id)}},
        {
            "$lookup": {
                "from": "categories",
                "localField": "category_id",
                "foreignField": "_id",
                "as": "category",
            }
        },
        {
            "$lookup": {
                "from": "suppliers",
                "localField": "supplier_id",
                "foreignField": "_id",
                "as": "supplier",
            }
        },
        {
            "$lookup": {
                "from": "reviews",
                "localField": "_id",
                "foreignField": "product_id",
                "as": "reviews",
            }
        },
        {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
        {"$unwind": {"path": "$supplier", "preserveNullAndEmptyArrays": True}},
        {
            "$addFields": {
                "review_count": {"$size": "$reviews"},
                "rating_avg": {"$avg": "$reviews.rating"},
            }
        },
    ]
    docs = list(db.products.aggregate(pipeline))
    if not docs:
        raise HTTPException(404, "Product not found")
    return serialize(docs[0])


@router.post("", status_code=201)
def create_product(payload: ProductIn):
    doc = payload.model_dump()
    doc["category_id"] = to_object_id(doc["category_id"])
    doc["supplier_id"] = to_object_id(doc["supplier_id"])
    doc["created_at"] = datetime.now(timezone.utc)
    result = db.products.insert_one(doc)
    return serialize(db.products.find_one({"_id": result.inserted_id}))


@router.patch("/{product_id}")
def update_product(product_id: str, payload: dict):
    """Partial update. Casts category_id/supplier_id to ObjectId when present."""
    allowed = {"name", "description", "price", "stock", "tags", "category_id", "supplier_id"}
    updates = {k: v for k, v in payload.items() if k in allowed}
    for key in ("category_id", "supplier_id"):
        if key in updates:
            updates[key] = to_object_id(updates[key])
    if not updates:
        raise HTTPException(400, "No valid fields to update")
    result = db.products.update_one({"_id": to_object_id(product_id)}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(404, "Product not found")
    return serialize(db.products.find_one({"_id": to_object_id(product_id)}))


@router.post("/{product_id}/restock")
def restock(product_id: str, amount: int = Query(..., gt=0)):
    """Atomic stock increment using $inc."""
    result = db.products.update_one(
        {"_id": to_object_id(product_id)}, {"$inc": {"stock": amount}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Product not found")
    return serialize(db.products.find_one({"_id": to_object_id(product_id)}))


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: str):
    result = db.products.delete_one({"_id": to_object_id(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Product not found")
