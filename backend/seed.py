"""Seed the MongoDB database with coherent, related sample data.

Run from the project root (with .env present and the virtualenv active):

    python backend/seed.py

Creates >= 10 collections, each with >= 10 documents, and builds indexes.
Demonstrates: drop, insert_one, insert_many, create_index, $inc updates.
"""
import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from pymongo import ASCENDING, DESCENDING, TEXT

from app.auth import hash_password
from app.database import COLLECTIONS, get_db

fake = Faker()
Faker.seed(42)
random.seed(42)

db = get_db()
NOW = datetime.now(timezone.utc)

# Mot de passe par défaut des comptes de test (admin + clients) pour le login JWT.
DEFAULT_PASSWORD = "password123"
DEFAULT_PASSWORD_HASH = hash_password(DEFAULT_PASSWORD)


def reset():
    """Drop every project collection for a clean reseed (idempotent)."""
    for name in COLLECTIONS:
        db[name].drop()
    print(f"Dropped {len(COLLECTIONS)} collections.")


def seed_categories():
    names = [
        ("Electronics", "Phones, laptops and gadgets"),
        ("Books", "Paperbacks, hardcovers and e-books"),
        ("Clothing", "Men, women and kids apparel"),
        ("Home & Kitchen", "Furniture, decor and appliances"),
        ("Sports", "Fitness, outdoor and team sports"),
        ("Toys & Games", "For all ages"),
        ("Beauty", "Skincare, makeup and fragrances"),
        ("Grocery", "Food and beverages"),
        ("Automotive", "Car parts and accessories"),
        ("Garden", "Plants, tools and outdoor living"),
    ]
    docs = [
        {"name": n, "slug": n.lower().replace(" & ", "-").replace(" ", "-"), "description": d}
        for n, d in names
    ]
    ids = db.categories.insert_many(docs).inserted_ids
    print(f"Inserted {len(ids)} categories.")
    return ids


def seed_suppliers():
    countries = ["Switzerland", "Germany", "France", "Italy", "USA", "China", "Japan", "Spain", "UK", "Netherlands"]
    docs = [
        {
            "name": fake.company(),
            "country": country,
            "email": fake.company_email(),
            "rating": round(random.uniform(3.0, 5.0), 1),
        }
        for country in countries
    ]
    ids = db.suppliers.insert_many(docs).inserted_ids
    print(f"Inserted {len(ids)} suppliers.")
    return ids


def seed_users():
    docs = []
    # One admin + 13 customers = 14 users.
    docs.append(
        {
            "first_name": "Alexandre",
            "last_name": "Admin",
            "email": "admin@shop.io",
            "role": "admin",
            "password_hash": DEFAULT_PASSWORD_HASH,
            "phone": fake.phone_number(),
            "created_at": NOW - timedelta(days=400),
        }
    )
    for _ in range(13):
        first, last = fake.first_name(), fake.last_name()
        docs.append(
            {
                "first_name": first,
                "last_name": last,
                "email": f"{first.lower()}.{last.lower()}@example.com",
                "role": "customer",
                "password_hash": DEFAULT_PASSWORD_HASH,
                "phone": fake.phone_number(),
                "created_at": NOW - timedelta(days=random.randint(1, 365)),
            }
        )
    ids = db.users.insert_many(docs).inserted_ids
    print(f"Inserted {len(ids)} users.")
    return ids


def seed_addresses(user_ids):
    docs = []
    for uid in user_ids:
        for label in random.sample(["home", "work", "billing"], k=random.randint(1, 2)):
            docs.append(
                {
                    "user_id": uid,
                    "label": label,
                    "street": fake.street_address(),
                    "city": fake.city(),
                    "zip_code": fake.postcode(),
                    "country": fake.country(),
                }
            )
    ids = db.addresses.insert_many(docs).inserted_ids
    print(f"Inserted {len(ids)} addresses.")
    return ids


PRODUCT_CATALOG = {
    "Electronics": ["Smartphone X12", "UltraBook Pro 14", "Noise-Cancel Headphones", "4K Action Cam", "Smartwatch Fit"],
    "Books": ["The MongoDB Handbook", "Clean Python", "Distributed Systems 101", "The Art of Indexing"],
    "Clothing": ["Merino Wool Sweater", "Running Jacket", "Classic Denim Jeans", "Cotton T-Shirt"],
    "Home & Kitchen": ["Espresso Machine", "Cast-Iron Skillet", "Robot Vacuum", "Standing Desk"],
    "Sports": ["Yoga Mat Pro", "Carbon Road Bike", "Adjustable Dumbbells"],
    "Toys & Games": ["Strategy Board Game", "Building Blocks 500pc"],
    "Beauty": ["Vitamin C Serum", "Eau de Parfum 50ml"],
    "Grocery": ["Organic Coffee Beans 1kg", "Dark Chocolate Box"],
    "Automotive": ["Dash Cam HD"],
    "Garden": ["Cordless Hedge Trimmer"],
}


def seed_products(category_ids, supplier_ids):
    cat_by_name = {}
    for cid in category_ids:
        cat = db.categories.find_one({"_id": cid})
        cat_by_name[cat["name"]] = cid

    tag_pool = ["new", "sale", "popular", "eco", "premium", "limited", "bestseller"]
    docs = []
    for cat_name, products in PRODUCT_CATALOG.items():
        for pname in products:
            docs.append(
                {
                    "name": pname,
                    "description": fake.sentence(nb_words=12),
                    "price": round(random.uniform(9.9, 1499.0), 2),
                    "stock": random.randint(0, 120),
                    "category_id": cat_by_name[cat_name],
                    "supplier_id": random.choice(supplier_ids),
                    "tags": random.sample(tag_pool, k=random.randint(1, 3)),
                    "created_at": NOW - timedelta(days=random.randint(1, 300)),
                }
            )
    ids = db.products.insert_many(docs).inserted_ids
    print(f"Inserted {len(ids)} products.")
    return ids


def seed_carts(user_ids, product_ids):
    docs = []
    for uid in random.sample(user_ids, k=10):
        items = [
            {"product_id": pid, "quantity": random.randint(1, 4)}
            for pid in random.sample(product_ids, k=random.randint(1, 3))
        ]
        docs.append(
            {
                "user_id": uid,
                "status": "open",
                "items": items,
                "created_at": NOW - timedelta(days=random.randint(0, 20)),
            }
        )
    ids = db.shopping_carts.insert_many(docs).inserted_ids
    print(f"Inserted {len(ids)} shopping carts.")
    return ids


def seed_orders(user_ids, product_ids):
    statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
    order_ids = []
    all_items = []
    for _ in range(18):
        uid = random.choice(user_ids)
        chosen = random.sample(product_ids, k=random.randint(1, 4))
        lines = []
        total = 0.0
        for pid in chosen:
            product = db.products.find_one({"_id": pid})
            qty = random.randint(1, 3)
            subtotal = round(product["price"] * qty, 2)
            total += subtotal
            lines.append(
                {
                    "product_id": pid,
                    "name": product["name"],
                    "unit_price": product["price"],
                    "quantity": qty,
                    "subtotal": subtotal,
                }
            )
        created = NOW - timedelta(days=random.randint(0, 120))
        order_id = db.orders.insert_one(
            {
                "user_id": uid,
                "status": random.choice(statuses),
                "total": round(total, 2),
                "created_at": created,
            }
        ).inserted_id
        order_ids.append(order_id)
        for line in lines:
            line["order_id"] = order_id
            all_items.append(line)
    db.order_items.insert_many(all_items)
    print(f"Inserted {len(order_ids)} orders and {len(all_items)} order items.")
    return order_ids


def seed_payments(order_ids):
    methods = ["card", "paypal", "transfer"]
    docs = []
    for oid in order_ids:
        order = db.orders.find_one({"_id": oid})
        if order["status"] == "pending":
            continue  # pending orders are not yet paid
        status = "failed" if order["status"] == "cancelled" else "succeeded"
        docs.append(
            {
                "order_id": oid,
                "amount": order["total"],
                "method": random.choice(methods),
                "status": status,
                "transaction_ref": f"TX-{random.randint(100000, 999999)}",
                "created_at": order["created_at"] + timedelta(minutes=5),
            }
        )
    if docs:
        db.payments.insert_many(docs)
    print(f"Inserted {len(docs)} payments.")


def seed_reviews(user_ids, product_ids):
    docs = []
    for pid in product_ids:
        for uid in random.sample(user_ids, k=random.randint(1, 4)):
            docs.append(
                {
                    "product_id": pid,
                    "user_id": uid,
                    "rating": random.randint(1, 5),
                    "title": fake.sentence(nb_words=4),
                    "comment": fake.paragraph(nb_sentences=2),
                    "created_at": NOW - timedelta(days=random.randint(0, 200)),
                }
            )
    ids = db.reviews.insert_many(docs).inserted_ids
    print(f"Inserted {len(ids)} reviews.")


def build_indexes():
    """Create indexes to speed up the common queries (and demonstrate indexing)."""
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.categories.create_index([("slug", ASCENDING)], unique=True)
    db.products.create_index([("category_id", ASCENDING)])
    db.products.create_index([("price", ASCENDING)])
    db.products.create_index([("name", TEXT), ("description", TEXT)])
    db.orders.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.order_items.create_index([("order_id", ASCENDING)])
    db.order_items.create_index([("product_id", ASCENDING)])
    db.reviews.create_index([("product_id", ASCENDING)])
    db.payments.create_index([("order_id", ASCENDING)])
    print("Created indexes on key collections.")


def main():
    print(f"Seeding database '{db.name}' ...")
    reset()
    category_ids = seed_categories()
    supplier_ids = seed_suppliers()
    user_ids = seed_users()
    seed_addresses(user_ids)
    product_ids = seed_products(category_ids, supplier_ids)
    seed_carts(user_ids, product_ids)
    order_ids = seed_orders(user_ids, product_ids)
    seed_payments(order_ids)
    seed_reviews(user_ids, product_ids)
    build_indexes()
    print("\nSeed complete. Document counts:")
    for name in COLLECTIONS:
        print(f"  {name:16} {db[name].count_documents({}):>4}")
    print("\nComptes de test (mot de passe commun) :")
    print(f"  admin     : admin@shop.io / {DEFAULT_PASSWORD}")
    print(f"  clients   : <prenom>.<nom>@example.com / {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    main()
