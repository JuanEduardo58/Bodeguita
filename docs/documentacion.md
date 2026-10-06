# Documentación y bitácora de Bodeguita

Documento único de contexto y seguimiento. Todo lo que se hace en el proyecto se anota aquí, en orden, en la **Bitácora** (§7).

---

## 1. Qué es Bodeguita

Sistema SaaS ligero para **colmados dominicanos**. Reemplaza las cuentas en papel con inventario, ventas y avisos automáticos de deudas ("fiao") por WhatsApp. Tiene que ser tan simple que el colmadero lo use desde el celular.

- **Repo:** https://github.com/JuanEduardo58/Bodeguita
- **Nombres anteriores:** SysCol y ColMaster. Es el mismo proyecto renombrado.
- **Equipo:** 2 personas. Al inicio eran 4.
- **Especificación original:** `cluade.md`, fuera del repo, en la carpeta de trabajo.

### Módulos

| Módulo | Alcance | Estado |
|---|---|---|
| Autenticación | JWT + roles (`dueno`, `cajero`) | ✅ Hecho |
| Inventario | Productos, categorías, stock, alertas de bajo inventario | ⏳ Pendiente (tablas listas) |
| Ventas (POS) | Carrito, totales, métodos de pago | ⏳ Pendiente (tablas listas) |
| Clientes / Fiao | Deudas, abonos parciales, límite de crédito | ⏳ Pendiente (tablas listas) |
| WhatsApp | Recordatorios automáticos de deuda | ⏳ Pendiente (tabla de registro lista) |
| Reportes | Ventas por período, más vendidos, resumen de deudas | ⏳ Pendiente |

---

## 2. Decisiones tomadas

| Tema | Decisión | Por qué |
|---|---|---|
| Código viejo | **Se borró y se arrancó de cero** | Solo tenía el login. El resto eran archivos vacíos y el CI estaba roto (ver `AUDITORIA.md`) |
| Varios colmados | Sí: tabla `negocios` + `id_negocio` | Es un SaaS. Agregarlo después obligaría a migrar todas las tablas |
| WhatsApp | Cloud API de Meta, directa | Sin el recargo de USD 0.005 por mensaje de Twilio, sin SDK extra, y con número de prueba gratis |
| UI | Angular Material + PWA | Mismo equipo que Angular, liviana en móvil, instalable desde el navegador |
| Roles | `dueno` y `cajero`, como texto con `CHECK` | Dos roles fijos no justifican una tabla |
| Backend | FastAPI + SQLAlchemy 2 **síncrono** | Async duplica la dificultad y un colmado no necesita esa concurrencia |
| JWT | PyJWT, token de 12 h sin refresh | python-jose tenía vulnerabilidades. 12 h es una jornada del colmado |
| Contraseñas | pwdlib con Argon2 | passlib está abandonado |
| Dónde guardar el token | `localStorage` | Para que la PWA no pida login cada vez. Límite: un XSS podría leerlo. Mejora futura: cookie `httpOnly` |
| CORS | No se usa: la API vive bajo `/api` en el mismo origen | nginx (producción) y el proxy de `ng serve` (desarrollo) reenvían `/api` al backend |
| Tareas programadas | Script + cron del servidor | Celery es demasiado. APScheduler duplica avisos si hay varios workers |
| Compras / proveedores | Fuera del MVP | No están entre los 6 módulos. Se hacen al final si sobra tiempo |
| Dinero y cantidades | Montos `Numeric(12,2)`, cantidades `Numeric(10,3)` | Nunca `float`. En el colmado se vende media libra |

Detalle y fuentes: `EVALUACION-TECNOLOGIAS.md`.

---

## 3. Stack y versiones (verificadas el 2026-10-05)

| Pieza | Versión |
|---|---|
| Python | 3.12 en Docker (localmente funciona con 3.14) |
| FastAPI / Starlette | 0.142.2 / 1.7.0 |
| SQLAlchemy / Alembic | 2.1.3 / 1.20.0 |
| psycopg | 3.3.6 |
| Pydantic / pydantic-settings | 2.13.5 / 2.15.0 |
| PyJWT / pwdlib | 2.15.1 / 0.3.1 |
| pytest / ruff / httpx2 | 9.1.1 / 0.16.10 / 2.13.1 |
| PostgreSQL | 17 |
| Angular / Angular Material | 22.2 |
| Node | 24 LTS |
| GitHub Actions | checkout@v7, setup-python@v7, setup-node@v7 |

---

## 4. Cómo levantar el proyecto

### 4.1 Desarrollo con cambios en tiempo real (recomendado para programar)

La base de datos corre en Docker. El backend y el frontend corren en tu máquina y se recargan solos al guardar.

**Terminal 1, base de datos** (desde la raíz del repo):
```bash
docker compose up -d db
```

**Terminal 2, backend** (desde `backend/`):
```bash
.venv\Scripts\activate
alembic upgrade head
uvicorn app.main:app --reload
```
Activa el entorno virtual (en Mac/Linux: `source .venv/bin/activate`), aplica las migraciones pendientes y arranca la API en http://127.0.0.1:8000. Se reinicia al guardar un `.py`.

**Terminal 3, frontend** (desde `frontend/`):
```bash
npm start
```
Abre http://127.0.0.1:4200. La página se actualiza al guardar un `.ts`, `.html` o `.scss`.

- Documentación interactiva de la API: http://127.0.0.1:8000/api/docs
- Usuario de prueba local: `dueno@demo.do` / `demo12345` (Colmado Demo)

**Primera vez** (si no existe `backend/.venv` o `frontend/node_modules`):
```bash
cp .env.example .env
```
Después edita `.env` con tu clave de Postgres y un `SECRET_KEY`.

```bash
cd backend && python -m venv .venv && .venv\Scripts\pip install -r requirements-dev.txt
```
Crea el entorno virtual de Python e instala las dependencias.

```bash
cd frontend && npm install
```
Instala las dependencias del frontend.

### 4.2 Todo en Docker (como en producción)

```bash
docker compose up -d --build
```
Levanta la app en http://localhost:8080. **No** tiene recarga automática: después de cada cambio hay que reconstruir.

> No uses las dos formas a la vez: los dos backends quieren el puerto 8000. Para pasar de Docker a desarrollo: `docker compose stop backend frontend`.

### 4.3 Crear un colmado nuevo

```bash
docker compose exec backend python -m app.tareas.crear_negocio
```
Esto es para el modo Docker. En modo desarrollo, desde `backend/` con el venv activo: `python -m app.tareas.crear_negocio`.

### 4.4 Tests

Backend (desde `backend/`):
```bash
ruff check . && ruff format --check . && pytest
```

Frontend (desde `frontend/`):
```bash
npx ng test --watch=false
```

---

## 5. Particularidades de la PC de desarrollo (Windows)

| Problema | Solución aplicada |
|---|---|
| Ya hay dos PostgreSQL instalados usando los puertos 5432 y 5433 | El Postgres de Docker se publica en **`127.0.0.1:55432`** |
| `localhost` intenta primero IPv6 (`::1`) y la conexión se cuelga | `DATABASE_URL` usa **`127.0.0.1`**, nunca `localhost` |
| Docker Desktop suele estar cerrado y tarda en arrancar (a veces da error 500 al principio) | Abrir Docker Desktop y esperar 1–2 min antes de `docker compose` |

---

## 6. Reglas del equipo

- Cada consulta filtra por `usuario.id_negocio`. Sin ese filtro, un colmado ve los datos de otro.
- Roles en el endpoint: `usuario: Annotated[Usuario, requiere_rol("dueno")]`.
- La lógica de negocio va en `services/`. Los routers solo validan, llaman al servicio y responden.
- Al cambiar un modelo: `alembic revision --autogenerate -m "..."` sobre `main` actualizado, revisar el archivo generado y avisar al compañero.
- Plan de trabajo, reparto y reglas de negocio pendientes: `PLAN.md`.

---

## 7. Bitácora

### 2026-10-05: auditoría, reinicio desde cero y base funcionando

**Auditoría del código viejo (SysCol)**
- Se clonó el repo y se revisaron todos los archivos y el historial de git.
- **Hallazgos principales:**
  - Solo existía el login. 17 archivos estaban vacíos.
  - No había frontend.
  - El CI estaba roto: un `import *` hacía fallar el lint, y los tests fallaban por variables de entorno faltantes.
  - `docker compose` no arrancaba desde cero.
  - Había dependencias con vulnerabilidades (starlette, python-multipart, python-jose).
  - El registro de usuarios era público y no se verificaba ningún rol.
  - El último commit había borrado el README.
- No había secretos commiteados.
- Entregables: `AUDITORIA.md`, `EVALUACION-TECNOLOGIAS.md`, `REUSO.md`, `PLAN-MIGRACION.md`. Hoy son documentos históricos.

**Decisiones del equipo:** arrancar de cero con 2 personas, varios colmados, Meta para WhatsApp y Angular Material (ver §2).

**Construcción de la base**
- Se borró todo el código viejo y se conservaron solo `.git` y los documentos.
- **Backend:**
  - `core/`: configuración, BD y JWT + Argon2.
  - `models/`: las 11 tablas, con CHECK, FK, índices y nombres de constraints fijos.
  - `dependencies.py`: `get_current_user`, `requiere_rol`.
  - `routers/auth.py`: `/api/auth/login`, `/api/auth/me`, `/api/auth/usuarios`.
  - Script `tareas/crear_negocio.py`.
- **Migración `0001_esquema_base`** generada con autogenerate y revisada. `alembic check` no encuentra diferencias.
- **Tests:** 8 de auth (login, mayúsculas en el correo, clave incorrecta, usuario inactivo, token inválido, dueño crea cajero, cajero recibe 403, clave corta). Cada test se deshace al terminar.
- **Frontend:**
  - Angular 22 + Material + PWA.
  - `core/auth.ts` con servicio, interceptor y guard.
  - Páginas `login` e `inicio`.
  - Proxy `/api` hacia el backend, Dockerfile con nginx.
  - 2 tests del interceptor.
- **Infra:** `docker-compose.yml` con base de datos (healthcheck), backend (no-root, migraciones al arrancar) y frontend. CI con lint, migraciones y tests. Dependabot semanal.
- **Docs:** `README.md`, `modelo-datos.dbml` (modelo nuevo), `PLAN.md` (reparto entre 2 personas).

**Problemas encontrados y resueltos**
- Docker Desktop no respondía (error 500): se reabrió y se esperó a que arrancara.
- El puerto 5432 y luego el 5433 estaban ocupados por PostgreSQL locales: se pasó al 55432.
- Alembic se colgaba al conectar porque `localhost` intentaba IPv6: se cambió a `127.0.0.1`.
- Starlette 1.x marcó `httpx` como obsoleto en su cliente de tests: se cambió a `httpx2`.
- Un test de Angular navegaba a `/login` sin que esa ruta existiera en el test: se agregó la ruta.

**Verificación**
- Con todo en Docker: se creó "Colmado Demo" con el script, el login por nginx devuelve el token, `/me` responde y la app carga en `:8080`.

**Proyecto levantado en modo desarrollo** (al final de la sesión)
- Se pararon los contenedores de backend y frontend. La base de datos sigue en Docker.
- Backend con `uvicorn --reload` en `:8000` y frontend con `ng serve` en `:4200`. El proxy `/api` funciona y el login de prueba responde.

### 2026-10-06: servidores de desarrollo detenidos

- Claude Code detuvo el backend (`uvicorn --reload`) y el frontend (`ng serve`) porque la PC se quedó con poca memoria mientras la sesión estaba inactiva. No es un error del proyecto.
- La base de datos sigue en Docker. Para volver a levantarlos, ver §4.1.
- Se volvieron a levantar desde la sesión de Claude a pedido del usuario. Había 4.5 GB de RAM libre de 31.8 GB. Verificado: la API responde, la app carga en `:4200` y el login por el proxy funciona.
- El nuevo `ng serve` no pudo arrancar ("Port 4200 is already in use"): el proceso anterior no se había cerrado del todo. Se cerró ese proceso huérfano y se volvió a levantar. **Si ves ese error**, busca quién usa el puerto con `Get-NetTCPConnection -LocalPort 4200` (PowerShell) y cierra ese proceso, o arranca con otro puerto: `npx ng serve --port 4201`.

### 2026-10-06: arreglado el login desde el navegador

- **Síntoma:** no se podía entrar desde la app. El backend respondía `422` al `POST /api/auth/login`. Con `curl` sí funcionaba.
- **Causa:** el login de FastAPI (OAuth2) espera un formulario (`application/x-www-form-urlencoded`). `AuthService.login` le pasaba un `URLSearchParams` a `HttpClient`, que no lo convierte a formulario, así que el backend no recibía `username` ni `password`.
- **Arreglo** (`frontend/src/app/core/auth.ts`): el cuerpo se envía como texto ya codificado (`URLSearchParams(...).toString()`) con la cabecera `Content-Type` explícita. No se usó `HttpParams` porque deja el `+` sin codificar y rompería contraseñas que lo tengan.
- **Test nuevo** (`auth.spec.ts`): comprueba la cabecera, el cuerpo codificado (con `@`, `+` y espacio en la contraseña) y que el token se guarde. Frontend: 3/3 tests en verde.
- **Lección:** el login se había probado con `curl` y con los tests del backend, pero no desde el frontend real. Toda pantalla nueva se prueba en el navegador antes de darla por hecha.

**Pendiente**
- Commit y push. Los hace el usuario.
- Que el compañero clone el repo y cree su propio `.env`.
- Pedir hoy la aprobación de la plantilla de WhatsApp a Meta.
- Arrancar los módulos según `PLAN.md`: Persona A con Inventario, Persona B con Clientes.
