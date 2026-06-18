# 🍃 E-Commerce MongoDB

Application e-commerce complète (frontend + backend + MongoDB) réalisée pour le projet
final de la formation MongoDB. Le backend est en **Python / FastAPI**, le frontend est une
**SPA Bootstrap**, et la base de données est un **cluster MongoDB Atlas**.

## Fonctionnalités

- Gestion des **utilisateurs**, **produits**, **catégories**, **fournisseurs**, **adresses**
- **Panier** d'achat, **commandes**, **paiements** (simulés) et **avis clients**
- Catalogue avec **filtres avancés**, recherche, tri et pagination
- **Tableau de bord** analytique (revenu par catégorie, top produits/clients, stock faible)
- API REST documentée automatiquement (Swagger UI sur `/docs`)

## Architecture

```
Frontend (HTML/JS + Bootstrap)  ->  Backend (FastAPI + PyMongo)  ->  MongoDB Atlas
```

## Modèle de données — 10 collections

| Collection      | Rôle                              | Références              |
|-----------------|-----------------------------------|-------------------------|
| `users`         | Clients et admins                 | —                       |
| `categories`    | Catégories de produits            | —                       |
| `suppliers`     | Fournisseurs                      | —                       |
| `products`      | Catalogue                         | category_id, supplier_id|
| `addresses`     | Adresses                          | user_id                 |
| `shopping_carts`| Paniers (items imbriqués)         | user_id, product_id     |
| `orders`        | Commandes                         | user_id                 |
| `order_items`   | Lignes de commande                | order_id, product_id    |
| `payments`      | Paiements (simulation)            | order_id                |
| `reviews`       | Avis clients                      | product_id, user_id     |

## Prérequis

- Python 3.11+
- Un cluster MongoDB Atlas (ou MongoDB local) et sa chaîne de connexion

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/Visualstudiocodetest/E-Commerce_MongoDB.git
cd E-Commerce_MongoDB

# 2. Créer le fichier .env à partir du modèle
cp .env.example .env
#    puis éditer .env et renseigner MONGODB_URI

# 3. Environnement virtuel + dépendances
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Fichier `.env`

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
DB_NAME=ecommerce
```

## Utilisation

```bash
# Depuis la racine du projet, avec le venv activé :

# 1. Peupler la base (10 collections, >= 10 documents chacune, + index)
python backend/seed.py

# 2. (Optionnel) Démonstration de TOUTES les commandes MongoDB du barème
python backend/mongo_demo.py

# 3. Lancer l'application (API + frontend servi sur le même port)
uvicorn app.main:app --reload --app-dir backend
```

- Frontend : http://localhost:8000/
- Documentation API (Swagger) : http://localhost:8000/docs
- Santé / connexion DB : http://localhost:8000/api/health

## Commandes MongoDB couvertes

Le script [`backend/mongo_demo.py`](backend/mongo_demo.py) et le mémo
[`docs/mongodb_queries.md`](docs/mongodb_queries.md) couvrent l'intégralité du barème :

création de base/collections, `insertOne`/`insertMany`, `find`, filtres avancés
(`$gte`, `$lte`, `$in`, `$or`, `$regex`), projections, tri + pagination,
agrégations (`$group`, `$sum`, `$avg`, `$match`, `$project`), jointures `$lookup`
(+ `$unwind`), mises à jour (`$set`, `$inc`, `$push`, upsert), suppressions et indexation.

## Présentation

La présentation est au format **LaTeX Beamer** :
[`presentation/presentation.tex`](presentation/presentation.tex).
Compilable directement sur **Overleaf** (ou via `pdflatex`) pour produire le PDF de soutenance.

## Structure du projet

```
.
├── backend/
│   ├── app/
│   │   ├── main.py            # point d'entrée FastAPI + service du frontend
│   │   ├── config.py          # chargement du .env
│   │   ├── database.py        # connexion MongoDB
│   │   ├── utils.py           # sérialisation ObjectId / dates
│   │   └── routers/           # 1 module par domaine (users, products, orders...)
│   ├── seed.py                # données de test + index
│   ├── mongo_demo.py          # démonstration des commandes MongoDB
│   └── requirements.txt
├── frontend/                  # SPA Bootstrap (index.html, app.js, styles.css)
├── presentation/presentation.tex
├── docs/mongodb_queries.md
├── .env.example
└── README.md
```

## Travail collaboratif

- Dépôt Git partagé, contributions via branches et pull requests.
- Cluster MongoDB Atlas accessible à tous les membres (chaîne de connexion dans `.env`).
