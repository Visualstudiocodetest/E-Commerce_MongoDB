"""Suppliers CRUD endpoints. Reads are public; writes are admin-only."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_admin
from ..database import get_db
from ..utils import serialize, to_object_id

router = APIRouter(prefix="/suppliers", tags=["suppliers"])
db = get_db()


class SupplierIn(BaseModel):
    name: str
    country: str
    email: str | None = None
    rating: float | None = None


@router.get("")
def list_suppliers(country: str | None = None):
    query = {"country": country} if country else {}
    return serialize(list(db.suppliers.find(query).sort("name", 1)))


@router.get("/{supplier_id}")
def get_supplier(supplier_id: str):
    sup = db.suppliers.find_one({"_id": to_object_id(supplier_id)})
    if not sup:
        raise HTTPException(404, "Supplier not found")
    return serialize(sup)


@router.post("", status_code=201, dependencies=[Depends(require_admin)])
def create_supplier(payload: SupplierIn):
    result = db.suppliers.insert_one(payload.model_dump())
    return serialize(db.suppliers.find_one({"_id": result.inserted_id}))


@router.delete("/{supplier_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_supplier(supplier_id: str):
    result = db.suppliers.delete_one({"_id": to_object_id(supplier_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Supplier not found")
