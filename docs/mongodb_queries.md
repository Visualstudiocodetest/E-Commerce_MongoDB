# Mémo des commandes MongoDB (mongosh)

Toutes les commandes ci-dessous correspondent au barème d'évaluation. Elles sont
exécutables dans `mongosh` (ou MongoDB Compass) après avoir sélectionné la base :

```js
use ecommerce
```

---

## 1. Bases de données & collections

```js
show dbs                     // lister les bases
use ecommerce                // créer / sélectionner la base
show collections             // lister les collections
db.products.countDocuments() // nombre de documents
db.createCollection("logs")  // créer une collection explicitement
```

## 2. Insertion

```js
db.users.insertOne({ first_name: "Ada", last_name: "Lovelace", email: "ada@ex.io", role: "customer" })

db.categories.insertMany([
  { name: "Electronics", slug: "electronics" },
  { name: "Books", slug: "books" }
])
```

## 3. Recherche (find)

```js
db.products.find()                         // tous les produits
db.products.find({ stock: 0 })             // égalité
db.users.findOne({ role: "admin" })        // un seul document
```

## 4. Filtres avancés

```js
db.products.find({ price: { $gte: 50, $lte: 300 } })          // intervalle
db.products.find({ stock: { $gt: 0 } })                       // supérieur à
db.users.find({ role: { $in: ["admin", "customer"] } })       // appartenance
db.products.find({ $or: [ { tags: "sale" }, { stock: 0 } ] }) // OU logique
db.products.find({ tags: "premium" })                         // élément d'un tableau
db.products.find({ name: { $regex: "pro", $options: "i" } })  // texte (regex)
```

## 5. Projections

```js
db.products.find({}, { _id: 0, name: 1, price: 1 })   // inclure name + price
db.users.find({}, { phone: 0 })                       // exclure phone
```

## 6. Tri & pagination

```js
db.products.find().sort({ price: -1 })                // tri décroissant
db.products.find().sort({ name: 1 }).skip(5).limit(5) // page 2 (5 par page)
```

## 7. Agrégations

```js
// Prix moyen et nombre de produits par catégorie
db.products.aggregate([
  { $group: { _id: "$category_id", avg_price: { $avg: "$price" }, count: { $sum: 1 } } },
  { $sort: { avg_price: -1 } }
])

// Chiffre d'affaires des commandes payées/expédiées/livrées
db.orders.aggregate([
  { $match: { status: { $in: ["paid", "shipped", "delivered"] } } },
  { $group: { _id: null, revenue: { $sum: "$total" }, orders: { $sum: 1 } } }
])
```

## 8. Jointures avec $lookup

```js
// Produits enrichis de leur catégorie et fournisseur
db.products.aggregate([
  { $lookup: { from: "categories", localField: "category_id", foreignField: "_id", as: "category" } },
  { $lookup: { from: "suppliers",  localField: "supplier_id", foreignField: "_id", as: "supplier" } },
  { $unwind: "$category" },
  { $unwind: "$supplier" },
  { $project: { _id: 0, name: 1, price: 1, category: "$category.name", supplier: "$supplier.name" } }
])

// Revenu par catégorie (double jointure : order_items -> products -> categories)
db.order_items.aggregate([
  { $lookup: { from: "products",   localField: "product_id",   foreignField: "_id", as: "p" } },
  { $unwind: "$p" },
  { $lookup: { from: "categories", localField: "p.category_id", foreignField: "_id", as: "c" } },
  { $unwind: "$c" },
  { $group: { _id: "$c.name", revenue: { $sum: "$subtotal" } } },
  { $sort: { revenue: -1 } }
])
```

## 9. Mise à jour

```js
db.products.updateOne({ _id: id }, { $set: { on_promo: true } })   // modifier un champ
db.products.updateOne({ _id: id }, { $inc: { stock: 10 } })        // incrémenter
db.products.updateMany({ price: { $lt: 20 } }, { $set: { budget: true } })
db.shopping_carts.updateOne({ user_id: u }, { $push: { items: { product_id: p, quantity: 1 } } })
db.shopping_carts.updateOne({ user_id: u }, { $pull: { items: { product_id: p } } })
db.carts.updateOne({ user_id: u }, { $setOnInsert: { status: "open" } }, { upsert: true })
```

## 10. Suppression

```js
db.reviews.deleteOne({ _id: id })   // supprimer un document
db.logs.deleteMany({})              // vider une collection
db.logs.drop()                      // supprimer la collection entière
```

## 11. Indexation

```js
db.users.createIndex({ email: 1 }, { unique: true })          // index unique
db.products.createIndex({ category_id: 1 })                   // index simple
db.products.createIndex({ name: "text", description: "text" }) // index texte
db.orders.createIndex({ user_id: 1, created_at: -1 })         // index composé
db.products.getIndexes()                                       // lister les index
db.products.find({ price: { $gte: 100 } }).explain("executionStats") // plan d'exécution
```
