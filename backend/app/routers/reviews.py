"""Reviews endpoints — customer reviews per product, with rating aggregation."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth import require_admin
from ..database import get_db
from ..utils import serialize, to_object_id

router = APIRouter(prefix="/reviews", tags=["reviews"])
db = get_db()


class ReviewIn(BaseModel):
    product_id: str
    user_id: str
    rating: int = Field(ge=1, le=5)
    title: str | None = None
    comment: str | None = None


@router.get("")
def list_reviews(product_id: str | None = None, min_rating: int | None = None):
    query: dict = {}
    if product_id:
        query["product_id"] = to_object_id(product_id)
    if min_rating is not None:
        query["rating"] = {"$gte": min_rating}
    return serialize(list(db.reviews.find(query).sort("created_at", -1)))


@router.get("/stats")
def rating_stats():
    """Average rating and count per product via an aggregation pipeline + $lookup for names."""
    pipeline = [
        {
            "$group": {
                "_id": "$product_id",
                "avg_rating": {"$avg": "$rating"},
                "review_count": {"$sum": 1},
            }
        },
        {
            "$lookup": {
                "from": "products",
                "localField": "_id",
                "foreignField": "_id",
                "as": "product",
            }
        },
        {"$unwind": "$product"},
        {
            "$project": {
                "_id": 0,
                "product_id": "$_id",
                "product_name": "$product.name",
                "avg_rating": {"$round": ["$avg_rating", 2]},
                "review_count": 1,
            }
        },
        {"$sort": {"avg_rating": -1}},
    ]
    return serialize(list(db.reviews.aggregate(pipeline)))


@router.post("", status_code=201)
def create_review(payload: ReviewIn):
    doc = payload.model_dump()
    doc["product_id"] = to_object_id(doc["product_id"])
    doc["user_id"] = to_object_id(doc["user_id"])
    doc["created_at"] = datetime.now(timezone.utc)
    result = db.reviews.insert_one(doc)
    return serialize(db.reviews.find_one({"_id": result.inserted_id}))


@router.delete("/{review_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_review(review_id: str):
    """Suppression d'un avis (modération) — réservée aux administrateurs."""
    result = db.reviews.delete_one({"_id": to_object_id(review_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Review not found")
