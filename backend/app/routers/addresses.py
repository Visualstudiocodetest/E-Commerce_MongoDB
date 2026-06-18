"""Addresses CRUD endpoints — addresses belong to a user."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import get_db
from ..utils import serialize, to_object_id

router = APIRouter(prefix="/addresses", tags=["addresses"])
db = get_db()


class AddressIn(BaseModel):
    user_id: str
    label: str = "home"
    street: str
    city: str
    zip_code: str
    country: str


@router.get("")
def list_addresses(user_id: str | None = None):
    query = {"user_id": to_object_id(user_id)} if user_id else {}
    return serialize(list(db.addresses.find(query)))


@router.post("", status_code=201)
def create_address(payload: AddressIn):
    doc = payload.model_dump()
    doc["user_id"] = to_object_id(doc["user_id"])
    result = db.addresses.insert_one(doc)
    return serialize(db.addresses.find_one({"_id": result.inserted_id}))


@router.delete("/{address_id}", status_code=204)
def delete_address(address_id: str):
    result = db.addresses.delete_one({"_id": to_object_id(address_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Address not found")
