"""Lightweight role-based access control.

Le projet ne dispose pas d'un système de login (pas de mot de passe / JWT) :
le frontend simule la session via un sélecteur d'utilisateur. On formalise
cette simulation côté API en exigeant un header `X-User-Id` sur les routes
sensibles, puis on vérifie le rôle de l'utilisateur correspondant en base.

Ça reste volontairement simple (pas de token signé), mais ça centralise la
règle "qui a le droit de faire quoi" dans un seul endroit réutilisable par
tous les routers, plutôt que de la dupliquer dans chaque endpoint.
"""
from fastapi import Depends, Header, HTTPException

from .database import get_db
from .utils import to_object_id

db = get_db()


def get_current_user(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> dict:
    """Résout l'utilisateur "courant" à partir du header X-User-Id."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Header X-User-Id manquant")
    user = db.users.find_one({"_id": to_object_id(x_user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur inconnu")
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dépendance à brancher sur les routes réservées aux admins."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Action réservée aux administrateurs")
    return user
