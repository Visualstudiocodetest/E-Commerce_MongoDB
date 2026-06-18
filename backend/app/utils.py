"""Shared helpers for serialising MongoDB documents to JSON-friendly dicts."""
from datetime import datetime, date
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException


def to_object_id(value: str) -> ObjectId:
    """Convert a string into an ObjectId or raise a clean 400 error."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid id: {value!r}")


def serialize(doc: Any) -> Any:
    """Recursively turn ObjectId / datetime values into JSON-safe types."""
    if isinstance(doc, list):
        return [serialize(item) for item in doc]
    if isinstance(doc, dict):
        return {key: serialize(val) for key, val in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, (datetime, date)):
        return doc.isoformat()
    return doc
