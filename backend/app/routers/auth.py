"""Authentication endpoints — register (sign up) and login."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from ..auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..database import get_db
from ..utils import serialize

router = APIRouter(prefix="/auth", tags=["auth"])
db = get_db()


class RegisterIn(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=6)
    phone: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=201)
def register(payload: RegisterIn):
    if db.users.find_one({"email": payload.email}):
        raise HTTPException(409, "Email already registered")
    doc = {
        "first_name": payload.first_name,
        "last_name": payload.last_name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": "customer",
        "phone": payload.phone,
        "created_at": datetime.now(timezone.utc),
    }
    result = db.users.insert_one(doc)
    user = serialize(db.users.find_one({"_id": result.inserted_id}))
    user.pop("password_hash", None)
    return {"user": user, "token": create_access_token(user["_id"])}


@router.post("/login")
def login(payload: LoginIn):
    user = db.users.find_one({"email": payload.email})
    if not user or not user.get("password_hash"):
        raise HTTPException(401, "Invalid email or password")
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    user = serialize(user)
    user.pop("password_hash", None)
    return {"user": user, "token": create_access_token(user["_id"])}


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    current_user.pop("password_hash", None)
    return current_user
