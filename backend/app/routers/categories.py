"""Categories CRUD endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import get_db
from ..utils import serialize, to_object_id

router = APIRouter(prefix="/categories", tags=["categories"])
db = get_db()


class CategoryIn(BaseModel):
    name: str
    slug: str
    description: str | None = None


@router.get("")
def list_categories():
    return serialize(list(db.categories.find().sort("name", 1)))


@router.get("/{category_id}")
def get_category(category_id: str):
    cat = db.categories.find_one({"_id": to_object_id(category_id)})
    if not cat:
        raise HTTPException(404, "Category not found")
    return serialize(cat)


@router.post("", status_code=201)
def create_category(payload: CategoryIn):
    if db.categories.find_one({"slug": payload.slug}):
        raise HTTPException(409, "Slug already exists")
    result = db.categories.insert_one(payload.model_dump())
    return serialize(db.categories.find_one({"_id": result.inserted_id}))


@router.patch("/{category_id}")
def update_category(category_id: str, payload: CategoryIn):
    result = db.categories.update_one(
        {"_id": to_object_id(category_id)}, {"$set": payload.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Category not found")
    return serialize(db.categories.find_one({"_id": to_object_id(category_id)}))


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: str):
    result = db.categories.delete_one({"_id": to_object_id(category_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Category not found")
