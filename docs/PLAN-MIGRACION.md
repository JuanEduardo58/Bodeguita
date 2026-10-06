# Plan de migración: de SysCol heredado a Bodeguita

> **Histórico.** Describe el código viejo de SysCol, que se borró el 2026-10-05 al arrancar desde cero. El plan vigente está en [`PLAN.md`](PLAN.md).

Orden pensado para que nadie se quede bloqueado esperando a otro.
- **P1** Inventario
- **P2** Ventas/POS
- **P3** Fiao + WhatsApp
- **P4** Reportes + Infra / Líder técnico

## Grafo de dependencias

```
Fase 0 Decisiones ──► Fase 1 Infra verde ──► Fase 2 Modelo base + migración 0001
                                                   │
                     ┌─────────────────────────────┼──────────────────────────┐
                     ▼                             ▼                          ▼
              Fase 3 Auth+roles             Fase 4 Frontend base        (P3) CRUD clientes
                     │                             │                          │
                     └──────────────┬──────────────┘                          │
                                    ▼                                          │
                         Fase 5 Inventario (P1)                                │
                                    ▼                                          │
                         Fase 6 Ventas/POS (P2) ◄──────────────────────────────┘
                                    ▼
                         Fase 7 Fiao: deudas + abonos (P3)
                                    ▼
                         Fase 8 WhatsApp + cron (P3)
                                    ▼
                         Fase 9 Reportes (P4)  ← puede empezar con datos semilla desde la Fase 6
```

Cadena de FK que obliga a este orden:
- `negocios → roles → usuarios`
- `negocios → categorias → productos`
- `negocios → clientes`
- `productos + clientes + usuarios → ventas → detalle_venta`
- `ventas + clientes → deudas → abonos → recordatorios_whatsapp`

---

## Fase 0: Decisiones (reunión de 1 h, todo el equipo)

| # | Decisión | Recomendación | Fuente |
|---|---|---|---|
| D1 | ¿Varios negocios por instalación (SaaS)? | Sí: tabla `negocios` + `id_negocio` | AUDITORIA C7 |
| D2 | Proveedor de WhatsApp | Meta Cloud API directa | EVALUACION §3 |
| D3 | Librería de UI | Angular Material | EVALUACION §2 |
| D4 | ¿Compras/proveedores entran al MVP? | No. Se hacen después de Reportes si sobra tiempo | REUSO §3 |
| D5 | Nombre único | "Bodeguita" en código, README y título de la API | AUDITORIA §1.3 |

Al cerrar, P3 abre de inmediato la cuenta de Meta Business y solicita la plantilla `recordatorio_deuda`. La aprobación tarda y está en la ruta crítica.

## Fase 1: Infra en verde (P4) · bloquea todo lo demás

1. Restaurar el README y renombrarlo.
   ```bash
   git show 68ad22d:README.md > README.md
   ```
   Recupera las 282 líneas que borró el commit `ce701aa`.
2. Actualizar `requirements.txt` y crear `requirements-dev.txt` (versiones en EVALUACION §1).
3. Arreglar los dos errores del CI:
   - `alembic/env.py`: cambiar el `import *` (C1).
   - `ci.yml`: agregar `env:` y el servicio `postgres:17` (C2).
4. Corregir el arranque de compose (C3):
   - Un solo `.env` en la raíz, a partir de un `.env.example` con `POSTGRES_*`.
   - Healthcheck en la BD.
   - `depends_on: condition: service_healthy`.
5. Corregir el Dockerfile: `.dockerignore`, usuario no-root, sin `--reload` en la imagen (I11).
6. Agregar `.gitignore` de Node/Angular y `dependabot.yml`.

**Listo cuando:** un clon limpio levanta con estos comandos y el CI pasa en verde.
```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend alembic upgrade head
curl http://localhost:8000/health
```

## Fase 2: Modelo de datos base (P4 escribe, los 4 revisan) · ⚠️ Requiere aviso al equipo

1. Actualizar `docs/modelo-datos.dbml` al **DBML v2** (REUSO §3) y regenerar el PNG.
2. PR de revisión: cada integrante aprueba las tablas de su módulo.
3. Escribir **todos** los modelos SQLAlchemy de una vez, en estilo `Mapped[]`, en este orden de FK:
   1. `negocio`
   2. `rol`
   3. `usuario`
   4. `categoria`
   5. `producto`
   6. `cliente`
   7. `venta`
   8. `detalle_venta`
   9. `deuda`
   10. `abono`
   11. `recordatorio_whatsapp`
4. Borrar las 2 migraciones viejas y generar la migración base.
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "esquema base"
   ```
   Crea `0001` con todas las tablas. Revisarla a mano y pegar el seed de roles de `c4574fa9da3b`.
5. Avisar a todos que reinicien su BD local.
   ```bash
   docker compose down -v
   ```
   Borra la BD local vieja. Hay que hacerlo una sola vez.

**Por qué todo de una vez:** si cada integrante crea su modelo en paralelo, Alembic termina con varias `heads` y FK hacia tablas que todavía no existen. A partir de aquí:
- Toda migración nueva se hace sobre `main` actualizado.
- El CI corre `alembic heads` y falla si hay más de una.

## Fase 3: Auth y roles (P4) · depende de la Fase 2

1. `security.py`: cambiar a pwdlib + PyJWT, `sub = id_usuario`, vida del token de 12 h.
2. `dependencies.py`: `get_current_user` exige `esta_activo` y expone `negocio_actual`. Agregar `requiere_rol(*roles)`.
3. `/auth/register`: solo para `admin`/`dueno`, dentro de su propio negocio.
4. Script para crear el primer negocio y su dueño.
   ```bash
   docker compose exec backend python -m app.tareas.crear_dueno
   ```
   Lee `DUENO_EMAIL` y `DUENO_PASSWORD` del entorno.
5. Tests: login correcto, login fallido, `/me` sin token, usuario inactivo, rol insuficiente → 403.

**Contrato para P1, P2 y P3:** cada endpoint nuevo lleva `usuario = Depends(requiere_rol(...))` y filtra por `usuario.id_negocio`.

## Fase 4: Frontend base (P4, o rotativo) · en paralelo con la Fase 3

```bash
npx @angular/cli@22 new frontend --routing --style=scss --ssr=false
```
Crea el proyecto Angular 22 standalone (requiere Node 24 LTS).

```bash
cd frontend && npx ng add @angular/material && npx ng add @angular/pwa
```
Agrega la librería de UI y deja la app instalable en el celular.

- `core/auth.service.ts` (signal del usuario actual), `core/auth.interceptor.ts` (adjunta el Bearer token y redirige al login con 401) y un guard por rol.
- `app.routes.ts` con rutas *lazy*: `inventario`, `ventas`, `fiao`, `reportes`, `login`.
- `Dockerfile` en `frontend/` (build + nginx) y servicio en compose.
- Job de CI: `npm ci && npx ng build`.

## Fase 5: Inventario (P1) · depende de las Fases 3 y 4

- **Backend:** CRUD de `categorias` y `productos`, búsqueda por nombre o código de barras, y `GET /productos/bajo-stock` (`stock_actual <= stock_minimo`).
- **Frontend:** lista con buscador, formulario de producto y aviso de bajo stock.
- **Tests:** stock decimal (0.5 lb), código de barras único por negocio.

## Fase 6: Ventas/POS (P2) · depende de la Fase 5 (productos) y del CRUD de clientes

- P3 entrega el **CRUD de clientes** (con `limite_credito` y `acepta_whatsapp`) antes de que P2 llegue a la venta al fiao. Puede hacerlo en paralelo con la Fase 5.
- **Backend:** `POST /ventas` en `services/ventas_service.py`, en **una sola transacción**:
  1. Valida el stock.
  2. Congela `precio_venta`.
  3. Descuenta el stock.
  4. Calcula los totales en el servidor (nunca se confía en el total que manda el cliente).
  5. Si `metodo_pago='fiao'`, crea la `deuda` llamando a una función de `fiao_service`, la de P3, para no duplicar reglas.
  6. Anular una venta devuelve el stock.
- **Frontend:** POS móvil con buscador, carrito, botones grandes de método de pago y total visible.

## Fase 7: Fiao (P3) · depende de la Fase 6 (ventas) y de clientes

- `services/fiao_service.py`:
  - `crear_deuda(venta)` rechaza la venta si `saldo_total_cliente + total > limite_credito`.
  - `registrar_abono(deuda, monto)` bloquea la fila con `SELECT … FOR UPDATE`, inserta el abono, baja el saldo y cambia el estado, todo en la misma transacción.
- **Endpoints:** deudas por cliente, registrar abono, estado de cuenta.
- **Tests:** límite excedido, abono mayor que el saldo (rechazado), abono parcial → `parcial`, abono final → `pagada`.

## Fase 8: WhatsApp (P3) · depende de la Fase 7 y de la plantilla aprobada (Fase 0)

- `services/whatsapp_service.py`: **una** función `enviar_recordatorio(telefono, nombre, saldo)` con un `POST` vía `httpx` a la Cloud API.
- `app/tareas/recordatorios.py`:
  - Recorre las deudas con saldo > 0 y vencidas (o con más de N días) de clientes con `acepta_whatsapp`.
  - Salta los clientes con un recordatorio enviado en los últimos N días.
  - Registra cada envío en `recordatorios_whatsapp`.
- **Cron del host:**
  ```bash
  0 9 * * * cd /ruta/bodeguita && docker compose exec -T backend python -m app.tareas.recordatorios
  ```
  Envía los avisos todos los días a las 9:00 a. m.
- **Tests:** el envío a Meta se simula (mock de `httpx`) y se verifica que no se envía dos veces.

## Fase 9: Reportes (P4) · depende de las Fases 6 y 7 (puede empezar con datos semilla)

- `services/reportes_service.py`: ventas por período, más vendidos (por cantidad y por monto), resumen de deudas (total por cobrar y vencidas), ganancia estimada (`precio_venta − precio_costo`).
- Consultas con `GROUP BY` en SQL, no en Python.
- **Frontend:** dashboard móvil con tarjetas de totales y una tabla `mat-table` con filtro de fechas.

## Fase 10 (opcional, si sobra tiempo)

- Compras y proveedores: cada compra suma stock.
- Cookie `httpOnly` en lugar de `localStorage`.
- Despliegue en un VPS con HTTPS (Caddy o nginx + Let's Encrypt).

---

## Reglas durante toda la migración

- Un PR por funcionalidad, con CI verde, revisado por al menos 1 integrante.
- Cualquier cambio en `models/` o `alembic/versions/` se anuncia en el chat del equipo antes del merge. ⚠️
- La lógica de negocio va en `services/`. Los routers solo validan, llaman al servicio y responden.
- Montos en `Numeric(12,2)` y cantidades en `Numeric(10,3)`. Nunca `float`.
