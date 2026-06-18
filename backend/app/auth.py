"""Lightweight role-based access control.

Le projet ne dispose pas d'un système de login (pas de mot de passe / JWT) :
le frontend simule la session via un sélecteur d'utilisateur. On formalise
cette simulation côté API en exigeant un header `X-User-Id` sur les routes
sensibles, puis on vérifie le rôle de l'utilisateur correspondant en base.

Ça reste volontairement simple (pas de token signé), mais ça centralise la
règle "qui a le droit de faire quoi" dans un seul endroit réutilisable par
tous les routers, plutôt que de la dupliquer dans chaque endpoint.
"""


"""JWT authentication utilities and FastAPI dependency."""
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET
from .database import get_db
from .utils import serialize, to_object_id

bearer_scheme = HTTPBearer()

from fastapi import Depends, Header, HTTPException

from .database import get_db
from .utils import to_object_id

db = get_db()


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dépendance à brancher sur les routes réservées aux admins."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Action réservée aux administrateurs")
    return user


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = get_db().users.find_one({"_id": to_object_id(user_id)})
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return serialize(user)
