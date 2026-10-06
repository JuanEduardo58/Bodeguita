from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

ALGORITMO = "HS256"
password_hash = PasswordHash.recommended()  # Argon2


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(id_usuario: int) -> str:
    expira = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(id_usuario), "exp": expira}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITMO)


def decode_access_token(token: str) -> int:
    """Devuelve el id del usuario. Lanza jwt.InvalidTokenError si el token no sirve."""
    payload = jwt.decode(
        token, settings.secret_key, algorithms=[ALGORITMO], options={"require": ["exp", "sub"]}
    )
    return int(payload["sub"])
