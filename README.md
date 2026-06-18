# 🍃 E-Commerce MongoDB

Application e-commerce complète (frontend + backend + MongoDB) réalisée pour le projet
final de la formation MongoDB. Le backend est en **Python / FastAPI**, le frontend est une
**SPA Bootstrap**, et la base de données est un **cluster MongoDB Atlas** (ou MongoDB local / Docker).

## Fonctionnalités

- **Authentification** : inscription, connexion et déconnexion avec JWT + bcrypt
- Gestion des **utilisateurs**, **produits**, **catégories**, **fournisseurs**, **adresses**
- **Panier** d'achat, **commandes**, **paiements** (simulés) et **avis clients**
- Catalogue avec **filtres avancés**, recherche, tri et pagination
- **Tableau de bord** analytique (revenu par catégorie, top produits/clients, stock faible)
- API REST documentée automatiquement (Swagger UI sur `/docs`)

## Architecture

```
Frontend (HTML/JS + Bootstrap)  ->  Backend (FastAPI + PyMongo)  ->  MongoDB (Atlas / local / Docker)
                                       |
                                   JWT Auth (bcrypt + python-jose)
```

## Modèle de données — 10 collections

| Collection      | Rôle                              | Références              |
|-----------------|-----------------------------------|-------------------------|
| `users`         | Clients et admins (+ password_hash) | —                     |
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
- MongoDB — au choix :
  - **Docker** : `docker run -d -p 27017:27017 --name mongodb mongo:7`
  - **MongoDB Atlas** (cluster cloud)
  - **MongoDB local** installé sur la machine

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/Visualstudiocodetest/E-Commerce_MongoDB.git
cd E-Commerce_MongoDB

# 2. Créer le fichier .env à partir du modèle
cp .env.example .env
#    puis éditer .env et renseigner MONGODB_URI + JWT_SECRET

# 3. Environnement virtuel + dépendances
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Fichier `.env`

```env
MONGODB_URI=mongodb://localhost:27017          # Docker / local
# MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority  # Atlas
DB_NAME=ecommerce
JWT_SECRET=change-me-in-production-use-a-real-secret
JWT_EXPIRE_MINUTES=1440
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

## Authentification

Le système d'authentification repose sur **JWT** (JSON Web Tokens) :

| Endpoint              | Méthode | Description                          |
|-----------------------|---------|--------------------------------------|
| `/api/auth/register`  | POST    | Inscription (crée un compte + token) |
| `/api/auth/login`     | POST    | Connexion (vérifie email/mot de passe, retourne un token) |
| `/api/auth/me`        | GET     | Profil de l'utilisateur connecté (nécessite le token) |

- Les mots de passe sont hachés avec **bcrypt** avant stockage
- Le token JWT est valide 24 h par défaut (`JWT_EXPIRE_MINUTES`)
- Le frontend stocke le token dans `localStorage` et l'envoie via le header `Authorization: Bearer <token>`

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
│   │   ├── config.py          # chargement du .env (MongoDB + JWT)
│   │   ├── database.py        # connexion MongoDB
│   │   ├── auth.py            # utilitaires JWT + bcrypt + dependency get_current_user
│   │   ├── utils.py           # sérialisation ObjectId / dates
│   │   └── routers/           # 1 module par domaine
│   │       ├── auth.py        # register, login, me
│   │       ├── users.py       # CRUD utilisateurs
│   │       ├── products.py    # catalogue + filtres
│   │       ├── categories.py  # catégories
│   │       ├── suppliers.py   # fournisseurs
│   │       ├── addresses.py   # adresses
│   │       ├── carts.py       # panier
│   │       ├── orders.py      # commandes
│   │       ├── payments.py    # paiements
│   │       ├── reviews.py     # avis clients
│   │       └── analytics.py   # dashboard / agrégations
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
