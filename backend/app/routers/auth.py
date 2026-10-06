from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import Db, UsuarioActual, requiere_rol
from app.models import Usuario
from app.schemas.auth import Token, UsuarioCrear, UsuarioOut

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: Db):
    email = form.username.strip().lower()
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    if (
        usuario is None
        or not usuario.activo
        or not verify_password(form.password, usuario.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(usuario.id_usuario))


@router.get("/me", response_model=UsuarioOut)
def usuario_actual(usuario: UsuarioActual):
    return usuario


@router.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear_usuario(datos: UsuarioCrear, dueno: Annotated[Usuario, requiere_rol("dueno")], db: Db):
    """El dueño crea cajeros (u otro dueño) para su propio colmado."""
    usuario = Usuario(
        id_negocio=dueno.id_negocio,
        nombre=datos.nombre,
        email=datos.email.lower(),
        password_hash=hash_password(datos.password),
        rol=datos.rol,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese correo ya está registrado") from None
    db.refresh(usuario)
    return usuario
