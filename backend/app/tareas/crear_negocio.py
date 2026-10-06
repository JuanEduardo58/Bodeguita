"""Da de alta un colmado y su dueño.

Uso: docker compose exec backend python -m app.tareas.crear_negocio
"""

from getpass import getpass

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Negocio, Usuario
from app.schemas.auth import UsuarioCrear


def main() -> None:
    nombre_negocio = input("Nombre del colmado: ").strip()
    if not nombre_negocio:
        raise SystemExit("El nombre del colmado es obligatorio.")
    try:
        datos = UsuarioCrear(
            nombre=input("Nombre del dueño: ").strip(),
            email=input("Correo del dueño: ").strip(),
            password=getpass("Contraseña (mínimo 8): "),
            rol="dueno",
        )
    except ValidationError as e:
        raise SystemExit(f"Datos inválidos:\n{e}") from None

    with SessionLocal() as db:
        negocio = Negocio(nombre=nombre_negocio)
        db.add(negocio)
        db.flush()
        db.add(
            Usuario(
                id_negocio=negocio.id_negocio,
                nombre=datos.nombre,
                email=datos.email.lower(),
                password_hash=hash_password(datos.password),
                rol="dueno",
            )
        )
        try:
            db.commit()
        except IntegrityError:
            raise SystemExit("Ese correo ya está registrado.") from None

    print(f"Listo: '{nombre_negocio}' creado. Ya puedes entrar con {datos.email.lower()}.")


if __name__ == "__main__":
    main()
