from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import get_current_user
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.usuario import Token, UsuarioCreate, UsuarioOut
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# module-level dependency singletons (avoid Depends(...) calls in signatures)
get_db_dep = Depends(get_db)
oauth2_form_dep = Depends()  # for OAuth2PasswordRequestForm
current_user_dep = Depends(get_current_user)


@router.post("/register", response_model=UsuarioOut)
def registrar_usuario(datos: UsuarioCreate, db: Session = get_db_dep):
    existente = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ese correo ya está registrado")

    rol_cajero = db.query(Rol).filter(Rol.nombre == "cajero").first()
    if rol_cajero is None:
        raise HTTPException(
            status_code=500, detail="No existe el rol por defecto 'cajero'"
        )

    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        hashed_password=hash_password(datos.password),
        id_rol=rol_cajero.id_rol,
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.post("/login", response_model=Token)
def iniciar_sesion(
    form_data: OAuth2PasswordRequestForm = oauth2_form_dep, db: Session = get_db_dep
):
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    if not usuario or not verify_password(form_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": usuario.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UsuarioOut)
def usuario_actual(usuario: Usuario = current_user_dep):
    return usuario