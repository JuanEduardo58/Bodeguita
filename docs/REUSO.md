# Qué se rescata y qué se tira del código heredado de SysCol

> **Histórico.** Describe el código viejo de SysCol, que se borró el 2026-10-05 al arrancar desde cero. El plan vigente está en [`PLAN.md`](PLAN.md).

Leyenda:
- ✅ **Rescatar tal cual**
- 🔧 **Rescatar con cambios**
- 🗑️ **Tirar**

Las referencias a hallazgos (C1, I9…) apuntan a `AUDITORIA.md`.

## 1. Backend

| Archivo | Decisión | Qué hacer |
|---|---|---|
| `app/core/config.py` | 🔧 | Pasar a `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`. Borrar `postgres_*`. Agregar `cors_origins`, `whatsapp_token`, `whatsapp_phone_id`, `secret_key` con `min_length=32` y vida del token de 12 h. |
| `app/core/database.py` | 🔧 | Cambiar `declarative_base()` por `class Base(DeclarativeBase)`. Mantener `get_db()`, que está bien. |
| `app/core/security.py` | 🔧 | Misma interfaz (`hash_password`, `verify_password`, `create_access_token`). Por dentro, pwdlib en vez de passlib y PyJWT en vez de jose. `sub = id_usuario`, claim `rol`. |
| `app/dependencies.py` | 🔧 | Conservar `get_current_user`, que ahora busca por id y exige `esta_activo`. Agregar **una** función `requiere_rol(*roles)`. Usar `Annotated` en vez de las dependencias guardadas en variables de módulo. |
| `app/routers/auth.py` | 🔧 | Conservar `/login` y `/me`. `/register` pasa a exigir `admin`/`dueno` y recibe el rol. Capturar `IntegrityError` y normalizar el email. |
| `app/schemas/usuario.py` | 🔧 | `ConfigDict(from_attributes=True)`, `EmailStr` y contraseña de 8 a 72 caracteres. Agregar `apellido`, `username` y `id_rol` si el DBML los mantiene. |
| `app/models/rol.py` | 🔧 | Estilo `Mapped[]`. Quitar el índice redundante de la PK. |
| `app/models/usuario.py` | 🔧 | Alinear con el DBML (`id_usuario`, `estado`/`esta_activo`: elegir un solo nombre) y agregar `id_negocio`. ⚠️ Requiere aviso al equipo |
| `app/models/__init__.py` | ✅ | Seguir importando aquí todos los modelos nuevos (Alembic los descubre por este archivo). |
| `app/main.py` | 🔧 | Título "Bodeguita API", `CORSMiddleware` y `include_router` de cada módulo a medida que exista. |
| `app/models/{cliente,deuda,producto,venta}.py` | 🗑️ | Vacíos. Cada responsable crea el suyo cuando le toque (ver plan). |
| `app/schemas/{cliente,producto,venta}.py` | 🗑️ | Vacíos. |
| `app/routers/{fiao,inventario,reportes,ventas,whatsapp}.py` | 🗑️ | Vacíos. Además, `whatsapp.py` como router no hace falta: los avisos salen del script de cron, no de un endpoint. |
| `app/services/{reportes,whatsapp}_service.py` | 🗑️ | Vacíos. Se recrean con contenido. |
| `test/test_health.py` | ✅ | Sirve. Agregar tests de auth al lado. |
| `alembic.ini` | 🔧 | Conservar `file_template` (fecha en el nombre: útil con 4 personas). Dejar `sqlalchemy.url` vacío y quitar comentarios de depuración. |
| `alembic/env.py` | 🔧 | Cambiar `import *` por `import app.models  # noqa: F401` (arregla el CI). |
| `alembic/script.py.mako` | 🔧 | Tipos con `\|` para que coincidan con las migraciones. |
| `alembic/versions/5f6377b4145f_*.py` | 🗑️ | Ver §2. |
| `alembic/versions/c4574fa9da3b_*.py` | 🗑️ (rescatar el seed) | Ver §2. El `INSERT` de los roles `admin`, `cajero` y `dueno` se copia a la migración base nueva. |
| `requirements.txt` | 🔧 | Nuevas versiones (ver evaluación). Separar `requirements-dev.txt`. |
| `Dockerfile` | 🔧 | Conservar la base `python:3.12-slim`. Quitar `gcc` y `libpq-dev`, agregar usuario no-root, sacar `--reload` del `CMD` y crear `.dockerignore`. |
| `.env.example` | 🔧 | Agregar `POSTGRES_*`, `CORS_ORIGINS` y las variables de WhatsApp Cloud API. Quitar las de Twilio. |

### Lógica de negocio rescatable

Solo existe la de auth. Se rescatan tres ideas, ya corregidas:
- Mensaje de login genérico que no revela si el email existe.
- Rol por defecto en la BD vía seed.
- Migración de datos dentro de Alembic (`op.execute` para rellenar antes de poner `NOT NULL`). El patrón de `c4574fa9da3b` es correcto y sirve de ejemplo al equipo para futuras migraciones con datos.

## 2. Migraciones de Alembic

**Hecho:** las 2 migraciones registran un cambio de diseño (rol como texto → tabla `roles`) que solo importa en una BD que ya tenía usuarios con `rol` de texto. No hay ninguna BD de producción.

**Decisión: tirar las 2 y crear una migración base nueva** (`0001_esquema_base`) con todas las tablas del DBML v2 (§3) más el seed de roles.
- **Por qué:** arrastrar una migración de datos que nadie necesita confunde. Además, la tabla `usuarios` cambia de todos modos (nombres, `id_negocio`).
- **Costo:** cada integrante debe borrar su BD local una vez (`docker compose down -v`). ⚠️ Requiere aviso al equipo.

## 3. Modelo de datos (DBML)

**Decisión:** 🔧 el DBML es la mejor pieza del repo. Se conserva como base y se corrige. ⚠️ Todos los cambios de esta sección requieren aviso al equipo.

| Tabla | Decisión | Cambios |
|---|---|---|
| `negocios` | ➕ nueva | `id_negocio`, `nombre`, `telefono`, `creado_en`. Solo si se elige la opción A de C7. |
| `roles` | ✅ | `nombre` con `unique`. |
| `usuarios` | 🔧 | `id_negocio`. Un solo nombre para el estado. `email` en minúsculas y `unique`. Decidir si `username` hace falta (opinión: no, basta el email). |
| `categorias` | 🔧 | Nombre en plural. `id_negocio`. `unique(id_negocio, nombre)`. |
| `productos` | 🔧 | `id_negocio`, `precio_costo Numeric(12,2)` y `unidad_medida` (`unidad`, `libra`, `onza`, `litro`). **Absorbe `stock_actual` y `stock_minimo` como `Numeric(10,3)`.** `codigo_barras` único por negocio. |
| `inventario` | 🗑️ | Sus columnas pasan a `productos` (I6). `stock_maximo` y `ultima_actualizacion` sobran para el MVP. |
| `clientes` | 🔧 | `id_negocio`. `telefono` obligatorio en formato E.164 (`+1809…`) si va a recibir avisos. `acepta_whatsapp boolean` (opt-in). `limite_credito Numeric(12,2)`. |
| `proveedores` | ✅ | `id_negocio`. Es opcional para el MVP (no está en los 6 módulos). |
| `compras`, `detalle_compra` | 🔧 | `id_usuario`, cantidades `Numeric(10,3)`. Opcional para el MVP: si se implementa, cada compra suma stock. |
| `ventas` | 🔧 | `id_negocio`, `id_usuario` (quién vendió), `estado` (`completada`/`anulada`), `metodo_pago` con `CHECK` (`efectivo`, `tarjeta`, `transferencia`, `fiao`). `impuesto` con `default 0`. |
| `detalle_venta` | 🔧 | `cantidad Numeric(10,3)`. `precio_venta` se guarda (precio congelado al momento de la venta, que es correcto). |
| `deudas` | 🔧 | Plural. Quitar `monto_pagado` (I5). `estado` con `CHECK` (`pendiente`, `parcial`, `pagada`). "Vencida" se calcula. `CHECK (saldo_pendiente >= 0)`. |
| `abonos` | 🔧 | Plural, `id_usuario` (quién cobró), `CHECK (monto > 0)`. |
| `recordatorios_whatsapp` | ➕ nueva | `id_recordatorio`, `id_deuda`, `enviado_en`, `estado_envio`, `id_mensaje_proveedor`, `error`. Evita duplicados y deja registro de cada envío. |
| Todas | 🔧 | `creado_en timestamptz default now()`. Montos en `Numeric(12,2)`. Índice en cada FK. |

## 4. Infra y docs

| Archivo | Decisión | Qué hacer |
|---|---|---|
| `docker-compose.yml` | 🔧 | Conservar la estructura. `postgres:17` con healthcheck, `env_file` y servicio `frontend`. Exponer 5432 solo en desarrollo. |
| `.github/workflows/ci.yml` | 🔧 | Conservar los jobs lint y tests. Agregar el servicio postgres, `env:`, `alembic upgrade head && alembic check` y el job de frontend. Quitar `develop`. |
| `.gitignore` | 🔧 | Agregar reglas de Node/Angular. Quitar `lib/`. |
| `README.md` | 🔧 | Restaurar desde `68ad22d`. Renombrar a Bodeguita. Corregir la URL de clonado y los pasos de `.env`. |
| `docs/modelo-datos.dbml` | 🔧 | Ver §3. |
| `docs/Diagrama de Syscol.png` | 🔧 | Regenerarlo desde el DBML v2 como `docs/diagrama-modelo.png`. |
| `frontend/src/app/**` (4 archivos vacíos) | 🗑️ | Se regenera con `ng new`. |
