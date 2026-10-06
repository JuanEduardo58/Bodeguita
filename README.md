# Bodeguita

Sistema para colmados dominicanos: inventario, ventas, fiao (crédito) y avisos de deuda por WhatsApp, pensado para usarse desde el celular. Un mismo despliegue atiende a varios colmados.

| Parte | Tecnología |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (sync), Alembic, PostgreSQL 17 |
| Auth | JWT (PyJWT) + Argon2 (pwdlib), roles `dueno` y `cajero` |
| Frontend | Angular 22 (standalone + signals), Angular Material, PWA |
| WhatsApp | WhatsApp Cloud API de Meta |
| Infra | Docker Compose, GitHub Actions |

## Arrancar con Docker (lo más rápido)

Requisito: Docker Desktop.

```bash
cp .env.example .env
```
Después edita `.env`: cambia `POSTGRES_PASSWORD` (en las dos líneas donde aparece) y pon un `SECRET_KEY` de al menos 32 caracteres.

```bash
docker compose up -d --build
```
Levanta la base de datos, el backend (aplica las migraciones solo) y el frontend.

```bash
docker compose exec backend python -m app.tareas.crear_negocio
```
Crea tu colmado y su dueño. Te pide los datos en la terminal.

- App: http://localhost:8080
- Documentación de la API: http://localhost:8080/api/docs

## Desarrollo local (con recarga automática)

La base de datos corre en Docker y el backend y el frontend en tu máquina. Requisitos: Python 3.12+ y Node 24 LTS.

```bash
docker compose up -d db
```
Solo la base de datos, publicada en `127.0.0.1:55432`. Ese puerto alto evita chocar con un PostgreSQL instalado en tu PC.

**Backend** (desde `backend/`):

```bash
python -m venv .venv
```
En Windows se activa con `.venv\Scripts\activate`; en Mac/Linux, con `source .venv/bin/activate`.

```bash
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend** (desde `frontend/`):

```bash
npm install
npm start
```
Abre http://localhost:4200. Las llamadas a `/api` se reenvían al backend en el puerto 8000 (`proxy.conf.json`).

## Tests y lint

Desde `backend/` (con la BD levantada y migrada):

```bash
ruff check . && ruff format --check . && pytest
```
Cada test corre dentro de una transacción que se deshace al final, así que tu BD queda intacta.

Desde `frontend/`:

```bash
npx ng test --watch=false
```

El CI (`.github/workflows/ci.yml`) corre lo mismo en cada push y PR, y además verifica que haya una sola cabeza de migraciones y que los modelos coincidan con la BD (`alembic check`).

## Estructura

```
backend/
  app/
    core/        configuración, conexión a BD, JWT y contraseñas
    models/      tablas (SQLAlchemy); todo modelo nuevo se importa en models/__init__.py
    schemas/     entrada/salida de la API (Pydantic)
    routers/     endpoints, uno por módulo
    tareas/      scripts de consola (crear_negocio; luego el cron de WhatsApp)
  alembic/       migraciones
  tests/
frontend/
  src/app/
    core/        auth: servicio, interceptor y guard
    paginas/     una carpeta o archivo por pantalla
docs/            modelo de datos, auditoría del código viejo y plan
```

## Reglas del equipo

- **Cada consulta filtra por `usuario.id_negocio`.** Es lo que separa un colmado de otro. Un endpoint sin ese filtro es una fuga de datos.
- **Roles:** `usuario: Annotated[Usuario, requiere_rol("dueno")]` en el endpoint. Ver `app/dependencies.py`.
- **Dinero** en `Numeric(12,2)` y **cantidades** en `Numeric(10,3)` (se vende media libra). Nunca `float`.
- **La lógica de negocio va en `services/`.** El router valida, llama al servicio y responde.
- **Migraciones:** después de cambiar un modelo, corre `alembic revision --autogenerate -m "qué cambió"` sobre `main` actualizado, revisa el archivo generado y avísale al compañero antes del merge.
- El modelo completo está en [`docs/modelo-datos.dbml`](docs/modelo-datos.dbml). Pégalo en dbdiagram.io para verlo como diagrama.
