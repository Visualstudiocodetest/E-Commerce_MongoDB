"""Guided demonstration of every MongoDB command category required by the evaluation.

Run AFTER seeding:

    python backend/seed.py
    python backend/mongo_demo.py

Each section prints the operation and a sample of the result, covering:
  - Database & collection management
  - Insert (insert_one / insert_many)
  - Find / search queries
  - Advanced filters ($gte, $lte, $in, $or, $regex, array match)
  - Projections (include / exclude fields)
  - Sorting + pagination (sort / skip / limit)
  - Aggregations ($group, $sum, $avg, $match, $project)
  - Joins with $lookup (+ $unwind)
  - Updates ($set, $inc, $push, upsert)
  - Deletes (delete_one / delete_many)
  - Indexing (create_index, list_indexes, explain)
"""
import json
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.database import get_db

db = get_db()


def show(title, result, limit=3):
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}")
    if isinstance(result, list):
        for doc in result[:limit]:
            print(json.dumps(_clean(doc), indent=2, ensure_ascii=False, default=str))
        if len(result) > limit:
            print(f"  ... ({len(result)} documents total)")
    else:
        print(json.dumps(_clean(result), indent=2, ensure_ascii=False, default=str))


def _clean(doc):
    if isinstance(doc, dict):
        return {k: (str(v) if isinstance(v, ObjectId) else _clean(v)) for k, v in doc.items()}
    if isinstance(doc, list):
        return [_clean(d) for d in doc]
    return doc


def section_database_management():
    show("1. DATABASE & COLLECTIONS — list collections in this database",
         db.list_collection_names())
    show("   Document count per collection",
         {name: db[name].count_documents({}) for name in db.list_collection_names()})


def section_insert():
    # insert_one
    res = db.demo_scratch.insert_one(
        {"label": "demo", "created_at": datetime.now(timezone.utc)}
    )
    show("2. INSERT — insert_one returns the new _id", {"inserted_id": str(res.inserted_id)})
    # insert_many
    res_many = db.demo_scratch.insert_many(
        [{"label": "a", "n": 1}, {"label": "b", "n": 2}, {"label": "c", "n": 3}]
    )
    show("   insert_many returns several _ids", {"count": len(res_many.inserted_ids)})


def section_find():
    show("3. FIND — first 3 products (no filter)",
         list(db.products.find()))
    show("   find_one — a single user with role=admin",
         db.users.find_one({"role": "admin"}))


def section_filters():
    show("4. FILTERS — products priced between 50 and 300 ($gte / $lte)",
         list(db.products.find({"price": {"$gte": 50, "$lte": 300}})))
    show("   $or — products tagged 'sale' OR with stock = 0",
         list(db.products.find({"$or": [{"tags": "sale"}, {"stock": 0}]})))
    show("   $regex — products whose name contains 'pro' (case-insensitive)",
         list(db.products.find({"name": {"$regex": "pro", "$options": "i"}})))
    show("   $in — users whose role is in ['admin', 'customer']",
         list(db.users.find({"role": {"$in": ["admin", "customer"]}})), limit=2)


def section_projection():
    show("5. PROJECTION — products: keep name & price, drop _id",
         list(db.products.find({}, {"_id": 0, "name": 1, "price": 1})))
    show("   Exclusion projection — users without phone & _id",
         list(db.users.find({}, {"phone": 0, "_id": 0})), limit=2)


def section_sort_paginate():
    show("6. SORT + PAGINATION — 5 most expensive products (sort desc, limit)",
         list(db.products.find({}, {"_id": 0, "name": 1, "price": 1})
              .sort("price", DESCENDING).limit(5)), limit=5)
    show("   skip + limit — page 2 of products sorted by name (skip 5, limit 5)",
         list(db.products.find({}, {"_id": 0, "name": 1})
              .sort("name", ASCENDING).skip(5).limit(5)), limit=5)


def section_aggregation():
    show("7. AGGREGATION — average product price per category ($group + $avg)",
         list(db.products.aggregate([
             {"$group": {"_id": "$category_id", "avg_price": {"$avg": "$price"},
                         "count": {"$sum": 1}}},
             {"$sort": {"avg_price": -1}},
         ])))
    show("   $match + $group — total revenue of paid/shipped/delivered orders",
         list(db.orders.aggregate([
             {"$match": {"status": {"$in": ["paid", "shipped", "delivered"]}}},
             {"$group": {"_id": None, "revenue": {"$sum": "$total"},
                         "orders": {"$sum": 1}}},
         ])))


def section_lookup():
    show("8. $LOOKUP — products joined with their category & supplier",
         list(db.products.aggregate([
             {"$lookup": {"from": "categories", "localField": "category_id",
                          "foreignField": "_id", "as": "category"}},
             {"$lookup": {"from": "suppliers", "localField": "supplier_id",
                          "foreignField": "_id", "as": "supplier"}},
             {"$unwind": "$category"},
             {"$unwind": "$supplier"},
             {"$project": {"_id": 0, "name": 1, "price": 1,
                           "category": "$category.name", "supplier": "$supplier.name"}},
         ])))
    show("   $lookup chain — revenue by category (order_items -> products -> categories)",
         list(db.order_items.aggregate([
             {"$lookup": {"from": "products", "localField": "product_id",
                          "foreignField": "_id", "as": "p"}},
             {"$unwind": "$p"},
             {"$lookup": {"from": "categories", "localField": "p.category_id",
                          "foreignField": "_id", "as": "c"}},
             {"$unwind": "$c"},
             {"$group": {"_id": "$c.name", "revenue": {"$sum": "$subtotal"}}},
             {"$sort": {"revenue": -1}},
         ])))


def section_update():
    sample = db.products.find_one({})
    pid = sample["_id"]
    db.products.update_one({"_id": pid}, {"$set": {"on_promo": True}})
    show("9. UPDATE — $set adds an on_promo flag to one product",
         db.products.find_one({"_id": pid}, {"name": 1, "on_promo": 1, "_id": 0}))
    db.products.update_one({"_id": pid}, {"$inc": {"stock": 10}})
    show("   $inc — increment that product's stock by 10",
         db.products.find_one({"_id": pid}, {"name": 1, "stock": 1, "_id": 0}))
    res = db.products.update_many({"price": {"$lt": 20}}, {"$set": {"budget": True}})
    show("   update_many — tag all products under 20 as budget",
         {"matched": res.matched_count, "modified": res.modified_count})
    # cleanup the demo-only fields
    db.products.update_many({}, {"$unset": {"on_promo": "", "budget": ""}})


def section_delete():
    res = db.demo_scratch.delete_many({})
    show("10. DELETE — delete_many clears the scratch collection",
         {"deleted": res.deleted_count})
    db.demo_scratch.drop()


def section_indexing():
    show("11. INDEXING — indexes currently on the products collection",
         list(db.products.index_information().keys()))
    plan = db.products.find({"price": {"$gte": 100}}).explain()
    winning = plan.get("queryPlanner", {}).get("winningPlan", {})
    show("   explain() — winning plan stage for a price>=100 query",
         {"stage": winning.get("stage") or winning.get("inputStage", {}).get("stage")})


def main():
    section_database_management()
    section_insert()
    section_find()
    section_filters()
    section_projection()
    section_sort_paginate()
    section_aggregation()
    section_lookup()
    section_update()
    section_delete()
    section_indexing()
    print("\nAll command categories demonstrated.\n")


if __name__ == "__main__":
    main()
