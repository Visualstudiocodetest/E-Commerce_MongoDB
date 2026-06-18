"""Analytics endpoints — complex aggregation pipelines for the dashboard."""
from fastapi import APIRouter

from ..database import get_db
from ..utils import serialize

router = APIRouter(prefix="/analytics", tags=["analytics"])
db = get_db()


@router.get("/revenue-by-category")
def revenue_by_category():
    """Total revenue grouped by category — joins order_items -> products -> categories."""
    pipeline = [
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "_id",
                "as": "product",
            }
        },
        {"$unwind": "$product"},
        {
            "$lookup": {
                "from": "categories",
                "localField": "product.category_id",
                "foreignField": "_id",
                "as": "category",
            }
        },
        {"$unwind": "$category"},
        {
            "$group": {
                "_id": "$category.name",
                "revenue": {"$sum": "$subtotal"},
                "units_sold": {"$sum": "$quantity"},
            }
        },
        {"$project": {"_id": 0, "category": "$_id", "revenue": {"$round": ["$revenue", 2]}, "units_sold": 1}},
        {"$sort": {"revenue": -1}},
    ]
    return serialize(list(db.order_items.aggregate(pipeline)))


@router.get("/top-products")
def top_products(limit: int = 5):
    """Best-selling products by units sold."""
    pipeline = [
        {
            "$group": {
                "_id": "$product_id",
                "name": {"$first": "$name"},
                "units_sold": {"$sum": "$quantity"},
                "revenue": {"$sum": "$subtotal"},
            }
        },
        {"$sort": {"units_sold": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "product_id": "$_id", "name": 1, "units_sold": 1, "revenue": {"$round": ["$revenue", 2]}}},
    ]
    return serialize(list(db.order_items.aggregate(pipeline)))


@router.get("/top-customers")
def top_customers(limit: int = 5):
    """Customers ranked by total amount spent on paid/shipped/delivered orders."""
    pipeline = [
        {"$match": {"status": {"$in": ["paid", "shipped", "delivered"]}}},
        {
            "$group": {
                "_id": "$user_id",
                "orders": {"$sum": 1},
                "spent": {"$sum": "$total"},
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user",
            }
        },
        {"$unwind": "$user"},
        {
            "$project": {
                "_id": 0,
                "user_id": "$_id",
                "name": {"$concat": ["$user.first_name", " ", "$user.last_name"]},
                "email": "$user.email",
                "orders": 1,
                "spent": {"$round": ["$spent", 2]},
            }
        },
        {"$sort": {"spent": -1}},
        {"$limit": limit},
    ]
    return serialize(list(db.orders.aggregate(pipeline)))


@router.get("/orders-by-status")
def orders_by_status():
    """Count and revenue grouped by order status."""
    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "revenue": {"$sum": "$total"},
            }
        },
        {"$project": {"_id": 0, "status": "$_id", "count": 1, "revenue": {"$round": ["$revenue", 2]}}},
        {"$sort": {"count": -1}},
    ]
    return serialize(list(db.orders.aggregate(pipeline)))


@router.get("/low-stock")
def low_stock(threshold: int = 15):
    """Products at or below a stock threshold — joined with supplier for reordering."""
    pipeline = [
        {"$match": {"stock": {"$lte": threshold}}},
        {
            "$lookup": {
                "from": "suppliers",
                "localField": "supplier_id",
                "foreignField": "_id",
                "as": "supplier",
            }
        },
        {"$unwind": "$supplier"},
        {"$project": {"name": 1, "stock": 1, "supplier": "$supplier.name", "_id": 0}},
        {"$sort": {"stock": 1}},
    ]
    return serialize(list(db.products.aggregate(pipeline)))


@router.get("/summary")
def summary():
    """Headline KPI counts for the dashboard."""
    return {
        "users": db.users.count_documents({}),
        "products": db.products.count_documents({}),
        "categories": db.categories.count_documents({}),
        "orders": db.orders.count_documents({}),
        "reviews": db.reviews.count_documents({}),
        "revenue": round(
            next(
                iter(
                    db.orders.aggregate(
                        [
                            {"$match": {"status": {"$in": ["paid", "shipped", "delivered"]}}},
                            {"$group": {"_id": None, "total": {"$sum": "$total"}}},
                        ]
                    )
                ),
                {"total": 0},
            )["total"],
            2,
        ),
    }
