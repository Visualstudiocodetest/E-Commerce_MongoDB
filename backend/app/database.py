"""MongoDB connection helpers shared across the application."""
from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from .config import DB_NAME, MONGODB_URI


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    """Return a singleton MongoClient (cached for the process lifetime)."""
    return MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)


def get_db() -> Database:
    """Return the application database handle."""
    return get_client()[DB_NAME]


# Canonical list of collections used throughout the project (>= 10 collections).
COLLECTIONS = [
    "users",
    "categories",
    "suppliers",
    "products",
    "addresses",
    "shopping_carts",
    "orders",
    "order_items",
    "payments",
    "reviews",
]
