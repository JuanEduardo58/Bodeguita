import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import engine, get_db
from app.core.security import hash_password
from app.main import app
from app.models import Negocio, Usuario

PASSWORD = "clave-segura-123"


@pytest.fixture
def db():
    """Cada test corre dentro de una transacción que se deshace al final:
    usa la BD ya migrada (`alembic upgrade head`) y la deja intacta."""
    with engine.connect() as conn:
        trans = conn.begin()
        session = Session(bind=conn, join_transaction_mode="create_savepoint")
        yield session
        session.close()
        trans.rollback()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def crear_usuario(db):
    def _crear(email, rol="dueno", activo=True, negocio=None):
        usuario = Usuario(
            negocio=negocio or Negocio(nombre="Colmado de prueba"),
            nombre="Prueba",
            email=email,
            password_hash=hash_password(PASSWORD),
            rol=rol,
            activo=activo,
        )
        db.add(usuario)
        db.flush()
        return usuario

    return _crear


def login(client, email, password=PASSWORD):
    return client.post("/api/auth/login", data={"username": email, "password": password})


def auth_header(client, email):
    return {"Authorization": f"Bearer {login(client, email).json()['access_token']}"}
