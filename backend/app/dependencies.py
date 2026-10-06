from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

Db = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Db) -> Usuario:
    no_autorizado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión inválida o vencida",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        id_usuario = decode_access_token(token)
    except jwt.InvalidTokenError:
        raise no_autorizado from None

    usuario = db.get(Usuario, id_usuario)
    if usuario is None or not usuario.activo:
        raise no_autorizado
    return usuario


# Todo endpoint de negocio filtra sus consultas por usuario.id_negocio (aislamiento SaaS).
UsuarioActual = Annotated[Usuario, Depends(get_current_user)]


def requiere_rol(*roles: str):
    """Uso: `usuario: Annotated[Usuario, requiere_rol("dueno")]`."""

    def verificar(usuario: UsuarioActual) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permiso para esta acción")
        return usuario

    return Depends(verificar)
