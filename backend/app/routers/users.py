"""Users CRUD endpoints — demonstrates insert, find, projection, update, delete."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

from ..database import get_db
from ..utils import serialize, to_object_id

router = APIRouter(prefix="/users", tags=["users"])
db = get_db()


class UserIn(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role: str = Field(default="customer", pattern="^(customer|admin)$")
    phone: str | None = None


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: str | None = None


@router.get("")
def list_users(
    role: str | None = None,
    search: str | None = Query(None, description="Match first/last name or email"),
    limit: int = 50,
):
    """List users with an optional role filter and a regex search (projection hides nothing sensitive here)."""
    query: dict = {}
    if role:
        query["role"] = role
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    cursor = db.users.find(query).sort("created_at", -1).limit(limit)
    return serialize(list(cursor))


@router.get("/{user_id}")
def get_user(user_id: str):
    user = db.users.find_one({"_id": to_object_id(user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    return serialize(user)


@router.post("", status_code=201)
def create_user(payload: UserIn):
    if db.users.find_one({"email": payload.email}):
        raise HTTPException(409, "Email already registered")
    doc = payload.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    result = db.users.insert_one(doc)
    return serialize(db.users.find_one({"_id": result.inserted_id}))


@router.patch("/{user_id}")
def update_user(user_id: str, payload: UserUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")
    result = db.users.update_one({"_id": to_object_id(user_id)}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")
    return serialize(db.users.find_one({"_id": to_object_id(user_id)}))


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: str):
    result = db.users.delete_one({"_id": to_object_id(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "User not found")
