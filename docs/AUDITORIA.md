# Auditoría del repositorio Bodeguita (código heredado de SysCol)

> **Histórico.** Describe el código viejo de SysCol, que se borró el 2026-10-05 al arrancar desde cero. El plan vigente está en [`PLAN.md`](PLAN.md).

Fecha: 2026-10-05 · Commit auditado: `ce701aa` (rama `main`) · Alcance: repo completo, todos los archivos abiertos.

## Resumen ejecutivo

1. El repo solo tiene implementado **login/registro JWT** y la tabla de usuarios/roles. Inventario, Ventas, Fiao, WhatsApp y Reportes son **archivos vacíos** (17 archivos de 0 bytes).
2. **No hay frontend**: 4 archivos vacíos, sin `package.json` ni proyecto Angular.
3. **El CI está roto**: `ruff` falla por un `import *` y `pytest` falla al importar la app porque faltan variables de entorno.
4. **El "Cómo empezar" no funciona de cero**: `docker compose up` no arranca porque las variables de Postgres no se definen donde compose las busca.
5. **Dependencias con vulnerabilidades conocidas**: starlette (arrastrada por fastapi 0.115.0), python-multipart, python-jose y python-dotenv.
6. **Seguridad de auth incompleta**: el registro es público, no se verifica ningún rol, los usuarios desactivados pueden entrar y no hay forma de crear un admin.
7. **El modelo de datos tiene tres versiones que no coinciden**: el DBML, los modelos SQLAlchemy y las migraciones. Falta definir multi-negocio (SaaS) y las cantidades por peso.
8. **No hay secretos commiteados** en ninguna versión del historial ✅.
9. El historial de git es un solo commit inicial más 2 commits de README. El último commit **borró el README** (−282 líneas).
10. **Veredicto**: vale rescatar la configuración base, la auth (corregida), Alembic, Docker y el DBML. El resto se construye nuevo, siguiendo `PLAN-MIGRACION.md`.

> Convenciones: **Hecho** = lo observado en el código. **Recomendación** = opinión del auditor.
> ⚠️ **Requiere aviso al equipo** = cambia el modelo de datos base que usan los 4 integrantes.

---

## 1. Inventario del repo

### 1.1 Estructura real vs. objetivo

| Ruta objetivo | Estado real |
|---|---|
| `backend/app/core/` | ✅ `config.py`, `database.py`, `security.py` con contenido |
| `backend/app/models/` | ⚠️ Solo `rol.py` y `usuario.py`. `cliente.py`, `deuda.py`, `producto.py` y `venta.py` están **vacíos** |
| `backend/app/schemas/` | ⚠️ Solo `usuario.py`. `cliente.py`, `producto.py` y `venta.py` están **vacíos** |
| `backend/app/routers/` | ⚠️ Solo `auth.py`. `fiao`, `inventario`, `reportes`, `ventas` y `whatsapp` están **vacíos** y no están registrados en `main.py` |
| `backend/app/services/` | ❌ `reportes_service.py` y `whatsapp_service.py` están **vacíos** |
| `backend/alembic/` | ✅ 2 migraciones (usuarios, roles) |
| `backend/test/` | ⚠️ 1 test (`/health`) |
| `frontend/src/app/{inventario,ventas,fiao,reportes}/` | ❌ No existen. Solo hay `app.routes.ts`, `core/auth.service.ts`, `core/auth.interceptor.ts` y `Dockerfile`, **los 4 vacíos** |
| `docs/modelo-datos.dbml` | ✅ 13 tablas, más el diagrama PNG exportado de dbdiagram.io |
| `docker-compose.yml` | ⚠️ Solo `db` y `backend`, sin servicio de frontend |

### 1.2 Versiones exactas declaradas

| Archivo | Pieza | Versión |
|---|---|---|
| `backend/requirements.txt` | fastapi | 0.115.0 (obliga a starlette `>=0.37.2,<0.39.0`) |
| | uvicorn[standard] | 0.30.6 |
| | sqlalchemy | 2.0.35 |
| | alembic | 1.13.2 |
| | psycopg2-binary | 2.9.9 |
| | pydantic / pydantic-settings | 2.9.2 / 2.5.2 |
| | python-jose[cryptography] | 3.3.0 |
| | passlib[bcrypt] / bcrypt | 1.7.4 / 4.0.1 |
| | python-multipart | 0.0.9 |
| | python-dotenv | 1.0.1 |
| | pytest, httpx, ruff | **sin versión fijada** |
| `backend/Dockerfile` | imagen base | `python:3.12-slim` |
| `docker-compose.yml` | base de datos | `postgres:16` |
| `.github/workflows/ci.yml` | acciones | `actions/checkout@v4`, `actions/setup-python@v5`, Python 3.12 |
| `package.json` | — | **no existe** |

### 1.3 Historial de git

| Commit | Fecha | Autor | Qué hizo |
|---|---|---|---|
| `3525bd0` | 2026-10-05 | Juan Eduardo Monagas Fernandez | "first commit": sube **todo** el código de una vez |
| `68ad22d` | 2026-10-05 | Taida (Mayoixv) | Cambia el título del README de "SysCol" a "ColMaster" |
| `ce701aa` | 2026-10-05 | Taida (Mayoixv) | "Translate README from Spanish to English": en realidad **borra 282 líneas** y deja solo `# ColMaster` |

- **Ramas:** solo `main`. El CI apunta también a `develop`, que no existe.
- **Hecho:** las migraciones tienen fechas del 26 y 28 de julio de 2026. El trabajo previo se hizo en otro repo y se subió aplastado, así que **no hay historial de quién hizo qué**.
- **Hecho:** el proyecto tiene tres nombres: `SysCol API` (`backend/app/main.py:4`), `ColMaster` (`README.md:1`) y `Bodeguita` (nombre del repo).

---

## 2. Hallazgos

### 🔴 Críticos

#### C1. CI rojo: el lint falla
- **Hecho:** `backend/alembic/env.py:6` tiene `from app.models import *`. Ruff, con sus reglas por defecto (que incluyen `F`), reporta **F403** y el job `lint` termina con error. Como `tests` tiene `needs: lint`, tampoco corre. No hay `pyproject.toml` ni `ruff.toml` que excluya `alembic/`.
- **Recomendación:** cambiar a `import app.models  # noqa: F401`, o excluir `alembic/versions` y usar un import explícito.

#### C2. CI rojo: los tests no pueden importar la app
- **Hecho:** `backend/app/core/config.py:11-12` declara `database_url` y `secret_key` sin valor por defecto, y `Settings()` se instancia al importar (`config.py:21`). En CI no hay `.env` (está en `.gitignore:151`) ni `env:` en el workflow. `test/test_health.py:1` importa `app.main`, así que la recolección de tests falla con `ValidationError`.
- **Recomendación:** definir `env:` en el job (`DATABASE_URL`, `SECRET_KEY` de prueba) y agregar un servicio `postgres` al job para los tests que toquen la BD.

#### C3. `docker compose up` no arranca desde cero
- **Hecho:** `docker-compose.yml:7-9` y `:22` usan `${POSTGRES_USER}`, `${POSTGRES_PASSWORD}`, `${POSTGRES_DB}` y `${DATABASE_URL}`. Compose resuelve esas variables desde un `.env` en la **raíz**, pero el README (versión `68ad22d`) solo manda a copiar `backend/.env.example` a `backend/.env`, y `.env.example` ni siquiera define `POSTGRES_*`.
- **Resultado (deducido, no ejecutado):** Postgres se detiene con "superuser password is not specified". El backend recibe `DATABASE_URL=""`, que tiene prioridad sobre `backend/.env` en pydantic-settings, y falla al crear el engine.
- **Hecho:** los pasos 5 y 6 del README (`npm install`, `ng serve`) no pueden funcionar porque no hay proyecto Angular.
- **Recomendación:** usar `env_file: ./backend/.env` en el servicio `backend`, agregar `POSTGRES_*` al `.env.example` y usar un solo `.env` en la raíz, documentado.

#### C4. Dependencias con vulnerabilidades publicadas (consulta OSV, 2026-10-05)

| Paquete fijado | Avisos en OSV | Ejemplos |
|---|---|---|
| starlette 0.38.x (vía `fastapi==0.115.0`) | 14 | GHSA-f96h-pmfr-66vw (DoS multipart), GHSA-2c2j-9gv5-cj73 |
| python-multipart 0.0.9 | 16 | GHSA-59g5-xgcq-4qw3 (DoS por boundary malformado) |
| python-jose 3.3.0 | 6 | PYSEC-2024-232/233 (confusión de algoritmo, bomba JWE) |
| ecdsa (dependencia de python-jose) | 4 | GHSA-wj6h-64fc-37mp (timing attack, **sin parche**) |
| python-dotenv 1.0.1 | 2 | GHSA-mf9w-mj56-hr94 |

- **Recomendación:** actualizar fastapi y python-multipart, y cambiar python-jose por PyJWT (detalle en `EVALUACION-TECNOLOGIAS.md`). Agregar `pip-audit` o Dependabot.

#### C5. Registro público sin control y sin forma de crear un administrador
- **Hecho:** `backend/app/routers/auth.py:19-40`: `POST /auth/register` no requiere token. Cualquiera en internet puede crear una cuenta, que siempre recibe el rol `cajero` (`auth.py:25`).
- **Hecho:** ningún endpoint ni script asigna `admin` o `dueno`. La migración `c4574fa9da3b` siembra los roles, pero no un usuario admin.
- **Recomendación:** que el registro de usuarios lo haga solo `admin`/`dueno`, y crear el primer admin con un script de CLI que lea el email y la clave de variables de entorno.

#### C6. Los roles no se verifican en ningún endpoint y los usuarios inactivos pueden entrar
- **Hecho:** `backend/app/dependencies.py:16-37` solo valida el token. No hay ninguna dependencia de rol en todo el código.
- **Hecho:** `auth.py:47-48` y `dependencies.py:34-37` no revisan `esta_activo`, así que un usuario desactivado sigue entrando y su token sigue sirviendo.
- **Recomendación:** una sola dependencia `requiere_rol(*roles)` en `dependencies.py`, más el filtro `esta_activo` en el login y en `get_current_user`.

#### C7. Modelo de datos sin dueño ("SaaS" sin negocio) ⚠️ Requiere aviso al equipo
- **Hecho:** el README y la especificación hablan de un SaaS para colmados, pero ninguna tabla (DBML ni modelos) tiene `id_negocio` o equivalente. Tal como está, todos los colmados verían los productos, clientes y deudas de los demás.
- **Recomendación:** decidir ya.
  - **Opción A (recomendada):** tabla `negocios` y `id_negocio` en las tablas raíz (usuarios, productos, categorias, clientes, proveedores, ventas, compras), filtrado por una dependencia `negocio_actual`.
  - **Opción B:** una instalación por colmado, documentada como límite.
  - Agregarlo después obliga a migrar todas las tablas.

### 🟠 Importantes

#### I1. Tres versiones del modelo de usuario que no coinciden ⚠️ Requiere aviso al equipo
- **Hecho:**
  - DBML (`docs/modelo-datos.dbml:136-145`): `id_usuario`, `apellido`, `username`, `password_hash`, `estado`.
  - Modelo (`backend/app/models/usuario.py:9-14`): `id`, `hashed_password`, `esta_activo`, sin `apellido` ni `username`.
  - Las migraciones coinciden con el modelo, no con el DBML.
- **Recomendación:** el DBML es la fuente de verdad del diseño. Unificar nombres (`id_<tabla>` en todas las PK, como en `roles`) y regenerar el diagrama.

#### I2. Cantidades enteras en un negocio que vende por peso ⚠️ Requiere aviso al equipo
- **Hecho:** `DetalleVenta.cantidad`, `DetalleCompra.cantidad` e `Inventario.stock_*` son `int` (`modelo-datos.dbml:63,75-77,117`).
- **Opinión:** en un colmado se vende "media libra de arroz" o "un cuarto de queso", y con `int` no se puede registrar.
- **Recomendación:** `Numeric(10,3)` para cantidades y stock, más `unidad_medida` en productos.

#### I3. Tipos monetarios sin precisión
- **Hecho:** el DBML usa `decimal` sin precisión en todos los montos. No se usa `float` ✅, pero no hay escala definida.
- **Recomendación:** `Numeric(12,2)` en todos los montos, por convención del equipo.

#### I4. Tablas y campos faltantes respecto al dominio ⚠️ Requiere aviso al equipo
- **Hecho:**
  - `Ventas` no tiene `id_usuario` (quién vendió) ni `estado` (anulada).
  - `Compras` no tiene `id_usuario`.
  - `Productos` no tiene `precio_costo` (sin él no hay ganancia en reportes).
  - No hay tabla para registrar los recordatorios de WhatsApp enviados, así que no hay forma de evitar duplicados ni de auditar envíos.
  - `Clientes.telefono` es nullable y no hay campo de consentimiento (opt-in), que Meta exige para escribirle a un cliente.
  - Ninguna tabla tiene `creado_en`.
- **Detalle en** `REUSO.md` §3.

#### I5. Datos redundantes en `Deuda`
- **Hecho:** `Deuda` guarda `monto_total`, `monto_pagado` y `saldo_pendiente` (`modelo-datos.dbml:155-157`). `monto_pagado` es la suma de `Abono.monto` y `saldo_pendiente` = total − pagado. Además `estado='vencida'` se puede deducir de `fecha_limite`.
- **Recomendación:** guardar solo `monto_total` y `saldo_pendiente`, actualizado en la **misma transacción** que inserta el abono, con `CHECK (saldo_pendiente >= 0)`. Calcular "vencida" al consultar.

#### I6. `Inventario` como tabla 1:N con productos
- **Hecho:** `Inventario.id_producto` no es `unique` (`modelo-datos.dbml:74`), así que un producto puede tener varias filas de stock.
- **Recomendación:** mover `stock_actual` y `stock_minimo` a `productos` (un solo almacén por colmado). Si se mantiene la tabla, ponerle `unique` a `id_producto`.

#### I7. Índices ausentes
- **Hecho:** Postgres no indexa las FK automáticamente, y el DBML no declara índices.
- **Recomendación:** indexar todas las FK, además de `ventas(fecha)`, `deudas(id_cliente, estado)` y `productos(nombre)`.

#### I8. Desfase probable entre modelo y migración de `roles`
- **Hecho:** el modelo declara `nombre = Column(String, unique=True)` sin `index=True` (`backend/app/models/rol.py:9`), pero la migración crea un índice único `ix_roles_nombre` (`c4574fa9da3b...py:30`).
- **Hecho:** `usuarios.esta_activo` es `nullable` y sin `server_default` en la BD (`5f6377b4145f...py:29`).
- **Recomendación:** correr `alembic check` tras levantar la BD. Al rehacer la migración base (ver plan), usar `server_default=sa.true()`.

#### I9. `passlib` está abandonado y `bcrypt` quedó fijado para esquivar su rotura
- **Hecho:**
  - `passlib==1.7.4` es de 2020 y es la última versión.
  - `bcrypt==4.0.1` está fijado porque bcrypt ≥4.1 rompe la detección de versión de passlib, y bcrypt 5 rechaza claves de más de 72 bytes.
  - `UsuarioCreate.password` no tiene límite de largo (`backend/app/schemas/usuario.py:19`).
- **Recomendación:** usar `pwdlib` y limitar la contraseña a 8–72 caracteres en el schema.

#### I10. Sin CORS
- **Hecho:** `backend/app/main.py` no agrega `CORSMiddleware`. Angular en `localhost:4200` no podrá llamar a la API en `:8000`.
- **Recomendación:** `CORSMiddleware` con orígenes leídos de una variable de entorno, nunca `*` junto con credenciales.

#### I11. Dockerfile del backend no apto para producción
- **Hecho:**
  - Corre como root (no hay `USER`).
  - Usa `--reload` en el `CMD` (`backend/Dockerfile:18`).
  - Instala `gcc` y `libpq-dev`, que no hacen falta con `psycopg2-binary` (`:6-9`).
  - Instala pytest y ruff en la imagen.
  - No hay `.dockerignore`, así que `COPY . .` (`:14`) **mete `backend/.env` con secretos dentro de la imagen**.
- **Recomendación:** `.dockerignore` (`.env`, `__pycache__`, `test/`), usuario no-root, `--reload` solo desde compose de desarrollo, y `requirements-dev.txt` aparte.

#### I12. docker-compose frágil
- **Hecho:**
  - Postgres publica `5432` hacia el host (`docker-compose.yml:10-11`).
  - No hay `healthcheck`, y `depends_on` no espera a que la BD esté lista (`:19-20`).
  - Las migraciones no se aplican solas.
  - `restart: always` combinado con un bind mount de desarrollo (`:26`).
  - No hay servicio de frontend.
- **Recomendación:** healthcheck con `pg_isready` y `depends_on: condition: service_healthy`. Publicar 5432 solo en desarrollo.

#### I13. El README fue borrado
- **Hecho:** el commit `ce701aa` dejó `README.md` solo con `# ColMaster`. El contenido completo (ES + EN) está en `68ad22d`.
- **Recomendación:** restaurarlo con `git show 68ad22d:README.md`, cambiar el nombre a Bodeguita y corregir la URL de clonado (`tu-usuario/sistema-colmados`).

#### I14. Pydantic v2 escrito con sintaxis de v1
- **Hecho:** `class Config` en `backend/app/core/config.py:16` y en `backend/app/schemas/usuario.py:9,27`. Funciona, pero genera aviso de deprecación.
- **Recomendación:** `model_config = SettingsConfigDict(...)` y `ConfigDict(from_attributes=True)`.

#### I15. Validación de entrada mínima en auth
- **Hecho:**
  - `email: str` sin `EmailStr` (`schemas/usuario.py:15`).
  - Comparación de email sensible a mayúsculas (`auth.py:21,47`), lo que permite cuentas duplicadas como `Ana@x.com` y `ana@x.com`.
  - Dos registros simultáneos con el mismo email dan `IntegrityError` → 500 (`auth.py:37-38`).
- **Recomendación:** `EmailStr` (requiere `email-validator`), normalizar a minúsculas y capturar `IntegrityError` → 400.

#### I16. Cobertura de tests ≈ 0 en la lógica
- **Hecho:** un único test, `/health` (`backend/test/test_health.py`). Ningún test de registro, login ni token.
- **Recomendación:** antes de seguir, tests de login correcto, login fallido, `/me` sin token y usuario inactivo.

### 🟡 Menores

| # | Archivo:línea | Hecho | Recomendación |
|---|---|---|---|
| M1 | `backend/app/core/security.py:18-24`, `dependencies.py:28` | El JWT usa `sub=email`: si el usuario cambia de email, su token deja de servir. Sin refresh token. HS256, 60 min. | `sub=str(id_usuario)`. Para el MVP basta access token sin refresh (ver evaluación). |
| M2 | `backend/app/core/config.py:12` | `secret_key` no exige un largo mínimo. | `Field(min_length=32)`. |
| M3 | `backend/app/core/config.py:6-8` | `postgres_user/password/db` se declaran pero no se usan. | Borrarlos. |
| M4 | `backend/alembic.ini:12` | URL con credenciales por defecto `postgres:postgres`, aunque `env.py:12` la reemplaza. Comentario "¡la línea que te daba el error!" (`:2`). | Dejar `sqlalchemy.url =` vacío y limpiar comentarios. |
| M5 | Migraciones `5f6377b4145f:33`, `c4574fa9da3b:29` | Índices redundantes sobre PK (`ix_usuarios_id`, `ix_roles_id_rol`). | Quitar `index=True` de las PK. |
| M6 | `backend/app/models/*.py` | `String` sin largo, estilo `Column` antiguo, `db.query()` antiguo. | Estilo 2.0: `Mapped[...]`, `mapped_column`, `select()`. |
| M7 | `backend/app/dependencies.py:11-13`, `routers/auth.py:13-16` | Dependencias guardadas en variables de módulo para esquivar la regla B008 de ruff, que ni siquiera está activa. | `Annotated[Session, Depends(get_db)]`. |
| M8 | `backend/requirements.txt:13-15` | pytest, httpx y ruff sin versión y mezclados con producción. | `requirements-dev.txt` con versiones fijadas. |
| M9 | `.github/workflows/ci.yml:5,7,16,19` | Rama `develop` inexistente. Acciones `checkout@v4` y `setup-python@v5` con majors más nuevos. Sin caché de pip. Sin job de frontend. | Ver `EVALUACION-TECNOLOGIAS.md` §CI. |
| M10 | `.gitignore` | Plantilla solo de Python: le faltan `node_modules/` y `.angular/`. El patrón `lib/` (`:17`) ignoraría cualquier carpeta `lib` del frontend. | Agregar reglas de Node/Angular y quitar `lib/`. |
| M11 | `frontend/src/app/Dockerfile` | Dockerfile dentro de `src/app/` (lugar incorrecto) y vacío. | Borrarlo; el Dockerfile del frontend va en `frontend/`. |
| M12 | `backend/alembic/script.py.mako:8,16-18` | La plantilla usa `Union[...]`, mientras que las migraciones existentes usan `str \| None`. | Unificar a `\|`. |
| M13 | `docs/modelo-datos.dbml` | Nombres mezclados en singular y plural (`Categoria`, `Deuda`, `Abono` vs `Productos`, `Ventas`). `metodo_pago` y `estado` son texto libre. | Tablas en plural `snake_case`. `CHECK` o enum para estados y métodos de pago. |
| M14 | `backend/app/main.py:4` | Título "SysCol API". | "Bodeguita API". |

---

## 3. Seguridad: verificaciones con resultado negativo (sin hallazgo)

- **Secretos en el historial:** se buscó `SECRET`, `password`, `token`, `api_key` y `sid` en las 3 versiones del repo. Solo aparecen placeholders (`.env.example`) y nombres de variables. **No hay credenciales reales** ✅.
- **Inyección SQL:** todo el acceso pasa por el ORM con parámetros. Los SQL crudos de la migración `c4574fa9da3b` son literales sin entrada del usuario ✅.
- **Hash de contraseñas:** se usa bcrypt, nunca texto plano ✅. Ver I9 para la librería.
- **Login:** el mensaje de error no revela si el email existe ✅ (`auth.py:51`).

## 4. Suposiciones del auditor

- Nada se ejecutó: ni contenedores, ni instalación de paquetes, ni tests. C1, C2 y C3 se deducen de leer el código y de las reglas por defecto de ruff, pydantic-settings y compose. Para confirmarlo, basta mirar el resultado del CI en GitHub Actions.
- Las vulnerabilidades vienen de `api.osv.dev` para las versiones exactas fijadas. Para starlette se consultó 0.38.6, la más alta que permite fastapi 0.115.0.
- "SaaS" se interpreta como varios colmados en una misma instalación (de ahí C7).
