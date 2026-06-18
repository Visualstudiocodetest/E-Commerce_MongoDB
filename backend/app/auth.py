"""JWT authentication & role-based access control.

Centralise ici toute la règle « qui a le droit de faire quoi » :
- hachage / vérification des mots de passe (bcrypt),
- création et décodage des tokens JWT,
- dépendances FastAPI `get_current_user` (authentifié) et `require_admin`
  (authentifié ET rôle administrateur), à brancher sur les routes sensibles.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET
from .database import get_db
from .utils import serialize, to_object_id

bearer_scheme = HTTPBearer()


# --- mots de passe ---------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# --- tokens ----------------------------------------------------------------
def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


# --- dépendances FastAPI ---------------------------------------------------
def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Décode le token Bearer et renvoie l'utilisateur correspondant.

    Lève 401 si le token est absent, invalide, expiré ou si l'utilisateur n'existe plus.
    """
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user = get_db().users.find_one({"_id": to_object_id(user_id)})
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    user = serialize(user)
    user.pop("password_hash", None)
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """À brancher sur les routes réservées aux administrateurs (rôle == 'admin')."""
    if user.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Action réservée aux administrateurs")
    return user
